from datetime import datetime
import multiprocess as mp
import numpy as np
import pandas as pd
import pyarrow.parquet as pa
from player import *

start_time = pd.Timestamp('1970-01-01 02:00:00')

# this module is supposed to replace both running.py and running_global.py
# it will be more efficient & offer some more functionality


def prep_df(players, path, first=False, second=False, regtime=False, overtime=False, begin=0, end=150, norm=False):
    # prepare the base for calculating the distances, velocities & accelerations
    # of the players from the 'raw' dataframe of the whole game
    table = pa.read_table(path)
    df_init = table.select(['time'] + [col for col in table.column_names if ('ball' not in col) and
                                  (('_x' in col) or ('_y' in col) or ('_sampling' in col))]).to_pandas()
    samplings = [col for col in table.column_names if ('ball' not in col) and ('_sampling' in col)]
    for col in samplings:
        df_init = df_init.loc[df_init[col] != 2]  # remove all unreliable samplings

    # drop the sampling columns(not needed anymore)
    # & compute the differences for each column
    df_init = df_init.drop(samplings, axis=1).diff()
    df_init.rename(columns={'time': 'dt'}, inplace=True)
    df_init['dt'] = df_init['dt'].map(lambda x: x.total_seconds())
    df_init['time'] = table.select(['time']).to_pandas()  # we'll need the original 'time' column for the future




    # match the column names of the dataframe with the players we're focusing on
    coords = list(map((lambda x: x + '_x'), players)) + list(map((lambda x: x + '_y'), players))
    teamCoords = list(set(coords) & set(df_init.columns))  # list of the column names of the players we're interested in
    df = df_init[['time', 'dt'] + teamCoords]

    # do some magic with the time objects in order to obtain the right time window

    # start and end match timestamps
    start_match = df['time'].iloc[0] - start_time
    end_match = df['time'].iloc[-1] - start_time

    # first recorded frame of the 2nd half & last recorded frame of the 1st half
    scnd_first_frame = df['time'].loc[df['time'].diff().map(lambda x: x.total_seconds()) > 14 * 60]
    fst_last_frame = df['time'].loc[df['time'] < scnd_first_frame.iloc[0]].iloc[-1]

    # duration of the break & 1st half
    break_dur = (scnd_first_frame - fst_last_frame).iloc[0].total_seconds()
    fst_dur = (fst_last_frame - df['time'].iloc[0]).total_seconds()

    # distinguish whether there was an overtime in the game or not and get info about the 2nd half based on that
    # (+potentially about the overtime as well)
    # Note that it might not work correctly if there were some longer interruptions during the game.
    # In our case (Italy, Wales), everything worked fine
    if (((end_match - start_match).total_seconds() - break_dur) / 60) < 120:
        scnd_dur = (end_match - start_match).total_seconds() - fst_dur - break_dur
    else:
        ot_first_frame = df['time'].loc[(df['time'].diff().map(lambda x: x.total_seconds()) < 14 * 60)
                                        & (df['time'].diff().map(lambda x: x.total_seconds()) > 4 * 60)]

        scnd_last_frame = df['time'].loc[df['time'] < ot_first_frame.iloc[0]].iloc[-1]
        scnd_dur = (scnd_last_frame - scnd_first_frame.iloc[0]).total_seconds()

    # start of the 2nd half timestamp
    start_scnd = scnd_first_frame.iloc[0] - start_time

    if first:
        start = start_match.total_seconds()
        stop = start_match.total_seconds() + fst_dur
    elif second:
        start = start_scnd.total_seconds()
        stop = start_match.total_seconds() + fst_dur + scnd_dur + break_dur
    elif regtime:
        start = start_match.total_seconds()
        stop = start_match.total_seconds() + fst_dur + scnd_dur + break_dur
    elif overtime:
        if (((end_match - start_match).total_seconds() - break_dur) / 60) < 120:
            return -1  # the game had no overtime
        else:
            # start of the overtime timestamp
            start_ot = (ot_first_frame - start_time).iloc[0]
            start = start_ot.total_seconds()
            stop = end_match.total_seconds()
    else:  # apply your custom time window
        if not 0 <= begin <= end:
            raise ValueError('invalid time window')

        # potentially 'shift' the window by the duration of the break to make up
        # for the 'time hole' in the dataframe caused by the break between the two halves
        if begin > fst_dur / 60:
            begin += break_dur / 60
        if end > fst_dur / 60:
            end += break_dur / 60

        start = begin * 60 + start_match.total_seconds()
        stop = min(end * 60, fst_dur + scnd_dur + break_dur) + start_match.total_seconds()

    # set the time window
    window_begin = datetime.fromtimestamp(start)
    window_end = datetime.fromtimestamp(stop)

    print(window_begin)
    print(window_end)

    df = df.set_index('time')
    df = df.loc[((df.index - window_begin).total_seconds() >= 0)
                & ((window_end - df.index).total_seconds() >= 0)].dropna(axis=1, how='all')

    combined = pd.DataFrame(index=df.index)

    for p in players:
        if (p + '_x') in df.columns:
            df_p = df[[(p + '_x'), (p + '_y')]].dropna()
            df_p = df_p.rolling('2550ms').median()

            df_p['dt'] = df['dt']
            df_p = df_p.loc[(0 < df_p['dt']) & (df_p['dt'] < 5 * 60)]
            df_p[p + '_mins'] = df_p['dt'].cumsum() / 60

            df_p[p + '_vx'] = df_p[(p + '_x')] / df_p['dt'] / 100
            df_p[p + '_vy'] = df_p[(p + '_y')] / df_p['dt'] / 100

            df_p = df_p.loc[(np.sqrt(df_p[p + '_vx'] ** 2 + df_p[p + '_vy'] ** 2) < 12)
                            & (np.sqrt(df_p[p + '_vx'] ** 2 + df_p[p + '_vy'] ** 2) > 0.05)]

            df_p[p + '_v'] = np.sqrt(df_p[p + '_vx'] ** 2 + df_p[p + '_vy'] ** 2)
            df_p[p + '_a'] = df_p[p + '_v'].diff() / df_p['dt']
            df_p[p + '_dist'] = np.sqrt(df_p[p + '_x'] ** 2 + df_p[p + '_y'] ** 2).cumsum() / 100000

            combined = combined.join(df_p.drop(['dt'], axis=1))

    return combined


def distsTournament(teamName, teamID):
    pass
    # TODO


def minToMin(playersA, playersB, match_path):
    pass
    # TODO


italy = getPlayerInfos(66)
ids_it = []
names = {}
for player in italy:
    ids_it.append(player.id)
    names[player.id] = player.name

path = '/home/igor/PycharmProjects/socceranalytics/dataframes/belgiumvitaly.pq'
print(prep_df(ids_it, path, begin=10, end=80))

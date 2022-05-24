import math
import sys
from datetime import datetime
import numpy as np
import pandas as pd
import pyarrow.parquet as pa
import glob
from matplotlib import pyplot as plt

from player import *

start_time = pd.Timestamp('1970-01-01 02:00:00')


# this module is supposed to replace both running.py and running_global.py
# it will be more efficient & offer some more functionality


def prep_df(players, path, first=False, second=False, regtime=False, overtime=False, begin=0, end=150):
    """
    The function prepares a dataframe containing distances, velocities, accelerations of every player from a single game,
    within the given time window
    @param players: a list of player ids of the players you're interested in
    @param path: a path to the parquet dataframe with 'raw' tracking data for every player (see snippet @422)
    @param first: a bool var -> if True, the considered time window is the 1st half only (by default set to False)
    @param second: a bool var -> if True, the considered time window is the 2nd half only (by default set to False)
    @param regtime: a bool var -> if True, the considered time window is the regular (+incl. stoppage) time only
     (by default set to False)
    @param overtime: a bool var -> if True, the considered time window is the overtime only (by default set to False)
    @param begin: a minute where your start window begins
    @param end: a minute where your start window ends
    @return: a dataframe with columns of form ['106737_dx', '106737_dy', '106737_mins', '106737_vx', '106737_vy',
       '106737_v', '106737_a', '106737_dist'...] (<playerID>_<attr>)
    """
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

    # consider the passed parameters
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
        stop = end * 60 + start_match.total_seconds()

    # set the time window
    window_begin = datetime.fromtimestamp(start)
    window_end = datetime.fromtimestamp(stop)
    df = df.set_index('time')
    df = df.loc[((df.index - window_begin).total_seconds() >= 0)
                & ((window_end - df.index).total_seconds() >= 0)].dropna(axis=1, how='all')

    combined = pd.DataFrame(index=df.index)

    # compute distances, velocities, accelerations for each player & join the resulting dfs together
    for p in players:
        if (p + '_x') in df.columns:
            df_p = df.loc[(0 < df['dt']) & (df['dt'] < 5 * 60), [(p + '_x'), (p + '_y')]]
            df_p = df_p.rolling('2250ms').median()
            df_p['dt'] = df['dt']
            df_p[p + '_mins'] = df_p['dt'].cumsum() / 60

            df_p[p + '_vx'] = df_p[(p + '_x')] / df_p['dt'] / 100
            df_p[p + '_vy'] = df_p[(p + '_y')] / df_p['dt'] / 100

            df_p = df_p.loc[(np.sqrt(df_p[p + '_vx'] ** 2 + df_p[p + '_vy'] ** 2) < 12)
                            & (np.sqrt(df_p[p + '_vx'] ** 2 + df_p[p + '_vy'] ** 2) > 0.05)]

            df_p[p + '_v'] = np.sqrt(df_p[p + '_vx'] ** 2 + df_p[p + '_vy'] ** 2)
            df_p[p + '_a'] = df_p[p + '_v'].diff() / df_p['dt']
            df_p[p + '_dist'] = np.sqrt(df_p[p + '_x'] ** 2 + df_p[p + '_y'] ** 2) / 100000

            df_p.rename(columns={(p + '_x'): (p + '_dx'), (p + '_y'): (p + '_dy')}, inplace=True)
            combined = combined.join(df_p.drop(['dt'], axis=1))

    return combined


#  & return
def distsTournament(team, players, first=False, second=False, regtime=False, overtime=False, begin=0, end=150, norm = False, save=False):
    """
    go over all team's games during the tournament and compute distances covered by every player in the team
    @param team: name of the team
    @param players: list of player ids of the team you're interested in
    @param first, second, regtime, overtime, begin, end: choose the period of the games you're interested in
    @param save: set to True if you want to store the dataframe
    @return: a df which contains distances covered by every team member in each game
    """
    pass
    directory = '/Users/igor/PycharmProjects/soccer-analytics/dataframes/'
    df = pd.DataFrame({'id': players}).set_index('id')
    for filename in glob.iglob(f'{directory}*'):
        if team.lower() in filename.lower():
            temp = prep_df(players, filename, first, second, regtime, overtime, begin, end)
            dists = [col for col in temp.columns if 'dist' in col]
            mins = [col for col in temp.columns if 'mins' in col]

            isHome = (filename[len(directory):len(directory + team)] == team)
            if isHome:
                label = team[0:3].upper() + ' - ' + filename[(len(directory) + len(team) + 1):(
                            len(directory) + len(team) + 4)].upper()
            else:
                label = filename[(len(directory)):(len(directory) + 3)].upper() + ' - ' + team[0:3].upper()

            temp2 = pd.DataFrame(temp[dists].sum(), columns={label})
            temp2.index = temp2.index.map(lambda x: x.strip('_dist'))
            if norm:
                temp3 = temp[mins].max()
                print(temp3)
                temp3.index = temp3.index.map(lambda x: x.strip('_mins'))
                # temp2 = temp2.divide(temp3)
            df = df.join(temp2)
    if save:
        df.to_parquet(team + '_dists.parquet', index=True)
    return df


def minToMin(playersA, playersB, match_path):
    """
    minute by minute distance covered comparison of two teams (based on the whole game)
    @param playersA: a list of home team's players' ids
    @param playersB: a list of away team's players' ids
    @param match_path: a path to the parquet dataframe with 'raw' tracking data for every player (see snippet @422)
    @return: a dataframe of form:
                  total_A    total_B
    min
    0.000667     0.000239   0.000326
    ...          ...        ...
    93.018667  101.266587  98.302286
    """

    # prepare the distance dataframe for both teams
    df_A = prep_df(playersA, match_path)
    df_B = prep_df(playersB, match_path)

    t = pd.DataFrame(df_A.index)
    t.set_index(df_A.index, inplace=True)
    t['time'] = t['time'].diff().map(lambda x: x.total_seconds())
    t['time'] = t.loc[t['time'] < 5 * 60, ['time']].cumsum() / 60  # filter out the break(s) - might not always work,
                                                                   # but it was sufficient in our case

    dists_A = [col for col in df_A.columns if 'dist' in col]
    df_A = df_A[dists_A]

    dists_B = [col for col in df_B.columns if 'dist' in col]
    df_B = df_B[dists_B]

    df_A['total_A'] = df_A.sum(axis=1).cumsum()

    df_A['min'] = t
    df_A.set_index('min', inplace=True)
    df_B['min'] = t
    df_B.set_index('min', inplace=True)
    df_B['total_B'] = df_B.sum(axis=1).cumsum()

    df_total = df_A.loc[:, ['total_A']].join(df_B.loc[:, ['total_B']])

    return df_total[df_total.index.notnull()]


# it - 66
# wal - 144
# bel - 13
def plotMinByMin(path, teamidA, teamidB, teamAname, teamBname, goalsA=[], goalsB=[], redA=[], redB=[], savepath=None):
    """
    plot the minute by minute distance comparison with indicators for goals and red cards
    @param path: a path to the parquet dataframe with 'raw' tracking data for every player (see snippet @422)
    @param teamidA: UEFA's teamID of home team
    @param teamidB: UEFA's teamID of away team
    @param teamAname: name of home team
    @param teamBname: name of away team
    @param goalsA: list of timestamps(in minutes) where home team scored the goals
    @param goalsB: list of timestamps(in minutes) where away team scored the goals
    @param redA: list of timestamps(in minutes) where home team got a red card
    @param redB: list of timestamps(in minutes) where away team got a red card
    @param savepath: a path to directory where you want to save the plot (by default the plot is not saved)
    """
    plrsA = getPlayerInfos(teamidA)
    ids_A = []
    for player in plrsA:
        ids_A.append(player.id)

    plrsB = getPlayerInfos(teamidB)
    ids_B = []
    for player in plrsB:
        ids_B.append(player.id)

    df = minToMin(ids_A, ids_B, path)
    if df.index[-1] >= 120:
        tick = 10
    else:
        tick = 5
    x_t = list(range(0, math.ceil(df.index[-1] + 5), tick))
    y_t = list(range(0, math.ceil(max(df['total_A'].iloc[-1], df['total_B'].iloc[-1]) + 5), 10))
    df['total_A'].plot(kind='line', xticks=x_t, yticks=y_t, label=teamAname + ' dist')
    df['total_B'].plot(kind='line', xticks=x_t, yticks=y_t, label=teamBname + ' dist', color='#e50000')
    plt.title("Minute by minute teams' distance covered")
    plt.ylabel('distance covered by teams [km]')
    plt.grid(True)
    for event in goalsA:
        plt.axvline(x=event, linestyle='dashed', label=teamAname + ' goal')
    for event in goalsB:
        plt.axvline(x=event, linestyle='dashed', label=teamBname + ' goal', color='#e50000')

    for event in redA:
        plt.axvline(x=event, linestyle='dotted', label=teamAname + ' red card')
    for event in redB:
        plt.axvline(x=event, linestyle='dotted', label=teamBname + ' red card', color='#e50000')

    plt.legend()
    if savepath is not None:
        plt.savefig(savepath + teamAname.lower() + '-' + teamBname.lower() + '_minByMin.png', dpi=300)
    plt.show()


# example of usage:

# plotMinByMin('italyvwales.pq', 66, 144, 'ITA', 'WAL', goalsA=[39], redB=[55], savepath='dashed')
# plotMinByMin('italyvspain.pq', 66, 122, 'ITA', 'SPA', goalsA=[60], goalsB=[80], savepath='dashed_')

# dict = {}
# plrsA = getPlayerInfos(66)
# ids_A = []
# for player in plrsA:
#     # print(player.name)
#     dict[player.id] = player.name
#     ids_A.append(player.id)
#
# plrsB = getPlayerInfos(144)
# ids_B = []
# for player in plrsB:
#     ids_B.append(player.id)
#
# original_stdout = sys.stdout # Save a reference to the original standard output
# # df = distsTournament('italy', ids_A, save=True)
# df2 = distsTournament('wales', ids_B, save=True)
# # df.index = df.index.map(lambda x: dict[x])
#
#
# desired_width=320
#
# pd.set_option('display.width', desired_width)
# pd.set_option('display.max_columns',10)
#
# print(df2)



# print(ids_A)
# print(prep_df(ids_A, 'italyvwales.pq', first=True,))
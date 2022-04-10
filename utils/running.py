from datetime import datetime
import multiprocess as mp
import numpy as np
import pandas as pd
import pyarrow.parquet as pa
import scipy.signal as signal

start_time = pd.Timestamp('1970-01-01 02:00:00')

# a global dictionary with entries of form: {'player.id':<distance covered>}
# for all the players passed as list of Player objects to distTeam() function
plrs = mp.Manager().dict()

global table, normalized, start, stop
normalized = False
start = 0
stop = 150


def distTeam(players, path, begin, end, norm=False):
    """
    computes distance [in km rounded to 3 decimal places] covered by every Player p whose id
    is passed in :param players by running :distPlayer(p.id) on it
    and stores it in the global plrs dictionary

    to speed things up, some concurrency is incorporated
    :param players: list of IDs of the players
    :return: None - the function updates the global dictionary plrs with entries of
    form {'p.id':<distance_covered_by_player_p>}
    """
    if begin >= end:
        return
    global table, normalized, start, stop
    table = pa.read_table(path)
    start = begin
    stop = end
    if norm:
        normalized = True
    plrs.clear()  # clear plrs, so that only data of players from one list is kept there at a time
    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(distPlayer, players)

    normalized = False
    start = 0
    stop = 150


def distPlayer(id):
    """
    computes distance covered during the game by a single player
    based on the reliable samplings

    does some basic filtering of errors/weird results

    :param id: id of a player, given by UEFA
    :return: if  player didn't play
    """

    if (str(id) + '_x') not in table.column_names:
        return 0

    # pick the columns of the player & use only reliable samplings
    df = table.select(['time', str(id) + '_x', str(id) + '_y',
                       str(id) + '_sampling', str(id) + '_type']).to_pandas()
    # df = df.loc[(df[str(id) + '_sampling'] == 1)]
    df = df.loc[(df[str(id) + '_sampling'] != 2)]

    dist_delta = pd.DataFrame({'dx': df[str(id) + '_x'].diff(),
                               'dy': df[str(id) + '_y'].diff(),
                               'dt': df['time'].diff().map(lambda x: x.total_seconds()),
                               'time': df['time']})

    # set the time window according to global parameters start and stop
    scnd_half_start = df['time'].loc[df['time'].diff().map(lambda x: x.total_seconds()) > 14 * 60]
    last_fst_half = df['time'].loc[df['time'] < scnd_half_start.iloc[0]].iloc[-1]
    break_time = (scnd_half_start - last_fst_half).iloc[0].total_seconds() / 60
    first_half_dur = (last_fst_half - dist_delta['time'].iloc[0]).total_seconds() / 60
    second_half_dur = dist_delta['time'].iloc[-1] - scnd_half_start
    global start, stop
    if start > first_half_dur:
        start += break_time
    if stop > first_half_dur:
        stop += break_time

    start_match = dist_delta['time'].iloc[0] - start_time
    end_match = dist_delta['time'].iloc[-1] - start_time
    dist_delta = dist_delta.set_index('time')

    window_begin = max(datetime.fromtimestamp(start_match.total_seconds() + 60 * start),
                       datetime.fromtimestamp(start_match.total_seconds()))

    window_end = min(datetime.fromtimestamp(start_match.total_seconds() + 60 * (stop + 1)),
                     datetime.fromtimestamp(end_match.total_seconds()))
    dist_delta = dist_delta.loc[((dist_delta.index - window_begin).total_seconds() / 60 >= 0)
                                & ((window_end - dist_delta.index).total_seconds() / 60 > 0)]

    # add velocity vectors for each timestamp
    dist_delta['vx'] = dist_delta['dx'] / dist_delta['dt'] / 100
    dist_delta['vy'] = dist_delta['dy'] / dist_delta['dt'] / 100

    # filter out erroneous position frames
    dist_delta = dist_delta.loc[(0 < dist_delta['dt']) & (dist_delta['dt'] < 5 * 60)
                                & (np.sqrt(dist_delta['vx'] ** 2 + dist_delta['vy'] ** 2) < 12)
                                & (np.sqrt(dist_delta['vx'] ** 2 + dist_delta['vy'] ** 2) > 0.05)]

    # smooth out the results - if the results are not satisfying, one can play around with the
    # sizes of the moving windows
    #
    # distances smoothed using rolling median (moving time window of size 2.8s)
    # velocities smoothed using Savitzky-Golay filter (of linear order, window of size 25 entries ~ 1s)
    dist_delta['dx'] = dist_delta['dx'].rolling('2800ms').median()
    dist_delta['dy'] = dist_delta['dy'].rolling('2800ms').median()
    if not pd.isnull(dist_delta['vx']).all():
        dist_delta['vx'] = signal.savgol_filter(dist_delta['vx'], 25, 1)
        dist_delta['vy'] = signal.savgol_filter(dist_delta['vy'], 25, 1)

    # total velocity & acceleration
    # cumulative distance covered & cumulative minutes played (counting from 'start' parameter)
    dist_delta['v'] = np.sqrt(dist_delta['vx'] ** 2 + dist_delta['vy'] ** 2)
    dist_delta['a'] = dist_delta['v'].diff() / dist_delta['dt']
    dist_delta['c_dist'] = np.sqrt(dist_delta['dx'] ** 2 + dist_delta['dy'] ** 2).cumsum() / 100000
    dist_delta['mins'] = dist_delta['dt'].cumsum() / 60

    distance = dist_delta['c_dist'].max()
    mins_played = dist_delta['mins'].max()

    if normalized:
        distance = round(distance * 90 / mins_played, 3)
    else:
        distance = round(distance, 3)

    plrs[id] = distance

    return distance



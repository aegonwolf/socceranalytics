import multiprocess as mp
import numpy as np
import pandas as pd
import pyarrow.parquet as pa
from player import getPlayerInfos

# get your input
# keep in mind that the script is going to work with the parquet file
# which has the structure of the output of the code (toframe1.py) I sent on 22.03.22 on discord
table = pa.read_table('_your_input_file_path_')

# a global dictionary with entries of form: {'player.id':<distance covered>}
# for all the players passed as list of Player objects to distTeam() function
plrs = mp.Manager().dict()


def distTeam(players):
    """
    computes distance [in km rounded to 3 decimal places] covered by every Player p whose id
    is passed in :param players by running :distPlayer(p.id) on it
    and stores it in the global plrs dictionary

    to speed things up, some concurrency is incorporated
    :param players: list of IDs of the players
    :return: None - the function updates the global dictionary plrs with entries of
    form {'p.id':<distance_covered_by_player_p>}
    """
    plrs.clear()  # clear plrs, so that only data of players from one list is kept there at a time
    with mp.Pool(mp.cpu_count()) as pool:
        pool.map(distPlayer, players)


def distPlayer(id):
    """
    computes distance covered during the game by a single player
    based on the reliable samplings

    does some basic filtering of errors/weird results

    :param id: id of a player, given by UEFA
    :return: if  player didn't play
    """
    if ('player' + str(id) + '_x') not in table.column_names:
        return 'didn\'t play'

    # pick the columns of the player & use only reliable samplings
    df = table.select(['time', 'player' + str(id) + '_x', 'player' + str(id) + '_y',
                       'player' + str(id) + '_sampling']).to_pandas()
    df = df.loc[(df['player' + str(id) + '_sampling'] == 1)]

    # we shift the 'coordinate vectors' by duplicating first resp. last row,
    # so that we can efficiently compute the differences in distances later
    df_padded_first = pd.concat([df.head(1), df]).reset_index(drop=True)  # [(x1,y1),(x1,y1),(x2,y2),...,(xn, yn)]
    df_padded_last = pd.concat([df, df.tail(1)]).reset_index(drop=True)  # [(x1,y1),(x2,y2),...,(xn, yn),(xn, yn)]

    # dataframe which contains time differences between the adjacent samplings
    # converted into floats [unit: seconds], so that we can compare/filter them easily
    t_delta = pd.DataFrame(df_padded_last['time'] - df_padded_first['time'])
    t_delta['time'] = t_delta['time'].map(lambda x: x.total_seconds())

    # create dataframe dist_delta containing the distances covered between
    # the samplings.
    # each entry is of form: sqrt((x_{i+1} - x_{i})^2 + (y_{i+1} - y_{i})^2)
    x_delta = pd.DataFrame()
    x_delta['dist'] = ((df_padded_last['player' + str(id) + '_x'] -
                       df_padded_first['player' + str(id) + '_x']) ** 2)

    y_delta = pd.DataFrame()
    y_delta['dist'] = ((df_padded_last['player' + str(id) + '_y'] -
                       df_padded_first['player' + str(id) + '_y']) ** 2)

    dist_delta = (x_delta + y_delta).applymap(np.sqrt)

    # compute the distance covered by summing up the partial distances, with filtering out the
    # "distance covered" between the last sampling of the 1st half and first sampling of the 2nd half
    # (i.e. delta_t must be within 3 minutes [can be adapted in case of overtimes etc.])     -- 1st&2nd conditions
    # as well as some anomalies, such as running faster than Usain Bolt (>12.3m/s)           -- 3rd condition
    # or ultra slow walking (<0.333m/s)                                                      -- 4th condition
    # [such entries are treated as errors and are ignored]
    df2 = pd.concat([dist_delta, t_delta.rename(columns={'time': 'delta_t'})], axis=1)
    distance = df2.loc[(0 < df2['delta_t']) & (df2['delta_t'] < 180)
                       & (df2['dist'] / (100 * df2['delta_t']) < 12.3)
                       & (df2['dist'] / (100 * df2['delta_t']) > 0.333), 'dist'].sum()

    plrs[id] = round(distance / 100000, 3)
    return distance


# ============================================================#
# demo part

def printDistances(team):
    """
    for every player of :param team who played, print their distance covered
    """
    for key in plrs.keys():
        x = next((p for p in team if p.id == key), False)
        if x:
            print(x.name + ':', str(plrs[key]) + 'km')


italy = getPlayerInfos(66)
wales = getPlayerInfos(144)

ids_it, ids_w = [], []
for player in italy:
    ids_it.append(player.id)
for player in wales:
    ids_w.append(player.id)

print('Italy: ')
distTeam(ids_it)
printDistances(italy)

total_it = 0
for value in plrs.values():
    total_it += value

total_it = round(total_it, 3)

print('\n\nWales: ')
distTeam(ids_w)
printDistances(wales)

total_w = 0
for value in plrs.values():
    total_w += value

total_w = round(total_w, 3)
total = total_w + total_it
print('\n\nItaly:', str(total_it) + 'km\nWales', str(total_w) + 'km\nTotal:', str(total) + 'km')

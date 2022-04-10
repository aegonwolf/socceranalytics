import glob
from run_smooth import *


def dists_team(team, players, norm=False, start=0, end=150, save=False, path=None):
    """
    goes over all dataframes in the directory and for each filename incl. param: team in its' name computes
    the distances covered for each player from param: players
    Parameters
    ----------
    team: name of the team; e.x. "italy" - make sure that all the dataframe files for the games of your team are of
            format "<opponent_team>vteam" or "teamv<opponent_team> !!!
    players: a list of player ids
    norm: if True, the resulting dataframe contains normalized distances (over 90 min) - by default False (computes
            total distances)
    start: minute of the match where you start considering the distances covered
    end: minute of the match after which you don't further consider the distances covered
    default values of start and end result in considering the whole game
    Returns
    -------
    a dataframe with player ids as indices, game as columns and distances as entries. A sample how it's structured:
                  TUR - WAL  ITA - WAL  WAL - DEN  WAL - SWI
    id
    74897            NaN        NaN        NaN        NaN
    250012939      4.340      4.220      3.929      4.241
    250100010        NaN        NaN        NaN        NaN
    102221           NaN      8.861        NaN        NaN
    250113272      9.206      9.480      8.991        NaN
    250012942      9.332      9.796      9.155      9.216
    ...
    """
    directory = '/home/igor/PycharmProjects/socceranalytics/dataframes/'
    df = pd.DataFrame({'id': players}).set_index('id')
    for filename in glob.iglob(f'{directory}*'):
        if team.lower() in filename.lower():
            isHome = (filename[len(directory):len(directory + team)] == team)

            distTeam(players, filename, start, end, norm)
            if isHome:
                label = team[0:3].upper() + ' - ' + filename[(len(directory) + len(team) + 1):(len(directory) + len(team) + 4)].upper()
            else:
                label = filename[(len(directory)):(len(directory) + 3)].upper() + ' - ' + team[0:3].upper()

            temp = pd.DataFrame.from_dict(plrs, orient='index', columns={label})
            df = df.join(temp)
    if save:
        path += team
        if norm:
            path += 'Norm'
        df.to_parquet(path + '.parquet', index=True)
    return df


# italy = getPlayerInfos(66)
# ids_it = []
# names = {}
# for player in italy:
#     ids_it.append(player.id)
#     names[player.id] = player.name
#
# print('Italy:')
# print(dists_team('italy', ids_it, True))
# print(dists_team('italy', ids_it, False))
#
# wales = getPlayerInfos(144)
# ids_wal = []
# names = {}
# for player in wales:
#     ids_wal.append(player.id)
#     names[player.id] = player.name
#
# print('Wales')
# print(dists_team('wales', ids_wal, True))
# print(dists_team('wales', ids_wal, False))
#

# poland = getPlayerInfos(109)
# ids_pl = []
# names = {}
# for player in poland:
#     ids_pl.append(player.id)
#     names[player.id] = player.name
#
#
# print(dists_team('poland', ids_pl, True, 0, 130))
import pandas as pd
import datetime
import xml.etree.ElementTree as et
import numpy as np

#----------------------------------------------------------------------------
# Created By: Danny Camenisch (dcamenisch)
# Created Date: 10/03/2022
# version ='1.1'
# ---------------------------------------------------------------------------
""" 
Simple module to convert a xml file containing data in TRACAB format to a Match object
"""
# ---------------------------------------------------------------------------

class Match:
    def __init__(self, filePath):
        match = et.parse(filePath).getroot()[0]

        self.matchID      = int(match.attrib['id'])
        self.matchNr      = int(match.attrib['matchNumber'])
        self.date         = match.attrib['dateMatch']
        self.stadiumID    = int(match[1].attrib['id'])
        self.stadiumName  = match[1].attrib['name']
        self.pitchLength  = int(match[1].attrib['pitchLength'])
        self.pitchWidth   = int(match[1].attrib['pitchWidth'])
        self.phases       = [Phase(phase) for phase in match[2]]
        self.frames       = [Frame(frame) for frame in match[3]]

        self.removeExcessFrames()
        
    def removeExcessFrames(self):
        keep = []
        for frame in self.frames:
            for phase in self.phases:
                if frame.time >= phase.start and frame.time <= phase.end:
                    keep.append(frame)
                    break

        self.frames = keep


class Phase:
    def __init__(self, phase):
        self.start       = phase.attrib['start']
        self.end         = phase.attrib['end']
        self.leftTeamID  = int(phase.attrib['leftTeamID'])
        
class Frame:
    def __init__(self, frame):
        self.time            = frame.attrib['utc']
        self.ballInPlay      = frame.attrib['isBallInPlay']
        self.ballPossession  = frame.attrib['ballPossession']
        self.trackingObjs    = [TrackingObj(obj) for obj in frame[0]]
    
class TrackingObj:
    def __init__(self, obj):
        self.type      = obj.attrib['type']
        self.id        = obj.attrib['id']
        self.x         = int(obj.attrib['x'])
        self.y         = int(obj.attrib['y'])
        self.sampling  = obj.attrib['sampling']


def load_data(path):
    # import match as m  # Danny's Match object, catches the frames sampled during the actual game
    match = Match(path)
    framedict = dict()

    for index, frame in enumerate(match.frames):
        # time is stored as datetime objects - makes it easier to do operations/comparisons on it
        time = frame.time.replace('Z', '').replace('T', ' ')
        columns = dict()
        if '.' not in time: # turns out that for some games there are frames for which milliseconds are dropped 
            time += '.0'    # in such case we add them artificially, so that the string format matches
        columns['time'] = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        columns['ball_possession'] = frame.ballPossession
        columns['ball_in_play'] = frame.ballInPlay

        for i, obj in enumerate(frame.trackingObjs):
            if obj.type == '7':
                for key, value in obj.__dict__.items():
                    columns["ball_" + key] = int(value)
            else:
                # Each player with id Q, who played during the match gets their own columns:
                # "playerQ_type", "playerQ_id"*, "playerQ_x", "playerQ_y" with the respective data.
                # In case the player got subbed on/off at some point, the entries corresponding to
                # the time the player was off the pitch have value <null>
                for key, value in obj.__dict__.items():
                    #  *since we encode players' IDs in the columns' names, you might  want to avoid
                    #   some data redundancy and skip the ID columns, depending on the application
                    # if key == 'id':
                    #     continue

                    columns["player" + str(obj.id) + "_" + key] = int(value)

        framedict[index] = columns

    # convert into pandas dataframe & export as parquet file
    df = pd.DataFrame.from_dict(framedict, orient='index')
    return df


def correct_player_cordinates(df, breaks):
    players_coords_keys = [key for key in df.keys() if '_x' in key or '_y' in key or 'time' in key]
    df_players = df[players_coords_keys]

    player_ids_home = [key.split('_')[0] for key in [k for k in df.keys() if 'type' in k] if df[key].mean() == 0]
    player_ids_away = [key.split('_')[0] for key in [k for k in df.keys() if 'type' in k] if df[key].mean() == 1]

    # get all possibilities of keys
    keys_home_x = [key + '_x' for key in player_ids_home]
    keys_home_y = [key + '_y' for key in player_ids_home]
    keys_away_x = [key + '_x' for key in player_ids_away]
    keys_away_y = [key + '_y' for key in player_ids_away]
    players_x = keys_home_x + keys_away_x
    players_y = keys_home_y + keys_away_y

    # flip second half
    df_players.loc[breaks.index[0]:, players_x] = -df_players.loc[breaks.index[0]:, players_x]
    df_players.loc[breaks.index[0]:, players_y] = -df_players.loc[breaks.index[0]:, players_y]

    # make all players play into the same direction
    if min(df_players.loc[0][keys_home_x].values) < -3500:
        # team1 plays left to right:
        df_players[keys_home_x] = -df_players[keys_home_x].values
    elif min(df_players.loc[0][keys_away_x].values) < -3500:
        # team1 plays left to right:
        df_players[keys_away_x] = -df_players[keys_away_x].values
    else: print("error, goalkeeper was not detected. Try varying the threshold.")

    # correct for odd TRACAB data format
    df_players[players_x] = df_players[players_x].values/100
    df_players[players_y] = df_players[players_y].values/100 + 68

    return df_players


def get_sg_window_coords(df, df_players, phases, ball_possessions, breaks):
    player_ids_home = [key.split('_')[0] for key in [k for k in df.keys() if 'type' in k] if df[key].mean() == 0]
    player_ids_away = [key.split('_')[0] for key in [k for k in df.keys() if 'type' in k] if df[key].mean() == 1]

    # get all possibilities of keys
    keys_home_x = [key + '_x' for key in player_ids_home]
    keys_home_y = [key + '_y' for key in player_ids_home]
    keys_away_x = [key + '_x' for key in player_ids_away]
    keys_away_y = [key + '_y' for key in player_ids_away]
    players_home = sorted(keys_home_x + keys_home_y)
    players_away = sorted(keys_away_x + keys_away_y)

    phases = (
        (
            (ball_possessions != ball_possessions.shift())
            | df_players.index.isin(df_players.index[(df_players.isnull().shift() != df_players.isnull()).any(axis=1)]) # substitutions
            | df_players.index.isin(breaks.index) # halftimes
        )
        .cumsum()
    )

    windows_mask = pd.Series(
            (df_players.index.isin(df_players.index[(df_players.isnull().shift() != df_players.isnull()).any(axis=1)])
            | df_players.index.isin(breaks.index)), index=df_players.index)
    windows_mask.iloc[-1] = True
    windows_mask_index = windows_mask[windows_mask == True].index
    phases_split = [phases.loc[windows_mask_index[i]:windows_mask_index[i+1]] for i in range(len(windows_mask_index)-1)]

    phase_cutoff = 5*25

    windows = {key: [] for key in ball_possessions.unique()} # dict storing the windows
    window_length = 60*25 # seconds

    # create windows
    for phases in phases_split:
        phase_lengths = phases.value_counts(sort=False)
        short_phases = phase_lengths.index[phase_lengths < phase_cutoff]
        phases = phases.loc[~phases.isin(short_phases)]
        phase_possessions = ball_possessions.loc[phases.index].groupby(phases).first()
        phase_lengths = phases.value_counts(sort=False) # update phase lengths

        w = {key: [] for key in ball_possessions.unique()}
        for index, value in phases.iteritems(): 
            w[phase_possessions[value]].append(index)

        # append windows globally for all phase splits
        for key, value in w.items():
            windows[key] += [value[i:i+window_length] 
                    for i in range(0, len(value), window_length)
                    if len(value) - i > 30*25] # only keep windows of length > 30s
    del windows['None'] # remove out-of-play and contested phases

    # convert windows into phases
    phases = pd.Series({v:k for k, vlist in dict(enumerate(sorted(windows['Home'] + windows['Away']))).items() for v in vlist})

    # extract windows from phases
    window = []
    windows_coords = {'team_1_offensive': [], 'team_1_defensive': [], 'team_2_offensive': [], 'team_2_defensive': []}
    a = (phases != phases.shift())

    for idx in phases.index:
        # Problem: after a red card there are only 10 players and the reshape does not work
        # player250097090_x
        try:
            if ((a[idx] == True) or (idx == a.index[-1])) and (idx != a.index[0]):
                if ball_possessions[window[0]] == 'Home':
                    active_players_home = df_players.loc[window][players_home].isnull().any().index[~df_players.loc[window][players_home].isnull().any()]
                    active_players_away = df_players.loc[window][players_away].isnull().any().index[~df_players.loc[window][players_away].isnull().any()]

                    windows_coords['team_1_offensive'].append((df_players.loc[window][active_players_home].values.reshape(-1, 11, 2)))
                    
                    if len(active_players_away) < 22:
                        active_players_away.append('player250097090_x')
                        active_players_away.append('player250097090_y')
                    
                    windows_coords['team_2_defensive'].append((df_players.loc[window][active_players_away].values.reshape(-1, 11, 2)))
                
                else:
                    active_players_home = df_players.loc[window][players_home].isnull().any().index[~df_players.loc[window][players_home].isnull().any()]
                    active_players_away = df_players.loc[window][players_away].isnull().any().index[~df_players.loc[window][players_away].isnull().any()]
                    windows_coords['team_1_defensive'].append((df_players.loc[window][active_players_home].values.reshape(-1, 11, 2)))
                    
                    if len(active_players_away) < 22:
                        active_players_away.append('player250097090_x')
                        active_players_away.append('player250097090_y')
                    
                    windows_coords['team_2_offensive'].append((df_players.loc[window][active_players_away].values.reshape(-1, 11, 2)))
                    
                window = [idx]
            else: 
                window.append(idx)
        except:
            print(active_players_away)
            print(active_players_home)
            break


    return windows_coords
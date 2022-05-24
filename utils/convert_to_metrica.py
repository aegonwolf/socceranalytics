import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from tqdm import tqdm

import xml.etree.ElementTree as ET # parsing XML files

# parse xml file

class Match_b:
    def __init__(self, match):
        self.matchID      = int(match.attrib['id'])
        self.matchNr      = int(match.attrib['matchNumber'])
        self.date         = match.attrib['dateMatch']
        self.stadiumID    = int(match[1].attrib['id'])
        self.stadiumName  = match[1].attrib['name']
        self.pitchLength  = int(match[1].attrib['pitchLength'])
        self.pitchWidth   = int(match[1].attrib['pitchWidth'])
        self.phases       = match[2]
        self.frames       = match[3]

path = 'data/tracab/Italy v Wales.xml'
tree = ET.parse(path).getroot()
match = Match_b(tree[0])


# Now convert to pandas and save

framedict_players = dict()
framedict_ball = dict()
path_to_data = 'data/metrica/'
savepath_pl = path_to_data + "tracking_players.parquet"
savepath_ph = path_to_data + "tracking_phases.parquet"
savepath_b = path_to_data + "tracking_ball.parquet"
i = 0
j = 0
for index, frame in enumerate(match.frames):
  time = datetime.fromisoformat(frame.attrib["utc"][:-1])
  
  for id, obj in enumerate(frame[0]):
    columns = dict()
    columns['time'] = time
    columns['frame'] = index
    if id == 0: #ball
      for key, value in obj.attrib.items():
        columns["ball_" + key] = int(value)
      framedict_ball[j] = columns
      j = j+1
      
    else:
      for key, value in obj.attrib.items():
        columns["player_" + key] = int(value)
      framedict_players[i] = columns
      i = i+1

phases = dict()
for index, phase in enumerate(match.phases):
    phases[index] =  phase.attrib

df_ph = pd.DataFrame.from_dict(phases, orient='index')
df_ph['start'] = df_ph['start'].apply(lambda x: datetime.fromisoformat(x[:19]))
df_ph['end'] = df_ph['end'].apply(lambda x: datetime.fromisoformat(x[:19]))
df_ph.to_parquet(savepath_ph, index = False)

df_p = pd.DataFrame.from_dict(framedict_players, orient='index')
df_p.to_parquet(savepath_pl, index = False)

df_b = pd.DataFrame.from_dict(framedict_ball, orient='index')
df_b.to_parquet(savepath_b, index = False)

# just short helpers
path = 'data/metrica/'
def load_data_pandas(file):
    return pd.read_parquet(path+file)
def save_data_pandas(df, file):
    df.to_parquet(path+file)

# helper coordinate conversion
def trac_to_metr_x(x):
    return x / 10500.0 + 0.5

def trac_to_metr_y(y):
    return y / -6800.0 + 0.5

def trac_to_metr(x, y):
    return (trac_to_metr_x(x), trac_to_metr_y(y))


#load data
df = load_data_pandas('tracking_players.parquet')
ball_data = load_data_pandas('tracking_ball.parquet')
phases = load_data_pandas('tracking_phases.parquet')


# get unique player ids

player_ids_1 = df[df['player_type']==0]['player_id'].unique().tolist()
# I found this necessary for the pitch controll code
while len(player_ids_1)<14:
    player_ids_1.append(-1)

player_ids_2= df[df['player_type']==1]['player_id'].unique().tolist()
# I found this necessary for the pitch controll code
while len(player_ids_2)<14:
    player_ids_2.append(-1)


# make base skeleton with times and frames
fd1 = dict()

frame = dict()
period = dict()
times = dict()
start = phases.start[0]
half = phases.end[0]
for ind, row in ball_data[['time', 'frame']].drop_duplicates().iterrows():
    fr = row['frame']
    frame[fr] = fr
    times[fr] = np.timedelta64(row['time']-start).astype('timedelta64[ms]').astype('float')/1000
    period[fr] = int(1 if row['time']<half else 2)
    
fd1['Period'] = period
fd1['Frame'] = frame
fd1['Time [s]'] = times

fd2 = fd1.copy()


#This is not very efficient, but it works so...

#add data for players

for pl_ind, id in enumerate(tqdm(player_ids_1)):
    pl_x = dict()
    pl_y = dict()
    for row_ind, row in df[df['player_id']==id].iterrows():
        pl_x[row['frame']] = trac_to_metr_x(row['player_x'])
        pl_y[row['frame']] = trac_to_metr_y(row['player_y'])
    fd1['Player'+str(pl_ind+1)] = pl_x
    fd1['Unnamed: '+str(2*pl_ind+4)] = pl_y

for pl_ind, id in enumerate(tqdm(player_ids_2)):
    pl_x = dict()
    pl_y = dict()
    for row_ind, row in df[df['player_id']==id].iterrows():
        pl_x[row['frame']] = trac_to_metr_x(row['player_x'])
        pl_y[row['frame']] = trac_to_metr_y(row['player_y'])
    fd2['Player'+str(pl_ind+2)] = pl_x
    fd2['Unnamed: '+str(2*pl_ind+4)] = pl_y


#add data for ball
colx = dict()
coly = dict()
for ind, row in ball_data.iterrows():
    fr = row['frame']
    colx[fr] = trac_to_metr_x(row['ball_x'])
    coly[fr] = trac_to_metr_y(row['ball_y'])
fd1['Ball'] = colx
fd1['Unnamed: '+str(len(fd1))] = coly
fd2['Ball'] = colx
fd2['Unnamed: '+str(len(fd2))] = coly

# make dataframes
df1 = pd.DataFrame(fd1).astype({'Frame':'int', 'Period':'int'})
df2 = pd.DataFrame(fd2).astype({'Frame':'int', 'Period':'int'})


# save files
save_data_pandas(df1,"tracking_team1.parquet")
save_data_pandas(df2,"tracking_team2.parquet")
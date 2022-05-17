import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

wyscoutPath   = f'data/wyscout/5034296/5034296_events.json'
statsbombPath = f'data/statsbomb360/events/3788766.json'
save_path     = 'assets/xG-Graph.png'


def get_json(filepath):
    with open(filepath, encoding='utf8') as f:
        js = json.load(f)
        return js


#load both datasets into dataframes [TODO adapt file names/relative paths]
wyscout = pd.json_normalize(get_json(wyscoutPath)['events'])
statsb = pd.json_normalize(get_json(statsbombPath))


#filter for shots and extract only relevant information into unified format [minute, second, xg, team, isGoal]
shots_wy_r = wyscout[((wyscout['type.primary']=='shot') | (wyscout['type.primary']=='penalty'))]
shots_sb_r = statsb[statsb['type.name']=='Shot']

shots_wy = shots_wy_r[['minute','second','shot.xg','team.name','shot.isGoal']].rename(columns={'shot.xg':'xg', 'team.name':'team', 'shot.isGoal':'isGoal'})

shots_sb_r['isGoal'] = shots_sb_r['shot.outcome.name']=='Goal'
shots_sb = shots_sb_r[['minute','second','shot.statsbomb_xg', 'possession_team.name', 'isGoal']].rename(columns={'shot.statsbomb_xg':'xg', 'possession_team.name':'team'})


#when passed data for one team in format [minute, second, cumXg(cumulated xg), ...] returns dataframe with points that create the 'steps' in the plot
def cleanLines(data, max_):
    '''inserts additional data points to create the steps'''
    n = data.shape[0]
    time = np.zeros(2*n+2, float)
    time[-1] = max_
    time[1:-1:2] = data['minute'] + data['second']/60.
    time[2::2] = data['minute'] + data['second']/60.
    plot_xg = np.zeros(2*n+2, float)
    plot_xg[2:-1:2] = data['cumXg']
    plot_xg[3::2] = data['cumXg']
    
    return pd.DataFrame(data={'time':time, 'xg':plot_xg})

#seperates data by team, plots stepplot and points for goals
def plot_xg(data_wy, data_sb, end, colors):
    teams = data_wy['team'].unique()

    for team, color in zip(teams, colors):
        data_t_wy = data_wy[data_wy['team']==team].copy()
        data_t_sb = data_sb[data_sb['team']==team].copy()

        data_t_wy['cumXg'] = np.cumsum(data_t_wy['xg'])
        data_t_sb['cumXg'] = np.cumsum(data_t_sb['xg'])

        df_wy = cleanLines(data_t_wy, end)
        df_sb = cleanLines(data_t_sb, end)

        plt.plot(df_wy['time'], df_wy['xg'], label=team + ' [Wyscout]', color=color[0])
        plt.plot(df_sb['time'], df_sb['xg'], label=team + ' [Statsbomb]', color=color[1])

        data_g_wy = data_t_wy[data_t_wy['isGoal']]
        data_g_sb = data_t_sb[data_t_sb['isGoal']]

        plt.scatter(data_g_wy['minute'] + data_g_wy['second']/60., data_g_wy['cumXg'], color=color[0])
        plt.scatter(data_g_sb['minute'] + data_g_sb['second']/60., data_g_sb['cumXg'], color=color[1])

    plt.legend()

config = get_json('plot_config.json')

# actual plotting
fig, ax = plt.subplots(figsize=(12, 7))

ax.set_title("xGoals", fontsize=16, fontweight="semibold")
ax.set_ylabel("Cumulative Expected Goals", fontsize=12, fontweight="light")
ax.set_xlabel("Minute", fontsize=12, fontweight="light")

ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
ax.minorticks_on()
ax.tick_params(which='minor', bottom=False, left=False)

ax.set_xlim(0, 93)

plot_xg(shots_wy, shots_sb, wyscout.iloc[-1].minute, colors=[['cornflowerblue', 'darkblue'], ['darkred', 'indianred']])

plt.savefig(save_path)

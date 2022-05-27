import matplotlib.pyplot as plt
import numpy as np
import json

from mplsoccer import Radar, FontManager
import matplotlib.pyplot as plt

URL4 = 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Thin.ttf?raw=true'
URL5 = 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Regular.ttf?raw=true'
URL6 = 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Bold.ttf?raw=true'

robotto_thin        = FontManager(URL4)
robotto_regular     = FontManager(URL5)
robotto_bold        = FontManager(URL6)

# Parameters we are interested in
list_params = [ 
    "shots",
    "crosses",
    "duelsWon",
    "progressiveRun",
    "foulsSuffered",
    "successfulDribbles",
    "successfulPasses",
    "successfulAttackingActions",
    "fouls",
    "successfulPasses",
    "recoveries",
    "losses",
    "clearances",
    "interceptions",
    "successfulDefensiveAction",
    'xgSave',
    'successfulGoalKicks',
    'gkExits',
    'gkSaves',
]

attack_params = [
    "shots",
    "crosses",
    "duelsWon",
    "progressiveRun",
    "foulsSuffered",
    "successfulDribbles",
    "successfulPasses",
    "successfulAttackingActions"
]

defense_params = [ 
    "fouls",
    "losses",
    "duelsWon",
    "recoveries",
    "clearances",
    "interceptions",
    "successfulPasses",
    "successfulDefensiveAction"
]

gk_params = [
    'losses',
    'xgSave',
    'successfulGoalKicks',
    'gkExits',
    'gkSaves',
    'successfulPasses',
    'successfulDefensiveAction'
]

matches = {
    'Both':  ['5034296'],
    'Wales': ['5111396', '5034293', '5034292'],
    'Italy': ['5111410', '5111408', '5111404', '5111397', '5034294', '5034291']
}

all_matches = ['5034296', '5111410', '5111408', '5111404', '5111397', '5034294', '5034291', '5111396', '5034293', '5034292']

defense = {
 'Centre Back',
 'Defensive Midfielder',
 'Left Back',
 'Left Back (5 at the back)',
 'Left Centre Back',
 'Left Centre Back (3 at the back)',
 'Right Back',
 'Right Back (5 at the back)',
 'Right Centre Back',
 'Right Centre Back (3 at the back)',
}

attack = {
 'Left Centre Midfielder',
 'Left Wing Forward',
 'Left Winger',
 'Right Centre Midfielder',
 'Right Wing Forward',
 'Right Winger',
 'Striker'
}

#############
# Functions #
#############

def get_player_ids():
    player_ids = {
        'Italy': set(),
        'Wales': set()
    }

    player_names = {}
    match_id = matches['Both'][0]

    with open(f'data/wyscout/games/{match_id}/{match_id}_events.json', 'r') as f: 
        data = json.load(f)

    for event in data['events']:
        if event['player'] != None:
            player_id = event['player']['id']
            player_name = event['player']['name']

            player_names[player_id] = player_name

            if event['team']['name'] == 'Italy':
                player_ids['Italy'].add(player_id)
            elif event['team']['name'] == 'Wales':
                player_ids['Wales'].add(player_id)

    return player_ids, player_names

def get_player_position():
    player_position = {}

    with open(f'data/wyscout/games/5034296/5034296_playerstats.json', 'r') as f: 
        data = json.load(f)

        for player in data['players']:
            if len(player['positions']) == 0:
                continue

            position = player['positions'][0]['position']['name']
            player_position[player['playerId']] = position

    return player_position

def filter_data(data, player_ids):
    players_filtered = {}

    for player in data['players']:
        pid = player['playerId']

        if pid in player_ids['Italy'] or pid in player_ids['Wales']: 
            players_filtered[pid] = {}

            for param in list_params:
                players_filtered[pid][param] = player['total'][param]

    return players_filtered

#############
# Main code #
#############

# Loading all the player stats from the games
player_ids, player_names = get_player_ids()
player_position = get_player_position()

player_stats = {}
for match_id in all_matches:
    with open(f'data/wyscout/games/{match_id}/{match_id}_playerstats.json', 'r') as f: 
        data = json.load(f)
        player_stats[match_id] = filter_data(data, player_ids)


# Calculating the average stats for each player
player_stats_avarage = {}
for team in ['Italy', 'Wales']:
    player_stats_avarage[team] = {}

    for player_id in player_ids[team]:
        player_stats_avarage[team][player_id] = {}

        for param in list_params: 
            player_stats_avarage[team][player_id][param] = 0

        for match_id in player_stats.keys():
            if player_id in player_stats[match_id].keys():           
                for param in list_params:
                    player_stats_avarage[team][player_id][param] += player_stats[match_id][player_id][param] / (len(matches[team]) + 1)


# Get all the values for each parameter
params_values = {}
for param in list_params:
    params_values[param] = []

for player in player_stats[matches['Both'][0]].values():
    for param in list_params:
        params_values[param].append(player[param])


# Get the maximum value for each parameter
params_values_max = {}
for param in list_params:
    params_values_max[param] = np.amax(np.array(params_values[param]))

high_att = [params_values_max[param] for param in attack_params]
low_att =  [0 for i in attack_params]

high_def = [params_values_max[param] for param in defense_params]
low_def =  [0 for i in defense_params]

high_gk = [params_values_max[param] for param in gk_params]
low_gk =  [0 for i in gk_params]

clean_arrack_params = [
    "Shots",
    "Crosses",
    "Duels Won",
    "Progressive Runs",
    "Fouls Suffered",
    "Successful Dribbles",
    "Successful Passes",
    "Successful Attacking Actions"
]

clean_defense_params = [ 
    "Fouls",
    "Losses",
    "Duels Won",
    "Recoveries",
    "Clearances",
    "Interceptions",
    "Successful Passes",
    "Successful Defensive Action"
]

clean_gk_params = [
    'Losses',
    'xG saved',
    'Successful Goal Kicks',
    'Exits',
    'Saves',
    'Successful Passes',
    'Successful Defensive Action'
]

attack_radar = Radar(clean_arrack_params, low_att, high_att, round_int=[False]*len(attack_params), num_rings=4, ring_width=1, center_circle_radius=1)
defense_radar = Radar(clean_defense_params, low_def, high_def, round_int=[False]*len(defense_params), num_rings=4, ring_width=1, center_circle_radius=1)
gk_radar = Radar(clean_gk_params, low_gk, high_gk, round_int=[False]*len(gk_params), num_rings=4, ring_width=1, center_circle_radius=1)

############
# Plotting #
############

def radar_mosaic(radar_height=0.915, title_height=0.06, figheight=14):
    figure, axes = plt.subplot_mosaic([['title'], ['radar']], 
                        gridspec_kw={'height_ratios': [title_height, radar_height],
                                     'bottom': 0, 'left': 0, 'top': 1,
                                     'right': 1, 'hspace': 0},
                        figsize=(figheight*radar_height, figheight))

    axes['title'].axis('off')
    return figure, axes

for team in ['Italy', 'Wales']:
    for (player_id, values) in player_stats_avarage[team].items():
        if max(list(values.values())) > 0:
            name = player_names[player_id]
            position = player_position[player_id]

            if position in defense:
                radar = defense_radar

                avg_val = [values[param] for param in defense_params]
                val     = [player_stats[matches['Both'][0]][player_id][param] for param in defense_params]
            elif position in attack:
                radar = attack_radar

                avg_val = [values[param] for param in attack_params]
                val     = [player_stats[matches['Both'][0]][player_id][param] for param in attack_params]
            elif position ==  'Goalkeeper':
                radar = gk_radar

                avg_val = [values[param] for param in gk_params]
                val     = [player_stats[matches['Both'][0]][player_id][param] for param in gk_params]

            fig, axs = radar_mosaic()
            radar.setup_axis(ax=axs['radar'])

            rings_inner = radar.draw_circles(ax=axs['radar'], facecolor='#fff', edgecolor='#b8b8b8')  # draw circles

            radar_output = radar.draw_radar_compare(list(val), list(avg_val), ax=axs['radar'],
                                        kwargs_radar   ={'facecolor': '#3d85c6', 'alpha': 0.6, 'edgecolor': '#073A67', 'linewidth': 2},
                                        kwargs_compare ={'facecolor': '#3eb700', 'alpha': 0.5, 'edgecolor': '#081e00', 'linewidth': 2})
            
            radar_poly, radar_poly2, vertices1, vertices2 = radar_output
            range_labels = radar.draw_range_labels(ax=axs['radar'], fontsize=15, fontproperties=robotto_thin.prop)  # draw the range labels
            param_labels = radar.draw_param_labels(ax=axs['radar'], fontsize=20, fontproperties=robotto_regular.prop) 
            
            title1_text = axs['title'].text(0.5, 0.1, f'{name} - ({team})', fontsize=35, color='#000000',
                                fontproperties=robotto_bold.prop, ha='center', va='center')

            title2_text = axs['title'].text(0.98, 0.5, 'Game Stats', fontsize=25, color='#3d85c6',
                                fontproperties=robotto_bold.prop, ha='right', va='center')

            title3_text = axs['title'].text(0.98, 0.05, 'Tournament Avg', fontsize=25, color='#3eb700',
                                fontproperties=robotto_bold.prop, ha='right', va='center')

            plt.savefig(f'assets/player_stats/{name}-{team}-{position}.png', dpi=300)
            plt.close()

# Verratti Chiesa: (21383, 447804)
# Bastoni Rodon: (405597, 412919)

for player_id1, player_id2 in [(405597, 412919), (21383, 447804)]:
    name1 = player_names[player_id1]
    name2 = player_names[player_id2]
    position = player_position[player_id1]

    if position in defense:
        radar = defense_radar
        val_p1     = [player_stats[matches['Both'][0]][player_id1][param] for param in defense_params]
        val_p2     = [player_stats[matches['Both'][0]][player_id2][param] for param in defense_params]
    elif position in attack:
        radar = attack_radar
        val_p1     = [player_stats[matches['Both'][0]][player_id1][param] for param in attack_params]
        val_p2     = [player_stats[matches['Both'][0]][player_id2][param] for param in attack_params]

    fig, axs = radar_mosaic()
    radar.setup_axis(ax=axs['radar'])

    rings_inner = radar.draw_circles(ax=axs['radar'], facecolor='#fff', edgecolor='#b8b8b8')  # draw circles

    radar_output = radar.draw_radar_compare(list(val_p1), list(val_p2), ax=axs['radar'],
                                kwargs_radar   ={'facecolor': '#3d85c6', 'alpha': 0.5, 'edgecolor': '#073A67', 'linewidth': 3},
                                kwargs_compare ={'facecolor': '#3eb700', 'alpha': 0.5, 'edgecolor': '#081e00', 'linewidth': 3})
            
    radar_poly, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax=axs['radar'], fontsize=15, fontproperties=robotto_thin.prop)  # draw the range labels
    param_labels = radar.draw_param_labels(ax=axs['radar'], fontsize=20, fontproperties=robotto_regular.prop) 
            
    title1_text = axs['title'].text(0.05, 0.1, name1, fontsize=35, color='#3d85c6',
                        fontproperties=robotto_bold.prop, ha='left', va='center')

    title2_text = axs['title'].text(0.95, 0.1, name2, fontsize=35, color='#3eb700',
                        fontproperties=robotto_bold.prop, ha='right', va='center')

    plt.savefig(f'assets/player_stats/{name1}-{name2}.png', dpi=300)
    plt.close()

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.projections import get_projection_class

import numpy as np

import pandas as pd

from passing.utils import read_json, statsbomb_to_point, json_to_normalized_dataframe
from passing.draw_pitch import draw_pitch

lineups_path = "data/statsbomb360/lineups/3788766.json"
events_path = "data/statsbomb360/events/3788766.json"

x_list_433 = [8,  44,32,32,44,   56,66,66,   87,87,100] 
y_list_433 = [45, 10,35,55,80,   45,25,65,   15,75,45]

x_list_3412 = [8,   37, 32, 37,   60, 60, 65, 65,   100, 100, 85]
y_list_3412 = [45,  65, 45, 25,   80, 10, 55, 35,   55, 35, 45]

def plot_passing_sonars(match_id=3788766):
    df_events = json_to_normalized_dataframe(events_path)
    lineups = read_json(lineups_path)

    # Define the home team, away team
    home_team = df_events["team.name"].unique()[0]
    away_team = df_events["team.name"].unique()[1]

    # Plot the passing network for the home team
    plot_passing_sonar(home_team, away_team, match_id, df_events, lineups, x_list_433, y_list_433, True)

    # Plot the passing network for the away team
    plot_passing_sonar(away_team, home_team, match_id, df_events, lineups, x_list_3412, y_list_3412, False)

def plot_passing_sonar(team_name, opponent_name, match_id, df_events, lineups, x_list, y_list, home_team):    
    config = read_json("plot_config.json")
    height = float(config["height"])
    width = float(config["width"])

    ax = draw_pitch()

    team_dict = players_with_coordinates(df_events, x_list=x_list, y_list=y_list, home_team=home_team)
    plot_name = "{0}_{1}_passing_sonar".format(match_id, team_name)

    for player_name, loc in team_dict.items():
        plot_inset(.9, ax, data = Passer(player_name, df_events), x = loc[0], y = loc[1], home_team=home_team)
        
        names_dict = { player["player_name"]: player["player_nickname"] for team in lineups for player in team["lineup"]}
        player_name = names_dict[player_name] if names_dict[player_name] else player_name

        ax.text(loc[0]+6, loc[1], player_name, size = 8,ha='left', va='center', weight='bold', 
            path_effects=[pe.Stroke(linewidth=1.5, foreground='white'), pe.Normal()])

    legend = "Size: length of passes\nColor: % completed passes"
    ax.annotate(legend, xy=(0.01*width, 0.02*height),
                ha="left", va="bottom", zorder=7, fontsize=10, color=config["lines_color"])

    ax.set_title("{0}'s passing sonar against {1}".format(team_name, opponent_name))
    plt.savefig("assets/{0}.png".format(plot_name), facecolor='white', transparent=False)

def players_with_coordinates(df, x_list = [8,44,32,32,44,56,66,66,87,87,100], y_list = [45,10,35,55,80,45,25,65,15,75,45], home_team = True):
    config = read_json("plot_config.json")
    height = float(config["height"])
    width = float(config["width"])
    
    team_dict = {}
    if home_team == True:
        for i in df["tactics.lineup"][0]:
            team_dict[i['player']['name']] = []
    else:
        for i in df["tactics.lineup"][1]:
            team_dict[i['player']['name']] = []

    for x,y,z in zip(x_list, y_list, team_dict):
        x,y = statsbomb_to_point([x,y])
        entry = {z: [x * width, 5 + y * height]}
        team_dict.update(entry)

    return team_dict

def Passer(player, local_df):
    local_df = local_df[local_df["type.name"]=="Pass"]
    local_df = local_df[local_df["player.name"]==player]

    df1 = local_df[['pass.angle','pass.length','pass.outcome.name']].copy()
    bins = np.linspace(-np.pi,np.pi,20)
    df1['binned'] = pd.cut(local_df['pass.angle'], bins, include_lowest=True, right = True)
    df1["Bin_Mids"] = df1["binned"].apply(lambda x: x.mid)
    df1["Complete"] = df1["pass.outcome.name"].apply(lambda x: 1 if pd.isna(x) else 0)
    df1 = df1[:-1]

    A= df1.groupby("Bin_Mids", as_index=False, dropna=False).mean()
    A = A.dropna(axis=0)
    
    return A

def plot_inset(width, axis_main, data, x, y, home_team=True):
    config = read_json("plot_config.json")
    cmap = config["sonar_cmap_home"] if home_team else config["sonar_cmap_away"]

    ax_sub = inset_axes(axis_main, width=width, height=width, loc=10,
                       bbox_to_anchor=(x,y),
                       bbox_transform=axis_main.transData,
                       borderpad=0.0, axes_class=get_projection_class("polar"))

    theta = data["Bin_Mids"]
    radii = data["pass.length"]
    color_metric = data["Complete"]
    bars = ax_sub.bar(theta, radii, width=0.3, bottom=0.0)
    ax_sub.patch.set_alpha(0)
    ax_sub.set_xticklabels([])
    ax_sub.set_yticks([])
    ax_sub.yaxis.grid(False)
    ax_sub.xaxis.grid(False)
    ax_sub.spines['polar'].set_visible(False)

    for r, bar in zip(color_metric, bars):
        bar.set_facecolor(plt.cm.get_cmap(cmap)(r))
        bar.set_alpha(0.8)
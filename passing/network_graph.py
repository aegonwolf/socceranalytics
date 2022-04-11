import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import cm
from matplotlib.colors import Normalize

import pandas as pd

from passing.utils import read_json, json_to_normalized_dataframe, change_range, statsbomb_to_point
from passing.draw_pitch import draw_pitch

lineups_path = "data/statsbomb360/lineups/3788766.json"
events_path = "data/statsbomb360/events/3788766.json"

def plot_passing_networks(match_id=3788766):
    # Read data and normalize events data
    df_events = json_to_normalized_dataframe(events_path).assign(match_id=match_id)

    # Define the home team, away team
    home_team = df_events["team.name"].unique()[0]
    away_team = df_events["team.name"].unique()[1]

    # Plot the passing network for the home team
    plot_passing_network(home_team, away_team, match_id, df_events, True)

    # Plot the passing network for the away team
    plot_passing_network(away_team, home_team, match_id, df_events, False)


def plot_passing_network(team_name, opponent_name, match_id, df_events, home_team):
    lineups = read_json(lineups_path)

    # Create a dictonary with all player name and their nicknames
    names_dict = {player["player_name"]: player["player_nickname"] for team in lineups for player in team["lineup"]}

    # Filter the events dataframe to only include the events for the team
    df_events = df_events[df_events["team.name"] == team_name]

    # Get the minute where the first player is subbed off, either by substitution or by a red card
    first_red_card_minute = df_events[df_events["foul_committed.card.name"].isin(["Second Yellow", "Red Card"])].minute.min()
    first_substitution_minute = df_events[df_events["type.name"] == "Substitution"].minute.min()
    max_minute = df_events.minute.max()

    num_minutes = min(first_substitution_minute, first_red_card_minute, max_minute)

    plot_name = "{0}_{1}_passing_network".format(match_id, team_name)
    plot_title ="{0}'s passing network against {1}".format(team_name, opponent_name)
    plot_legend = "Location: pass origin\nSize: number of passes\nColor: number of passes"

    # Create a dataframe with all the events that are passes that where successful
    df_passes = df_events[(df_events["type.name"] == "Pass") &
                          (df_events["pass.outcome.name"].isna()) &
                          (df_events.minute < num_minutes)].copy()

    # If available, use player's nickname instead of full name to optimize space in plot
    df_passes["pass.recipient.name"] = df_passes["pass.recipient.name"].apply(lambda x: names_dict[x] if names_dict[x] else x)
    df_passes["player.name"] = df_passes["player.name"].apply(lambda x: names_dict[x] if names_dict[x] else x)

    # Calculate average player position
    df_passes["origin.pos.x"] = df_passes.location.apply(lambda x: statsbomb_to_point(x)[0])
    df_passes["origin.pos.y"] = df_passes.location.apply(lambda x: statsbomb_to_point(x)[1])
    player_position = df_passes.groupby("player.name").agg({"origin.pos.x": "median", "origin.pos.y": "median"})

    player_pass_count = df_passes.groupby("player.name").size().to_frame("num.passes")
    player_pass_value = df_passes.groupby("player.name").size().to_frame("pass.value")

    df_passes["pair.key"] = df_passes.apply(lambda x: ".".join(sorted([x["player.name"], x["pass.recipient.name"]])), axis=1)
    pair_pass_count = df_passes.groupby("pair.key").size().to_frame("num.passes")
    pair_pass_value = df_passes.groupby("pair.key").size().to_frame("pass.value")

    ax = draw_pitch()
    ax = draw_pass_map(ax, player_position, player_pass_count, player_pass_value,
              pair_pass_count, pair_pass_value, plot_title, plot_legend, home_team)

    plt.savefig("assets/{0}.png".format(plot_name), facecolor='white', transparent=False)


def draw_pass_map(ax, player_position, player_pass_count, player_pass_value, pair_pass_count, pair_pass_value, title="", legend="", home_team=True):
    """
    Parameters
    -----------
        ax: Matplotlib's axis object, it expects to have the pitch already plotted.
        player_position: pandas DataFrame with player names as index and columns 'origin_pos_x' and 'origin_pos_y' in 0-1 range.
        player_pass_count: pandas DataFrame with player names as index and a column 'num_passes'.
        player_pass_value: pandas DataFrame with player names as index and a column 'pass_value'.
        pair_pass_count: pandas DataFrame with 'player1_player2' as index and a column 'num_passes'.
        pair_pass_value: pandas DataFrame with 'player1_player2' as index and a column 'pass_value'.
        title: text that will be shown above the pitch.
        legend: text that will be shown in the bottom-left corner of the pitch.
        home_team: boolean, True if the team is the home team, False if the team is the away team.
    Returns
    -----------
       ax : Matplotlib's axis object to keep adding elements on the pitch.
    """

    config = read_json("plot_config.json")
    height = float(config["height"])
    width = float(config["width"])

    background_color = config["background_color"]
    nodes_cmap = config["nodes_cmap_home"] if home_team else config["nodes_cmap_away"]

    player_position["origin.pos.y"] = player_position["origin.pos.y"]*height
    player_position["origin.pos.x"] = player_position["origin.pos.x"]*width

    # This allows to fix the range of sizes and color scales so that two plots from different teams are comparable.
    max_player_count = player_pass_count["num.passes"].max()
    max_player_value = player_pass_value["pass.value"].max()
    max_pair_count = pair_pass_count["num.passes"].max()
    max_pair_value = pair_pass_value["pass.value"].max()

    # Step 1: plot edges
    if config["plot_edges"]:
        # Combine num_passes and pass_value columns into one DataFrame
        pair_stats = pd.merge(pair_pass_count, pair_pass_value, left_index=True, right_index=True)
        for pair_key, row in pair_stats.iterrows():
            player1, player2 = pair_key.split(".")

            player1_x = player_position.loc[player1]["origin.pos.x"]
            player1_y = player_position.loc[player1]["origin.pos.y"]

            player2_x = player_position.loc[player2]["origin.pos.x"]
            player2_y = player_position.loc[player2]["origin.pos.y"]

            num_passes = row["num.passes"]
            pass_value = row["pass.value"]

            line_width = change_range(num_passes, (0, max_pair_count), (config["min_edge_width"], config["max_edge_width"]))
            norm = Normalize(vmin=0, vmax=max_pair_value)
            edge_cmap = cm.get_cmap(nodes_cmap)
            edge_color = edge_cmap(norm(pass_value))

            ax.plot([player1_x, player2_x], [player1_y, player2_y], linestyle='-', 
                    alpha=1, lw=line_width, zorder=3, color=edge_color)

    # Step 2: plot nodes
    # Combine num_passes and pass_value columns into one DataFrame
    player_stats = pd.merge(player_pass_count, player_pass_value, left_index=True, right_index=True)
    for player_name, row in player_stats.iterrows():
        player_x = player_position.loc[player_name]["origin.pos.x"]
        player_y = player_position.loc[player_name]["origin.pos.y"]

        num_passes = row["num.passes"]
        pass_value = row["pass.value"]

        marker_size = change_range(num_passes, (0, max_player_count), (config["min_node_size"], config["max_node_size"]))
        norm = Normalize(vmin=0, vmax=max_player_value)
        node_cmap = cm.get_cmap(nodes_cmap)
        node_color = node_cmap(norm(pass_value))

        ax.plot(player_x, player_y, '.', color=node_color, markersize=marker_size, zorder=5)
        ax.plot(player_x, player_y, '.', color=background_color, markersize=marker_size-20, zorder=6)
        ax.annotate(player_name, xy=(player_x, player_y), ha="center", va="center", zorder=7,
                    fontsize=config["font_size"], color=config["font_color"], weight='bold',
                    path_effects=[pe.withStroke(linewidth=2, foreground=background_color)])

    # Step 3: Extra information shown on the plot
    if legend:
        ax.annotate(legend, xy=(0.01*width, 0.02*height),
                    ha="left", va="bottom", zorder=7, fontsize=10, color=config["lines_color"])

    if title:
        ax.set_title(title)

    return ax
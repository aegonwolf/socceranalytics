import matplotlib.pyplot as plt
import json
import zipfile
import argparse

def xGPlot(eventsFilePath):
    with open(eventsFilePath) as f:   
        data = json.load(f)

    events = data["events"]

    team_current_score = {}

    team_shot_x_points = {}
    team_shot_y_points = {}

    team_goal_x_points = {}
    team_goal_y_points = {}

    team_meta = {}

    end = 0

    for event in events:
        end = event["minute"]

        if event["type"]["primary"] != "shot":
            continue
        team_id = event["team"]["id"]
        team_meta[team_id] = event["team"]
        shot = event["shot"]
        old_score = team_current_score.get(team_id, 0)

        team_shot_x_points.setdefault(team_id, []).append(event["minute"])
        team_shot_y_points.setdefault(team_id, []).append(old_score)

        # Increment score
        xg = shot["xg"]
        team_current_score[team_id] = old_score + xg

        team_shot_x_points.setdefault(team_id, []).append(event["minute"])
        team_shot_y_points.setdefault(team_id, []).append(old_score + xg)

        if shot["isGoal"]:
            team_goal_x_points.setdefault(team_id, []).append(event["minute"])
            team_goal_y_points.setdefault(team_id, []).append(old_score + xg)


    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
    ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
    ax.minorticks_on()
    ax.tick_params(which='minor', bottom=False, left=False)

    for team, points in team_shot_x_points.items():
        meta = team_meta[team]
        end_score = team_current_score[team]

        color = "blue" if meta["name"] == "Italy" else "red"
        ax.plot(
            [0] + points + [end],
            [0] + team_shot_y_points.get(team, []) + [end_score],
            color=color,
            label=meta["name"],
        )

        if team in team_goal_x_points:
            ax.scatter(
                team_goal_x_points[team],
                team_goal_y_points[team],
                color=color,
                marker="o",
            )

    ax.set_title("xGoals", fontsize=16, fontweight="semibold")
    ax.set_ylabel("Cumulative Expected Goals", fontsize=12, fontweight="light")
    ax.set_xlabel("Minute", fontsize=12, fontweight="light")
    ax.set_xlim(0, end)
    ax.set_xticks(range(0, end + 1, 10))
    ax.legend()

    fig.savefig("xG-Graph")

xGPlot("data/wyscout/5034296/5034296_events.json")
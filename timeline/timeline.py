import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from parse_statsbomb import extract_events

PATH = 'data/statsbomb360/events/3788766.json'


def get_events_of_team(event_list: list, team: str):
    team_events = list(filter(lambda e: e["team"] == team, event_list))

    team_labels = list(map(lambda te: "{:02d}:{:02d}\n{}".format(te["minute"], te["second"], te["text"]), team_events))
    team_minutes = list(map(lambda te: te["minute"], team_events))

    return team_labels, team_minutes


def plot_team_labels(ax, team_labels, team_minutes, even_offset, odd_offset, text_color):
    team_label_offsets = np.zeros(len(team_labels))
    team_label_offsets[::2] = even_offset
    team_label_offsets[1::2] = odd_offset
    for i, (l, d) in enumerate(zip(team_labels, team_minutes)):
        t = ax.text(d, team_label_offsets[i], l, ha='center', fontfamily='sans serif', fontweight='bold',
                    color=text_color,
                    fontsize=12)
        t.set_bbox(dict(facecolor="white", edgecolor="white", alpha=0.8))


def plot_stems(ax, team_minutes, even_hight, odd_height, team_color):
    team_stems = np.zeros(len(team_minutes))
    team_stems[::2] = even_hight
    team_stems[1::2] = odd_height
    markerline, stemline, baseline = ax.stem(team_minutes, team_stems, use_line_collection=True)
    _ = plt.setp(baseline, color="black")
    _ = plt.setp(markerline, marker=',', color=team_color)
    _ = plt.setp(stemline, color=team_color)


def draw_goals(axis, goal_minute_list):
    axis.scatter(goal_minute_list, np.zeros(len(goal_minute_list)), s=140, color="black", marker="o", zorder=10)
    axis.scatter(goal_minute_list, np.zeros(len(goal_minute_list)), s=120, color="white", marker="o", zorder=11)
    axis.scatter(goal_minute_list, np.zeros(len(goal_minute_list)), s=20, color="black", marker="p", zorder=13)
    axis.scatter(goal_minute_list, np.zeros(len(goal_minute_list)), s=140, color="black", marker="2", zorder=12)

with open(PATH, "r") as statsbomb_file:
    df = pd.json_normalize(json.load(statsbomb_file))

events, teams, halves = extract_events(df)

with open("timeline/plot_style.json") as plot_style_file:
    plot_style = json.load(plot_style_file)

# https://dadoverflow.com/2021/08/17/making-timelines-with-python/
team_zero_labels, team_zero_minutes = get_events_of_team(events, teams[0])
team_one_labels, team_one_minutes = get_events_of_team(events, teams[1])

halve_ends = np.unique(halves["minute"].tolist())
halve_labels = list(map(lambda p: "{}. End".format(p), np.unique(halves["period"].tolist())))
goal_minutes = list(
    map(lambda e: e["minute"], filter(lambda e: e["type"] == "Goal" or e["type"] == "Own Goal", events)))
substitution_minutes = list(map(lambda e: e["minute"], filter(lambda e: e["type"] == "Substitution", events)))
yellow_card_minutes = list(map(lambda e: e["minute"], filter(lambda e: e["type"] == "Yellow Card", events)))
red_card_minutes = list(map(lambda e: e["minute"], filter(lambda e: e["type"] == "Red Card", events)))

fig, ax = plt.subplots(figsize=(16, 4), constrained_layout=True)
_ = ax.set_ylim(-2, 1.75)
_ = ax.set_xlim(0, max(halve_ends))
_ = ax.axhline(0, xmin=0, xmax=max(halve_ends), c='black', zorder=1)

start_text = ax.text(0, -0.04, "1. Start", ha="center", color=plot_style.get("text_color", "black"),
                     fontfamily="sans serif", fontweight="bold",
                     fontsize=10)
start_text.set_bbox(dict(facecolor="white", edgecolor="white"))
for m, l in zip(halve_ends, halve_labels):
    t = ax.text(m, -0.04, l, ha="center", color=plot_style.get("text_color", "black"), fontfamily="sans serif",
                fontweight="bold", fontsize=10)
    t.set_bbox(dict(facecolor="white", edgecolor="white"))

draw_goals(ax, goal_minutes)
_ = ax.scatter(substitution_minutes, [0.01 for i in range(len(substitution_minutes))], s=120, color="green", marker=10,
               zorder=10)
_ = ax.scatter(substitution_minutes, [-0.01 for i in range(len(substitution_minutes))], s=120, color="red", marker=11,
               zorder=10)
_ = ax.scatter(yellow_card_minutes, np.zeros(len(yellow_card_minutes)), s=120, color="gold", marker="s", zorder=10)
_ = ax.scatter(red_card_minutes, np.zeros(len(red_card_minutes)), s=120, color="red", marker="s", zorder=10)

ax.set_title('{} v {}: Euro 2020'.format(teams[0], teams[1]), fontweight="bold", fontfamily='sans serif',
             fontsize=plot_style.get("header", {}).get("size", 20),
             color=plot_style.get("header", {}).get("color", "black"))

ax.text(-5, 0.4, teams[0], ha="left", fontfamily="sans serif", fontweight="bold",
        fontsize=plot_style.get("team_title", {}).get("size", 16),
        color=plot_style.get("header", {}).get("color", "black"))
ax.text(-5, -0.4, teams[1], ha="left", fontfamily="sans serif", fontweight="bold",
        fontsize=plot_style.get("team_title", {}).get("size", 16),
        color=plot_style.get("header", {}).get("color", "black"))

plot_stems(ax, team_zero_minutes, 0.3, 1.2, plot_style.get("team_colors").get(teams[0]))
plot_stems(ax, team_one_minutes, -0.3, -1.2, plot_style.get("team_colors").get(teams[1]))

plot_team_labels(ax, team_zero_labels, team_zero_minutes, 0.35, 1.3, plot_style.get("text_color", "black"))
plot_team_labels(ax, team_one_labels, team_one_minutes, -0.9, -1.8, plot_style.get("text_color", "black"))

# hide lines around chart
for spine in ["left", "top", "right", "bottom"]:
    _ = ax.spines[spine].set_visible(False)

# hide tick labels
ax.set_xticks([])
ax.set_yticks([])

plt.savefig("assets/timeline.png", dpi=300)

from mplsoccer import Pitch, VerticalPitch
import matplotlib.pyplot as plt
import json
import numpy as np

PATH = 'data/wyscout/5034296/5034296_events.json'
TEAM = 'Wales'

with open(PATH, 'r') as jfile:
    data = json.load(jfile)

def get_locations(type, team):
    start_locations_accurate = []
    end_locations_accurate = []
    start_locations_notaccurate = []
    end_locations_notaccurate = []
    start_goal = []
    end_goal = []
    for event in data['events']:
        event_type = event['type']['primary']

        if event_type == type and event['team']['name'] == team:
            location1 = event['location']
            
            try:
                location2 = event['pass']['endLocation']
                accurate = event['pass']['accurate']
            except:
                location2 = event['possession']['endLocation']
                accurate = True

            if event['possession'] is not None and event['possession']['attack'] is not None and event['possession']['attack']['withGoal']:
                start_goal.append([location1['x'], location1['y']])
                end_goal.append([location2['x'], location2['y']])

                print("{} --> Goal: {} ".format(type, event['possession']['attack']['withGoal']))
                continue

            if accurate:
                start_locations_accurate.append([location1['x'], location1['y']])
                end_locations_accurate.append([location2['x'], location2['y']])
            else:
                start_locations_notaccurate.append([location1['x'], location1['y']])
                end_locations_notaccurate.append([location2['x'], location2['y']])

    return np.array(start_locations_accurate), np.array(end_locations_accurate), \
           np.array(start_locations_notaccurate), np.array(end_locations_notaccurate), np.array(start_goal), np.array(end_goal)


def drawarrows(pitch, ax, locations, color_accurate, color_notaccurate, color_goal):
    start_accurate, end_accurate, start_notaccurate, end_notaccurate, start_goal, end_goal = locations
    if start_accurate.size != 0:
        sc_accurate = pitch.arrows(start_accurate[:, 0], start_accurate[:, 1], end_accurate[:, 0], end_accurate[:, 1],
                               width=1.5, headwidth=4, headlength=6, ax=ax, color=color_accurate)
    if start_notaccurate.size != 0:
        sc_notaccurate = pitch.arrows(start_notaccurate[:, 0], start_notaccurate[:, 1],
                                  end_notaccurate[:, 0], end_notaccurate[:, 1],
                                  width=1.5, headwidth=4, headlength=6, ax=ax, color=color_notaccurate)
    if start_goal.size != 0:
        sc_notaccurate = pitch.arrows(start_goal[:, 0], start_goal[:, 1],
                                  end_goal[:, 0], end_goal[:, 1],
                                  width=1.5, headwidth=4, headlength=6, ax=ax, color=color_goal)

#penalty_start, penalty_end = get_locations("penalty", "Belgium")
pitch = Pitch(pitch_type='wyscout')
fig, ax = pitch.draw()


# add title
fig.text(
    0.99, 0.010, "Corners in green\nFree kicks in red\nThrow ins in blue\nGoal Kick in orange", size=9, color="#000000",
    ha="right"
)

ax.set_title(f'{TEAM} Set Pieces', fontsize=16)

drawarrows(pitch, ax, get_locations("corner", TEAM), "green", "lightgreen", "black")
drawarrows(pitch, ax, get_locations("throw_in", TEAM), "blue", "lightblue", "black")
drawarrows(pitch, ax, get_locations("free_kick", TEAM), "red", "lightcoral", "black")
drawarrows(pitch, ax, get_locations("goal_kick", TEAM), "goldenrod", "moccasin", "black")

plt.savefig(f'assets/{TEAM}_set_pieces.png')

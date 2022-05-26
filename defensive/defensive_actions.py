import pandas as pd
import json
from mplsoccer.pitch import Pitch, VerticalPitch
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt

# Read in data
pd.set_option("display.max_rows", 50)
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", None)

###### PASTE HERE THE CSV FOR STATSBOMB EVENTS
with open("data/statsbomb360/events/3788766.json", 'r', encoding="UTF-8") as f:
    obj = json.loads(f.read())
    df = pd.json_normalize(obj, sep='_')

path_eff = [path_effects.Stroke(linewidth=3, foreground='black'), path_effects.Normal()]

def_action = ["Pressure", "Duel", "Ball Recovery", "Clearance", "Interception", "Block"]
df = df[df.type_name.isin(def_action)]

df['x']=df.location.apply(lambda x: x[0])
df['y']=df.location.apply(lambda x: x[1])

# Defensive plot for team
team = "Wales"
cmap = 'Reds'

df_home = df[(df.team_name == team)].reset_index()

pitch = VerticalPitch(pitch_type='statsbomb', line_zorder=2, pitch_color='#FFFFFF')
fig, ax = pitch.draw(figsize=(8, 11))
fig.set_facecolor('#FFFFFF')

bin_statistic = pitch.bin_statistic_positional(df_home.x, df_home.y, statistic='count', positional='full', normalize=True)

pitch.heatmap_positional(bin_statistic, ax=ax, cmap=cmap, edgecolors='#22312b')
pitch.scatter(df_home.x, df_home.y, c='white', s=2, ax=ax)
pitch.lines(df_home.x.mean(), 80, df_home.x.mean(), 0 , color="grey", ax=ax, lw=5, linestyle="-.")

labels = pitch.label_heatmap(bin_statistic, color='#f4edf0', fontsize=18, ax=ax, ha='center', va='center', str_format='{:.0%}', path_effects=path_eff)

ax.set_title('Defensive Actions for ' + team, fontsize=20)

plt.savefig('assets/defensive_actions_' + team + '.png', dpi=300)
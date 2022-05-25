import pandas as pd
import json
import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np

PATH = 'data/wyscout/5034296/5034296_events.json'
TEAM = 'Italy'

with open(PATH, 'r') as jfile:
    data = json.load(jfile)

def get_times(team, etype):
    minutes =[]
    interruption_time = []
    types = []
    for event in data['events']:
        event_type = event['type']['primary']
        if event_type in etype:
            time_interruption = last_event['matchTimestamp']
            time_restart = event['matchTimestamp']
            from datetime import datetime, timedelta

            time1 = datetime.strptime(time_interruption, "%H:%M:%S.%f")
            time2 = datetime.strptime(time_restart, "%H:%M:%S.%f")
            time = (time1.time().second + time1.time().minute*60.0 + time1.time().hour *60*60)/60.0

            if event['team']['name'] == team:
                interruption_time.append((time2-time1).total_seconds())
                minutes.append(time)
                types.append(event_type)

        last_event = event
        
    return list(zip(minutes, interruption_time, types))


setpieces_df = pd.DataFrame(get_times(TEAM,["throw_in", "free_kick", "corner", "goal_kick"]),
                            columns=['Minute', 'Interruption in seconds', 'Type'])

sns.set_theme(style="dark", font_scale=2, color_codes=True)
ax = sns.lineplot(x="Minute", y="Interruption in seconds", hue='Type', data=setpieces_df, legend='full')

plt.setp(ax.get_legend().get_texts(), fontsize='14')
plt.savefig(f'assets/interruption_time_{TEAM}.png', bbox_inches='tight')
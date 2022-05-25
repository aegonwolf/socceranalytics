from cmath import exp
import json
import pandas as pd
from datetime import time

def json_to_normalized_dataframe(path):
    rd = ""
    with open(path, 'r') as f:
        rd = f.read()
    obj = json.loads(rd)
    df = pd.json_normalize(obj)

    return df
    
df = json_to_normalized_dataframe("data/statsbomb360/events/3788766.json")
match_id = "3788766"
teams = [df["team.name"][0],df["team.name"][1]]

get_s = lambda t_obj:  t_obj.hour*3600 + t_obj.minute*60 + t_obj.second +t_obj.microsecond/1_000_000

halves = df[(df["type.name"]=="Half End")]
durs = []
t=0
for i, r in halves.iterrows():
	if t!=get_s(time.fromisoformat(r["timestamp"])):
		t=get_s(time.fromisoformat(r["timestamp"]))
		durs.append(t)

subs = df["type.name"]=="Substitution"
own_goal = df["type.name"]=="Own Goal Against"
goal = (df["type.name"]=="Shot") & (df["shot.outcome.name"] == "Goal")
assist = (df["type.name"]=="Pass") & (df["pass.goal_assist"]==True)
card =  (df["type.name"]=="Bad Behaviour") |((~df["foul_committed.card.name"].isna()) & (df["type.name"]=="Foul Committed"))
df = df[(subs) | (goal) | (own_goal) | (assist) | (card)]

periods=["1st","2nd","3rd","4th"]
period=""
p = 0

events = []
t=0
assist=""
v=0

for i, r in df.iterrows():
	timestamp = time.fromisoformat(r["timestamp"])
	time_s = get_s(timestamp)
	for per in range(r["period"]-1):
		time_s+=durs[per]+9
	if r["period"]>p or t!=r["minute"]:
		t=r["minute"]
		t_str = str(t)+"'"
		if r["period"]>p:
			p=r["period"]
			events.append([periods[p-1],t_str,"",""])
		else:
			events.append(["",t_str,"",""])
	
	t_index = 0 if r["team.name"]==teams[0] else 1
	def write(s,t_i=t_index):
		t_i+=2
		if events[-1][t_i]=="":
			events[-1][t_i]=s
		else:
			events[-1][t_i]+="<br>"+s

	# def video(t_i=t_index):
	# 	global v
	# 	path="test/video_{}.mp4".format(v)
	# 	write("![Video {}]({})".format(v,path),t_i)
	# 	query = "{} {} {}".format(match_id,time_s+5, path)
	# 	!python eventvideo/eventvideo.py -s $query
	# 	v+=1
		
	if r["type.name"]=="Shot":
		if r["shot.outcome.name"]=="Goal":
			scorer = r["player.name"]
			if r["shot.type.name"]=="Penalty":
				scorer+=" (P)"
			write("⚽ {} {}".format(scorer,assist))
			# video()
		assist=""
	elif r["type.name"]=="Pass":
		if r["pass.goal_assist"]==True:
			assist="({})".format(r["player.name"])
	elif r["type.name"]=="Substitution":
		write("⬇️{} <br>⬆️{}".format(r["player.name"],r["substitution.replacement.name"]))
		period=""
	elif r["type.name"]=="Own Goal Against":
		t_i=(t_index+1)%2
		write("⚽ {} (OG)".format(r["player.name"]),t_i)
		# video(t_i)
	elif r["type.name"]=="Bad Behaviour" or r["type.name"]=="Foul Committed":

		try:
			card = r["bad_behaviour.card.name"]
		except:
			card = r["foul_committed.card.name"]

		if card == "Yellow Card":
			write("🟨 {}".format(r["player.name"]))
		elif card == "Second Yellow":
			write("🟨🟥 {}".format(r["player.name"]))
			# video()
		elif card == "Red Card":
			write("🟥 {}".format(r["player.name"]))
			# video()

print("|Period|Time|{}|{}|".format(teams[0],teams[1]))
print("|---|---|---|---|")
for e in events:
	print("|"+"|".join(e)+"|")

print("""
<details><summary>Legend</summary>
⚽ Goal (P=penalty) (OG=own goal) (assist)

🔻 Player out<br>
🔺 Player in<br>
🟨 Yellow card<br>
🟨🟥 Second yellow card<br>
🟥 Red card
</details>
""")


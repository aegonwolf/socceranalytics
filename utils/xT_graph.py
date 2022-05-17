import socceraction.spadl as spadl
import socceraction.xthreat as xthreat

from socceraction.data.statsbomb import StatsBombLoader

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

def xTvalue(pathtodata, matchid, home_team_id, xTModel):
    """
    Imports statsbomb event data and rates all actions according to the given xTModel.
    Returns the rated event data as a pandas DataFrame.
    """

    #Load Statsbomb data
    SBL = StatsBombLoader(getter="local", root=pathtodata)
    df_events = SBL.events(game_id=matchid)

    #convert the events into SPADL format used in the socceraction package
    df_actions = spadl.statsbomb.convert_to_actions(df_events, home_team_id=home_team_id)
    #add metadata for the players
    df_actions = (spadl.add_names(df_actions).merge(SBL.teams(game_id=matchid)).merge(SBL.players(game_id=matchid)))
    #invert coordinates so that the direction of plays matches the scoring potential
    df_actions = spadl.play_left_to_right(df_actions, home_team_id)

    #calculated change in xT
    df_actions["xT_value"] = xTModel.rate(df_actions) #without interpolation
    df_actions["xT_value_interpolated"] = xTModel.rate(df_actions, use_interpolation=True) #with interpolation
    return df_actions

def accumulated_xT(df_actions):
    """
    Calculates the accumulated creation of xT for each individual player.
    The accumalted is returned as an pandas DataFrame including some metadata.
    """

    data = {"xT_value":[], "xT_value_interpolated":[]}
    metadata = {"team_name":[], "player_name":[], "jersey_number": [],
                "is_starter": [], "starting_position_name": [], "minutes_played": []}

    for player, group in df_actions.groupby("player_name"):
        for k in data.keys():
            #sum all up all events
            s = 0
            for xT in group[k]:
                s += max(0, xT)
            data[k].append(s)
        for k in metadata.keys():
            metadata[k].append(np.array(group[k])[0])

    xTplayers = pd.DataFrame(metadata)
    xTplayers["total_xT"] = data["xT_value"]
    xTplayers["total_xT_interpolated"] = data["xT_value_interpolated"]

    #Normalize values to 90 minutes of play.
    xTplayers["total_xT_normalized"] = xTplayers["total_xT"]/xTplayers["minutes_played"]*90
    xTplayers["total_xT_normalized_interpolated"] = xTplayers["total_xT_interpolated"]/xTplayers["minutes_played"]*90
    xTplayers = xTplayers.round(2)
    return xTplayers

#Implement actions as Dataframes
def momentum(actions, home_id, away_id):
    #find the index and the second, where the actions change period into halftime 2
    ht_durations = np.array(actions.groupby("period_id").max()["time_seconds"])
    times = np.zeros(len(ht_durations)+1)
    for i in range(1,len(times)):
        times[i] = ht_durations[i-1]+times[i-1]

    total_time = np.sum(ht_durations)
    time = np.arange(1, total_time+1)
    acc_home = np.zeros_like(time)
    acc_away = np.zeros_like(time)
    print(ht_durations, times)
    for index, xT in actions.iterrows():
        if xT['xT_value_interpolated'] > 0:
            ind = int(xT['time_seconds']) + int(times[int(xT["period_id"])-1])-1
            if xT['team_id']==home_id:
                acc_home[ind] += xT['xT_value_interpolated']
            else:
                acc_away[ind] += xT['xT_value_interpolated']
    return time, np.cumsum(acc_home), np.cumsum(acc_away), times

def plot_momentum_chart(t, home, away, ht, twin, goalshome=[], goalsaway=[], pathtoicon=None, hometeam="", awayteam=""):
    arr_image = plt.imread(pathtoicon)

    ts =0.5*(t[::twin][1:]+t[::twin][:-1])
    home_avg = np.diff(home[::twin])
    away_avg = np.diff(away[::twin])
    maxdiff = np.max(np.abs(home_avg-away_avg))

    f, ax = plt.subplots(1, 1, figsize=(12, 5))

    limfact = 1.3
    htmargin = 100

    def converttime(t):
        if t <= 45:
            return t*60
        elif t <= 90:
            return (t-45)*60 +ht[1] +htmargin
        elif t <= 105:
            return (t-90)*60 +ht[2] +htmargin*2
        else:
            return (t-105)*60 +ht[3] +htmargin*3

    ballwidth = 150
    ballheight = 0.2
    linefact = 0.92
    lineheight = linefact*maxdiff*limfact

    for g in goalshome:
        ax.plot(np.ones(2)*converttime(g), [0.001, lineheight*0.9], color="black", zorder=-5)
        axin = ax.inset_axes([converttime(g)-ballwidth*0.5, lineheight-ballheight*0.5, ballwidth, ballheight], transform=ax.transData)    # create new inset axes in data coordinates
        axin.imshow(arr_image)
        axin.axis('off')

    for g in goalsaway:
        ax.plot(np.ones(2)*converttime(g), [-lineheight, -0.01], color="black", zorder=-5)
        axin = ax.inset_axes([converttime(g)-ballwidth*0.5,-lineheight-ballheight*0.5,ballwidth,ballheight],transform=ax.transData)    # create new inset axes in data coordinates
        axin.imshow(arr_image)
        axin.axis('off')

    for i, h in enumerate(ht[1:]):
        A = np.logical_and(t<h, t > ht[i])
        ttmp = t[A]
        hometmp = home[A]
        awaytmp = away[A]
        ts =0.5*(ttmp[::twin][1:]+ttmp[::twin][:-1])
        diff = np.diff(hometmp[::twin])-np.diff(awaytmp[::twin])
        A = diff > 0
        ax.bar(ts[A]+htmargin*i, diff[A], width=twin*0.9, color="blue")
        ax.bar(ts[~A]+htmargin*i, diff[~A], width=twin*0.9, color="red")

        tover = int(h-ht[i]) % twin
        diffover = (home[int(h)-1]-home[int(h)-tover-1]-(away[int(h)-1]-away[int(h)-tover-1]))*twin/tover
        if tover > 0.0*twin:
            if diffover > 0:
                ax.bar(np.max(ts)+(tover+twin)*0.5+htmargin*i, diffover, width=tover*0.9, color="blue")
            else:
                ax.bar(np.max(ts)+(tover+twin)*0.5+htmargin*i, diffover, width=tover*0.9, color="red")
    ax.set_ylim([-maxdiff*limfact, maxdiff*limfact])
    ax.set_xlim([0, np.max(ts)+len(ht)*htmargin])
    ax.text(0.38, 1.05, "Momentum chart:", ha="center", va="bottom",color="black",transform=ax.transAxes, fontsize=20)
    ax.text(0.55, 1.05, hometeam, ha="center", va="bottom",color="blue", transform=ax.transAxes, fontsize=20)
    ax.text(0.58, 1.05, "-", ha="center", va="bottom",color="black",transform=ax.transAxes, fontsize=20)
    ax.text(0.615, 1.05, awayteam, ha="center", va="bottom",color="red",transform=ax.transAxes, fontsize=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_ylabel("Differential Created Threat", fontsize=14)
    ax.set_xlabel("Minutes played", fontsize=14)
    ticks = np.arange(1, 10)*10
    if len(ht) > 3:
        ticks = np.concatenate((ticks, np.array([95, 105, 110, 120])))
    ax.set_xticks([converttime(x) for x in ticks], [str(x) for x in ticks])
    ax.plot(np.ones(2)*(ht[1]+htmargin*0.5), [-maxdiff*limfact, maxdiff*limfact], color="gray", linestyle="--")
    ax.plot(np.ones(2)*(ht[2]+htmargin*1.5), [-maxdiff*limfact, maxdiff*limfact], color="gray", linestyle="--")
    if len(ht) > 3:
        ax.plot(np.ones(2)*(ht[3]+htmargin*2.5), [-maxdiff*limfact, maxdiff*limfact], color="gray", linestyle="--")
    return f




#Load the xT model
xTfile = "open_xt_12x8_v1.json" #Premier league 17/18 season symmetrized https://mobile.twitter.com/karun1710/status/1156196523765633024
xTModel = xthreat.load_model(xTfile)

matchid = 3788766 #Your match id
home_team = 914 #Home team id
away_team = 907 #Away team id
statsbombfile = "data/statsbomb360" #path to statsbomb

actions = xTvalue(statsbombfile, matchid, home_team, xTModel)
t, home, away, ht = momentum(actions, home_team, away_team)

#Lists of times when goals were scored
goalshome = [39] 
goalsaway = []
icon_path = 'assets/football_icon.png' #add path to an picture of football icon
twin = int(3*60) #Width of the bars in seconds
f = plot_momentum_chart(t, home, away, ht, twin, goalshome, goalsaway, pathtoicon=icon_path, hometeam="Ita", awayteam="Wal")

f.savefig("assets/momentum_chart.png")

from datetime import time

from pandas import DataFrame
from pandas import Series


# Adapted from Snippet $441
# https://gitlab.ethz.ch/socceranalytics/uefa-euro-2020/-/snippets/441


def create_default_boolean_series(length: int):
    return Series(False, index=range(length))


def is_card(card_series: Series, card_string: str):
    try:
        is_bad_behaviour_card = card_series["bad_behaviour.card.name"] == card_string
    except KeyError:
        is_bad_behaviour_card = False
    try:
        is_foul_committed_card = card_series["foul_committed.card.name"] == card_string
    except KeyError:
        is_foul_committed_card = False

    return is_bad_behaviour_card or is_foul_committed_card


def get_seconds(t_obj):
    return t_obj.hour * 3600 + t_obj.minute * 60 + t_obj.second + t_obj.microsecond / 1_000_000


def extract_events(df: DataFrame):
    teams = [df["team.name"][0], df["team.name"][1]]

    halves = df[(df["type.name"] == "Half End")]

    try:
        subs = df["type.name"] == "Substitution"
    except KeyError:
        subs = create_default_boolean_series(len(df.index))
        print("KeyError for Substitution")

    try:
        own_goal = df["type.name"] == "Own Goal Against"
    except KeyError:
        own_goal = create_default_boolean_series(len(df.index))
        print("KeyError for Own Goal")

    try:
        goal = (df["type.name"] == "Shot") & (df["shot.outcome.name"] == "Goal")
    except KeyError:
        goal = create_default_boolean_series(len(df.index))
        print("KeyError for Goal")

    try:
        assist = (df["type.name"] == "Pass") & (df["pass.goal_assist"])
    except KeyError:
        assist = create_default_boolean_series(len(df.index))
        print("KeyError for Assist")

    try:
        card = (df["type.name"] == "Bad Behaviour") | (
                (~df["foul_committed.card.name"].isna()) & (df["type.name"] == "Foul Committed"))
    except KeyError:
        card = create_default_boolean_series(len(df.index))
        print("KeyError for Card")

    df = df[subs | goal | assist | own_goal | card]

    events = []
    assist = ""
    durs = []
    t = 0

    for i, r in halves.iterrows():
        if t != get_seconds(time.fromisoformat(r["timestamp"])):
            t = get_seconds(time.fromisoformat(r["timestamp"]))
            durs.append(t)

    for i, r in df.iterrows():
        timestamp = time.fromisoformat(r["timestamp"])
        time_s = get_seconds(timestamp)
        for per in range(r["period"] - 1):
            time_s += durs[per] + 9

        if r["type.name"] == "Shot":
            if r["shot.outcome.name"] == "Goal":
                scorer = r["player.name"]
                if r["shot.type.name"] == "Penalty":
                    scorer += " (P)"
                events.append({
                    "type": "Goal",
                    "minute": r["minute"],
                    "second": r["second"],
                    "team": r["team.name"],
                    "text": "(G) {} {}".format(scorer, assist)
                })
            assist = ""
        elif r["type.name"] == "Pass":
            if r["pass.goal_assist"]:
                assist = "({})".format(r["player.name"])
        elif r["type.name"] == "Substitution":
            events.append({
                "type": "Substitution",
                "minute": r["minute"],
                "second": r["second"],
                "team": r["team.name"],
                "text": "Out: {} \n In: {}".format(r["player.name"], r["substitution.replacement.name"])
            })
        elif r["type.name"] == "Own Goal Against":
            events.append({
                "type": "Own Goal",
                "minute": r["minute"],
                "second": r["second"],
                "team": r["team.name"],
                "text": "(OG) {}".format(r["player.name"])
            })
        elif r["type.name"] == "Bad Behaviour" or r["type.name"] == "Foul Committed":
            card_event = {
                "minute": r["minute"],
                "second": r["second"],
                "team": r["team.name"],
            }
            if is_card(r, "Yellow Card"):
                card_event["type"] = "Yellow Card"
                card_event["text"] = "(Y) {}".format(r["player.name"])
            elif is_card(r, "Second Yellow"):
                card_event["type"] = "Red Card"
                card_event["text"] = "(YR) {}".format(r["player.name"])
            elif is_card(r, "Red Card"):
                card_event["type"] = "Red Card"
                card_event["text"] = "(R) {}".format(r["player.name"])

            events.append(card_event)

    return events, teams, halves

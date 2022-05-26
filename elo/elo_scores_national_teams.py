###############################################################################
# IMPORTS
###############################################################################
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Source: https://medium.com/mlearning-ai/how-to-calculate-elo-score-for-international-teams-using-python-66c136f01048


###############################################################################
# FUNCTIONS
###############################################################################

confederation_tournaments=[ 'AFC Asian Cup',
                            'African Cup of Nations',
                            'UEFA Euro',
                            'Copa América',
                            'CONCACAF Championship',
                            'Oceania Nations Cup']

confed_tournaments_qual = [ 'AFC Asian Cup qualification',
                            'African Cup of Nations qualification',
                            'UEFA Euro qualification',
                            'Copa América qualification',
                            'CONCACAF Championship qualification',
                            'Oceania Nations Cup qualification']

def expected_result(loc,aw):
  dr=loc-aw
  we=(1/(10**(-dr/400)+1))
  return [np.round(we,3), 1-np.round(we,3)]

def k_value(tournament):
    k=5
    if tournament == 'Friendly':
        k=10
    elif 'Nations League' in tournament:
        k = 15
    elif tournament == 'FIFA World Cup qualification' or tournament in confed_tournaments_qual:
        k=25
    elif tournament in confederation_tournaments:
        k=35
    elif tournament == 'FIFA World Cup':
        k=50
    return k

def elo_calculations(results):
    # extract teams and add to ranking system
    teams = results['home_team'].unique()
        
    # ranking
    ranking = {}
    
    # ranking time evolution
    X  = []
    r_italy = []
    r_wales = []
    r_best =[]

    for i in range(len(teams)):
        ranking[teams[i]] = 1350.0
        
    curr_year = int(results.index.min().year)

    if curr_year > 2020:
        return
    
    # update ranking
    for i in range(len(results)):
        team_1 = results['home_team'].iloc[i]
        team_2 = results['away_team'].iloc[i]
        
        k = k_value(results['tournament'].iloc[i])

        # calculate Ea ==> expected match outcome
        if team_2 in teams: 
            ea1 = 1/(1.0+10.0**((ranking[team_2]- ranking[team_1])/400.0))
            ea2 = 1/(1.0+10.0**((ranking[team_1]- ranking[team_2])/400.0))
            
            # draw
            if results['home_score'].iloc[i] == results['away_score'].iloc[i]:
                nr_t1 = ranking[team_1] + k*(0.5 -ea1 )
                nr_t2 = ranking[team_2] + k*(0.5-ea2)
                
            # win team 1
            if results['home_score'].iloc[i] > results['away_score'].iloc[i]:
    
                nr_t1 = ranking[team_1] + k*(1.0 -ea1 )
                nr_t2 = ranking[team_2] + k*(0.0-ea2)
                
            # win team 2
            if results['home_score'].iloc[i] < results['away_score'].iloc[i]:
                nr_t1 = ranking[team_1] + k*(0.0 -ea1 )
                nr_t2 = ranking[team_2] + k*(1.0-ea2)  
            
            ranking[team_1] = nr_t1
            ranking[team_2] = nr_t2 
            
            # making ranking snapshot every end of year
            if curr_year !=  int(results.index[i].year):
                curr_year = int(results.index[i].year)
                
                X.append(curr_year)
                r_italy.append(ranking['Italy'])
                r_wales.append(ranking['Wales'])
                r_best.append(max(ranking.values()))
                
             
    # plot 
    fig = plt.figure(figsize=(20, 10))
    plt.plot(X, r_italy, label = 'Italy', color = 'blue')
    plt.plot(X, r_wales, label = 'Wales', color = 'red')
    plt.plot(X, r_best, label = 'World Nr. 1', color = 'grey')
    fig.suptitle('Elo Score over Time', fontsize=22)
    plt.xlabel('Year', fontsize=18)
    plt.ylabel('Elo Score', fontsize=18)
    plt.legend(loc="upper left", fontsize=16)
    plt.xlim(1875, 2025)

    plt.savefig('assets/elo_scores.png')
             
    # predict result of Italy - Wales
    res = expected_result(ranking['Italy'], ranking['Wales'])
    print(f"ELO Italy - Wales: {ranking['Italy']} - {ranking['Wales']}")
    print("expected result: italy vs wales " + str(res[0]) + ":"  +str(res[1]))
    

###############################################################################
# MAIN CODE
###############################################################################

# load and pre-process data
filepath = 'elo/results.csv'
results = pd.read_csv(filepath)
results.set_index('date', inplace=True)
results.index = pd.to_datetime(results.index)
results.drop(columns={'city','country','neutral'}, inplace=True)

# elo calculations
elo_calculations(results)
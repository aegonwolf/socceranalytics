from datetime import datetime
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd


headers = {'User-Agent':
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 '
               'Safari/537.36'}

# requires some manual work to get the profiles of every player from the national squad
italy = {'Gianluigi Donnarumma': 'https://www.transfermarkt.com/gianluigi-donnarumma/marktwertverlauf/spieler/315858',
         'Giorgio Chiellini': 'https://www.transfermarkt.com/giorgio-chiellini/marktwertverlauf/spieler/29260',
         'Leonardo Bonucci': 'https://www.transfermarkt.com/leonardo-bonucci/marktwertverlauf/spieler/39983',
         'Emerson': 'https://www.transfermarkt.com/emerson/marktwertverlauf/spieler/181778',
         'Giovanni Di Lorenzo': 'https://www.transfermarkt.com/giovanni-di-lorenzo/marktwertverlauf/spieler/169880',
         'Jorginho': 'https://www.transfermarkt.com/jorginho/marktwertverlauf/spieler/102017',
         'Marco Veratti': 'https://www.transfermarkt.com/marco-verratti/marktwertverlauf/spieler/102558',
         'Nicolo Barella': 'https://www.transfermarkt.com/nicolo-barella/marktwertverlauf/spieler/255942',
         'Lorenzo Insigne': 'https://www.transfermarkt.com/lorenzo-insigne/marktwertverlauf/spieler/133964',
         'Federico Chiesa': 'https://www.transfermarkt.com/federico-chiesa/marktwertverlauf/spieler/341092',
         'Ciro Immobile': 'https://www.transfermarkt.com/ciro-immobile/marktwertverlauf/spieler/105521',
         'Alex Meret': 'https://www.transfermarkt.com/alex-meret/marktwertverlauf/spieler/240414',
         'Salvatore Sirigu': 'https://www.transfermarkt.com/salvatore-sirigu/marktwertverlauf/spieler/25508',
         'Franceso Acerbi': 'https://www.transfermarkt.com/francesco-acerbi/marktwertverlauf/spieler/131075',
         'Alessandro Bastoni': 'https://www.transfermarkt.com/alessandro-bastoni/marktwertverlauf/spieler/315853',
         'Rafael Toloi': 'https://www.transfermarkt.com/rafael-toloi/marktwertverlauf/spieler/72441',
         'Alessandro Florenzi': 'https://www.transfermarkt.com/alessandro-florenzi/marktwertverlauf/spieler/130365',
         'Manuel Locatelli': 'https://www.transfermarkt.com/manuel-locatelli/marktwertverlauf/spieler/265088',
         'Bryan Cristante': 'https://www.transfermarkt.com/bryan-cristante/marktwertverlauf/spieler/199248',
         'Matteo Pessina': 'https://www.transfermarkt.com/matteo-pessina/marktwertverlauf/spieler/332179',
         'Domenico Berardi': 'https://www.transfermarkt.com/domenico-berardi/marktwertverlauf/spieler/177843',
         'Federico Bernardeschi': 'https://www.transfermarkt.com/federico-bernardeschi/marktwertverlauf/spieler/197300',
         'Andrea Belotti': 'https://www.transfermarkt.com/andrea-belotti/marktwertverlauf/spieler/167727',
         'Leonardo Spinazzola': 'https://www.transfermarkt.com/leonardo-spinazzola/marktwertverlauf/spieler/118689',
         'Gaetano Castrovilli': 'https://www.transfermarkt.com/gaetano-castrovilli/marktwertverlauf/spieler/303116',
         'Giacomo Raspadori': 'https://www.transfermarkt.com/giacomo-raspadori/marktwertverlauf/spieler/405885'
         }


def marketValue(url):
    """
    Given the link to the player's profile, extract the information about the club,
    market value and the dates of updates based on transfermarkt's data
    Parameters
    ----------
    url: link to 'marktwertverlauf' of the player on Transfermarkt (see examples above)

    Returns
    -------
    a dataframe
    """
    pageTree = requests.get(url, headers=headers)
    pageSoup = BeautifulSoup(pageTree.text, 'html.parser')

    values = []
    dates = []
    clubs = []

    # some gymnastics to extract the data from raw html
    # the structure of the player's page seems to be consistent for every player,
    # so it should just work no matter which player you're interested in
    scripts = pageSoup.find_all('script')
    for number, script in enumerate(scripts):
        if "Highcharts.Chart" in script.text:
            for line in script.text.split('\n'):
                if '\'series\'' in line:
                    result = re.search('\'data\':\[(.*?)]}', line)
                    list = result.group(1).split('{\'y\'')
                    list.pop(0)
                    for elem in list:
                        value = re.search(':(.*?),', elem).group(1)
                        date = re.search('\'datum_mw\':(.*?),\'x\'', elem).group(1).strip('\'')
                        date = datetime.strptime(date, "%b\\x20%d,\\x20%Y")
                        club = re.search('\'verein\':(.*?),', elem).group(1).replace('\\x20', ' ').replace('\\x2D',
                                                                                                           '-').strip(
                            '\'')
                        values.append(int(value))
                        dates.append(date)
                        clubs.append(club)

    return pd.DataFrame.from_dict({'date': dates, 'value': values, 'club': clubs})


def valueEuro(name, url):
    """
    given the name of the player and the link to their Transfermarkt's marktwertverlauf, provides the data
    from 'just' before the tournament and 'right' after Euro2020
    Parameters
    ----------
    name: name of the player (doesn't need to be the same as on transfermarkt, it's just used for the dataframe's index)
    url: link to 'marktwertverlauf' of the player on Transfermarkt (see examples above)

    Returns
    -------
    two dataframes: [0] is the one with the data before the tournament, [1] contains the data from after the tournament
    """
    df = marketValue(url)
    before = df[df['date'] <= datetime.strptime('2021-06-11', '%Y-%m-%d')].iloc[-1:]
    after = df[df['date'] >= datetime.strptime('2021-07-11', '%Y-%m-%d')].head(1)
    before.index = {name}
    after.index = {name}
    return before, after


def valuesTeam(players):
    '''
    combine the values for all the players
    Parameters
    ----------
    players: a dictionary with player names as keys, urls to their profiles as values (see dict 'italy' above)

    Returns
    -------
    two dataframes: [0] is the one with the data before the tournament, [1] contains the data from after the tournament
    '''
    df_before = pd.DataFrame()
    df_after = pd.DataFrame()
    for key in players:
        df_before = pd.concat([df_before, valueEuro(key, players[key])[0]])
        df_after = pd.concat([df_after, valueEuro(key, players[key])[1]])

    return df_before.sort_values('value'), df_after.sort_values('value')


def valueBefore(before):
    '''
    plot the data from before the tournament
    Parameters
    ----------
    before: dataframe containing values from before the tournament started (obtained by function valuesTeam)

    Returns
    -------
    produces a plot and saves it
    '''
    fig, ax = plt.subplots(constrained_layout=True)
    ax.barh(before.index, before['value'])
    ax.set_title('Market value of Italian players right before Euro2020')
    ax.set_xlim(right=7e7)
    ax.set_xlabel('Market value in 10xMio. €')
    fig.savefig('italy_beforeEuro.png')
    plt.show()


def valueAfter(before, after):
    '''
    plot the data based on data after the tournament ended with indicators for the value changes
    Parameters
    ----------
    before: valuesTeam[0]
    after: valuesTeam[1]

    Returns
    -------
    produces a plot and saves it
    '''
    fig, ax = plt.subplots(constrained_layout=True)
    color = []
    label = []
    for player in after.index.values:
        diff = after.loc[player]['value'] - before.loc[player]['value']
        if diff > 0:
            color.append('green')
            label.append('+' + str(diff / 1e7))
        elif diff < 0:
            color.append('red')
            label.append(str(diff / 1e7))
        else:
            color.append('#1f77b4')
            label.append("")

    hbars2 = ax.barh(after.index, after['value'], color=color)
    ax.set_title('Market value of Italian players shortly after Euro2020')
    ax.bar_label(hbars2, labels=label)
    ax.set_xlim(right=8e7)
    ax.set_xlabel('Market value in 10xMio. €')
    fig.savefig('italy_afterEuro.png')
    plt.show()


def transfers(before, after):
    '''
    lists all the transfers which took place directly after the tournament ended
    Parameters
    ----------
    before: valuesTeam[0]
    after: valuesTeam[1]

    Returns
    -------
    a dataframe containing the names of the transferred players as indices & clubs from & to which they were transferred
    '''
    dict = {}
    for player in before.index.values:
        prev_club = before.loc[player]['club']
        next_club = after.loc[player]['club']
        if prev_club != next_club:
            dict[player] = [prev_club, next_club]

    print(pd.DataFrame.from_dict(dict, orient='index', columns=['from', 'to']))


before, after = valuesTeam(italy)

valueBefore(before)
valueAfter(before, after)
transfers(before, after)

#----------------------------------------------------------------------------
# Created By: Danny Camenisch (dcamenisch)
# Created Date: 19/03/2022
# version ='1.1'
# ---------------------------------------------------------------------------
""" 
Simple module to parse the UEFA website to get player id's, names, positions and stats
for a given team.
"""
# ---------------------------------------------------------------------------
import requests
from bs4 import BeautifulSoup

urlItaly = 'https://web.archive.org/web/20210712203057/https://www.uefa.com/uefaeuro-2020/teams/66--italy/squad/'
urlWales = 'https://web.archive.org/web/20210620033107/https://www.uefa.com/uefaeuro-2020/teams/144--wales/squad/'

class Player:
    def __init__(self, attr):
        self.id             = attr[0]
        self.name           = attr[1]
        self.number         = attr[2]
        self.position       = attr[3]
        self.age            = attr[4]
        self.gamesPlayed    = attr[5]
        self.goals          = attr[6]

def getPlayerInfos(teamID):
    if teamID == 66:
        teamURL = urlItaly
    elif teamID == 144:
        teamURL = urlWales
    else:
        return None

    # Get the HTML from the site
    page = requests.get(teamURL)

    # Check for bad status code
    if not page.status_code == 200:
        print("Error: Could not get the page")
        return

    # Parse the HTML
    html = page.text
    soup = BeautifulSoup(html, 'html.parser')
    
    # The HTML has multiple divs with class 'squad--team-wrap' that contain all 
    # the player infos split by postition
    squad = soup.find_all('div', class_='squad--team-wrap')

    # Extract the player infos from the HTML
    players = []

    for wrap in squad[0:4]:
        postition = wrap.h5.text[:-1]

        for player in wrap.find('tbody').find_all('tr'):
            infos = player.find_all('td')

            players.append(Player([
                infos[0].find('a', class_='player-name')["href"].split("/")[-2].split("-")[0], 
                infos[0].find('a', class_='player-name')["title"], 
                infos[0].text.strip().split(" ")[-1].strip("()"), 
                postition, 
                infos[1].text.strip(), 
                infos[2].text.strip().replace("-", "0"), 
                infos[3].text.strip().replace("-", "0")
            ]))

    return players

# Examples
print(getPlayerInfos(66))
print(getPlayerInfos(144))
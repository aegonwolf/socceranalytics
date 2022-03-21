import xml.etree.ElementTree as ET  # parsing XML files
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from glob import glob
import numpy as np
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
from bokeh.models.glyphs import Circle, Patches, Wedge
from bokeh.plotting import figure
from bokeh.models import Range1d
from math import pi
import imageio
import requests
from bs4 import BeautifulSoup
#https://github.com/znstrider/PyFootballPitch/blob/master/Football_Pitch_Bokeh.py#L6


class Match:
    """
    Creates a super useful match Object from the tracking data
    Credit Danny
    """
    def __init__(self, match):
        self.matchID = int(match.attrib['id'])
        self.matchNr = int(match.attrib['matchNumber'])
        self.date = match.attrib['dateMatch']
        self.stadiumID = int(match[1].attrib['id'])
        self.stadiumName = match[1].attrib['name']
        self.pitchLength = int(match[1].attrib['pitchLength'])
        self.pitchWidth = int(match[1].attrib['pitchWidth'])
        self.phases = match[2]
        self.frames = match[3]

def tracking_to_parquet(path, save = False, save_path = None):
    """
    credit Bojan
    converts tracking data to pandas dataframe
    saves in parquet if save == True
    saves to current directory
    params path: str, path to xml tracking file
    params save: Bool: whether or not to save
    params savepath: str path to save dataframe
    """
    tree = ET.parse(path).getroot()
    match = Match(tree[0])

    framedict = dict()

    players_ids = dict()  # dictionary for storing unique mappings from player's id to {1,...,(22 + #subs during the match)}
    for index, frame in enumerate(match.frames):
        time = frame.attrib["utc"]

        columns = dict()

        for i, obj in enumerate(frame[0]):
            columns['time'] = time
            if obj.attrib['type'] == '7':
                for key, value in obj.attrib.items():
                    columns["ball_" + key] = value
            else:
                if not obj.attrib['id'] in players_ids:
                    players_ids[obj.attrib['id']] = len(players_ids) + 1

                for key, value in obj.attrib.items():
                    columns["player" + str(players_ids[obj.attrib['id']]) + "_" + key] = value

        framedict[index] = columns

    df = pd.DataFrame.from_dict(framedict, orient='index')
    df.to_parquet(save_path, index=False)
#%%
def create_pitch(length, width, linecolor, bounds = 15):

    """
    mainly stolen from fc python
    param length: an int the length of the field
    param width: an int the height of the field
    param linecolor: the color of the lines
"""
    #Create figure
    fig=plt.figure()
    #fig.set_size_inches(7, 5)
    ax=fig.add_subplot(1,1,1)

    #Pitch Outline & Centre Line
    plt.plot([0,0],[0,width], color=linecolor)
    plt.plot([0,length],[width,width], color=linecolor)
    plt.plot([length,length],[width,0], color=linecolor)
    plt.plot([length,0],[0,0], color=linecolor)
    plt.plot([length/2,length/2],[0,width], color=linecolor)
    plt.fill_between(x = [-bounds, length + bounds],
                     y1 = [width + bounds, width + bounds],
                     y2 = [-bounds, -bounds], color='green')

    #Left Penalty Area
    plt.plot([16.5 ,16.5],[(width/2 +16.5),(width/2-16.5)],color=linecolor)
    plt.plot([0,16.5],[(width/2 +16.5),(width/2 +16.5)],color=linecolor)
    plt.plot([16.5,0],[(width/2 -16.5),(width/2 -16.5)],color=linecolor)

    #Right Penalty Area
    plt.plot([(length-16.5),length],[(width/2 +16.5),(width/2 +16.5)],color=linecolor)
    plt.plot([(length-16.5), (length-16.5)],[(width/2 +16.5),(width/2-16.5)],color=linecolor)
    plt.plot([(length-16.5),length],[(width/2 -16.5),(width/2 -16.5)],color=linecolor)

    #Left 5-meters Box
    plt.plot([0,5.5],[(width/2+7.32/2+5.5),(width/2+7.32/2+5.5)],color=linecolor)
    plt.plot([5.5,5.5],[(width/2+7.32/2+5.5),(width/2-7.32/2-5.5)],color=linecolor)
    plt.plot([5.5,0.5],[(width/2-7.32/2-5.5),(width/2-7.32/2-5.5)],color=linecolor)

    #Right 5-meters Box
    plt.plot([length,length-5.5],[(width/2+7.32/2+5.5),(width/2+7.32/2+5.5)],color=linecolor)
    plt.plot([length-5.5,length-5.5],[(width/2+7.32/2+5.5),width/2-7.32/2-5.5],color=linecolor)
    plt.plot([length-5.5,length],[width/2-7.32/2-5.5,width/2-7.32/2-5.5],color=linecolor)

    #Prepare Circles
    centreCircle = plt.Circle((length/2,width/2),9.15,color=linecolor,fill=False)
    centreSpot = plt.Circle((length/2,width/2),0.8,color=linecolor)
    leftPenSpot = plt.Circle((11,width/2),0.8,color=linecolor)
    rightPenSpot = plt.Circle((length-11,width/2),0.8,color=linecolor)

    #Draw Circles
    ax.add_patch(centreCircle)
    ax.add_patch(centreSpot)
    ax.add_patch(leftPenSpot)
    ax.add_patch(rightPenSpot)

    #Prepare Arcs
    leftArc = Arc((11,width/2),height=18.3,width=18.3,angle=0,theta1=308,theta2=52,color=linecolor)
    rightArc = Arc((length-11,width/2),height=18.3,width=18.3,angle=0,theta1=128,theta2=232,color=linecolor)

    #Draw Arcs
    ax.add_patch(leftArc)
    ax.add_patch(rightArc)
    #Axis titles
    #Tidy Axes
    plt.axis('off')

    return fig,ax

#This function creates a gif like you've seen in my presentation
def create_gif(images_path, gif_path):
    images = []
    filenames = sorted(glob(images_path))
    #I know it's a double sort but this isn't A&D!!!
    filenames.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
    for index, filename in enumerate(filenames):
        img = imageio.imread(filename)
        images.append(img)
    imageio.mimsave(gif_path, images, fps=10) # Save gif



def draw_pitch(width = 700, height = 500,
               measure = 'metres',
               fill_color = '#B3DE69', fill_alpha = 0.5,
               line_color = 'grey', line_alpha = 1,
               #hspan = [-52.5, 52.5], vspan = [-34, 34],
               hspan = [0, 105], vspan = [0, 68],
               arcs = True):
    '''
    -----
    Draws and returns a pitch on a Bokeh figure object with width 105m and height 68m
    p = drawpitch()
    -----
    hspan = [left, right] // eg. for SBData this is: hspan = [0, 120]
    vspan = [bottom, top] //
    to adjust the plot to your needs.
    -----
    set arcs = False to not draw the penaltybox arcs
    '''

    # measures:
    # goalcenter to post, fiveyard-box-length, fiveyard-width,
    # box-width, penalty-spot x-distance, circle-radius

    measures = [3.66, 5.5, 9.16, 16.5, 40.32, 11, 9.15]

    hmid = hspan[1] / 2.0
    vmid = vspan[1] / 2.0

    p = figure(width = width,
               height = height,
               x_range = Range1d(hspan[0], hspan[1]),
               y_range = Range1d(vspan[0], vspan[1]))

    boxes = p.quad(top = [vspan[1], vmid+measures[2], vmid+measures[4]/2, vmid+measures[4]/2, vmid+measures[2]],
                   bottom = [vspan[0], vmid-measures[2], vmid-measures[4]/2, vmid-measures[4]/2, vmid-measures[2]],
                   left = [hspan[0], hspan[1]-measures[1], hspan[1]-measures[3], hspan[0]+measures[3], hspan[0]+measures[1]],
                   right = [hspan[1], hspan[1], hspan[1], hspan[0], hspan[0]],
                   color = fill_color,
                   alpha = [fill_alpha,0,0,0,0], line_width = 2,
                   line_alpha = line_alpha,
                   line_color = line_color)
    boxes.selection_glyph = boxes.glyph
    boxes.nonselection_glyph = boxes.glyph

    #middle circle
    p.circle(x=[hmid], y=[vmid], radius = measures[6],
             color = line_color,
             line_width = 2,
             fill_alpha = 0,
             fill_color = 'grey',
             line_color= line_color)

    if arcs == True:
        p.arc(x=[hspan[0]+measures[5], hspan[1]-measures[5]], y=[vmid, vmid],
              radius = measures[6],
              start_angle = [(2*pi-np.arccos((measures[3]-measures[5])/measures[6])), pi - np.arccos((measures[3]-measures[5])/measures[6])],
              end_angle = [np.arccos((measures[3]-measures[5])/measures[6]), pi + np.arccos((measures[3]-measures[5])/measures[6])],
              color = line_color,
              line_width = 2)

    p.circle([hmid, hspan[1]-measures[5], hspan[0]+measures[5]], [vmid, vmid, vmid], size=5, color=line_color, alpha=1)
    #midfield line
    p.line([hmid, hmid], [vspan[0], vspan[1]], line_width = 2, color = line_color)
    #goal lines
    p.line((hspan[1],hspan[1]),(vmid+measures[0],vmid-measures[0]), line_width = 6, color = 'white')
    p.line((hspan[0],hspan[0]),(vmid+measures[0],vmid-measures[0]), line_width = 6, color = 'white')
    p.grid.visible = False
    p.xaxis.visible = False
    p.yaxis.visible = False

    return p

def save_frames(df, length, width, position_cols, output_path):
    for index, frame in df.iterrows():
        fig, ax = create_pitch(length, width,'white')
        x, y = df.loc[index, "ball_x"] / 100, df.loc[index, "ball_y"] /100
        x = length/2.0 + x
        y = width/2.0 + y
        plt.scatter(x, y, marker = 'o', color = 'black')
        for i in range(3, len(position_cols), 3):
            t, x, y = df.loc[index, position_cols[i]], df.loc[index, position_cols[i + 1]], df.loc[index, position_cols[i + 2]]
            if np.isnan(x) or np.isnan(y):
                continue
            t = int(t)
            x = length/2.0 + x
            y = width/2.0 + y

            y = 80 - y
            color = 'yellow' if t == 0 else 'red'
            plt.scatter(x,y, marker = 'o', color = color)
        plt.ioff()
        plt.savefig(output_path + f'/{index}.png')
        plt.close(fig)
    #     if index % 100 == 0:
    #         plt.show()



baseURL = "https://www.uefa.com/uefaeuro-2020/teams/"

class Player:
    """
    Player Object
    Credit: Danny Camenisch
    """
    def __init__(self, attr):
        self.id             = attr[0]
        self.name           = attr[1]
        self.number         = attr[2]
        self.position       = attr[3]
        self.age            = attr[4]
        self.gamesPlayed    = attr[5]
        self.goals          = attr[6]

def parseSite(teamID):
    """
    get Player Id Name mappings
    credit Danny Camenisch
    :param teamID: Int Id of Team
    """
    teamURL = baseURL + str(teamID) + "/squad/"

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

    for wrap in squad[1:5]:
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


def create_gif(images_path, gif_path):
    """
    Creates a gif from images in images_path, saves to gif_path
    :param images_path: str path to image folder
    :param gif_path: str output path for gif
    :return: None
    """
    images = []
    images_path = images_path + '/*.png'
    filenames = sorted(glob(images_path))
    #I know it's a double sort but this isn't A&D :-)
    filenames.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
    for index, filename in enumerate(filenames):
        img = imageio.imread(filename)
        images.append(img)
    imageio.mimsave(gif_path, images, fps=10) # Save gif
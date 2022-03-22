#----------------------------------------------------------------------------
# Created By: Danny Camenisch (dcamenisch)
# Created Date: 10/03/2022
# version ='1.1'
# ---------------------------------------------------------------------------
""" 
Simple module to convert a xml file containing data in TRACAB format to a Match object
"""
# ---------------------------------------------------------------------------
import xml.etree.ElementTree as et

class Match:
    def __init__(self, filePath):
        match = et.parse(filePath).getroot()[0]

        self.matchID      = int(match.attrib['id'])
        self.matchNr      = int(match.attrib['matchNumber'])
        self.date         = match.attrib['dateMatch']
        self.stadiumID    = int(match[1].attrib['id'])
        self.stadiumName  = match[1].attrib['name']
        self.pitchLength  = int(match[1].attrib['pitchLength'])
        self.pitchWidth   = int(match[1].attrib['pitchWidth'])
        self.phases       = [Phase(phase) for phase in match[2]]
        self.frames       = [Frame(frame) for frame in match[3]]
        
class Phase:
    def __init__(self, phase):
        self.start       = phase.attrib['start']
        self.end         = phase.attrib['end']
        self.leftTeamID  = int(phase.attrib['leftTeamID'])
        
class Frame:
    def __init__(self, frame):
        self.time            = frame.attrib['utc']
        self.ballInPlay      = frame.attrib['isBallInPlay']
        self.ballPossession  = frame.attrib['ballPossession']
        self.trackingObjs    = [TrackingObj(obj) for obj in frame[0]]
    
class TrackingObj:
    def __init__(self, obj):
        self.type      = obj.attrib['type']
        self.id        = obj.attrib['id']
        self.x         = int(obj.attrib['x'])
        self.y         = int(obj.attrib['y'])
        self.sampling  = obj.attrib['sampling']
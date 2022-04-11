import json
import pandas as pd
import numpy as np

def json_to_normalized_dataframe(path):
    '''
    Converts a json file to a pandas dataframe
    '''
    obj = read_json(path)
    df = pd.json_normalize(obj)
    return df
    
def read_json(path):
    '''
    Read JSON file from path
    '''
    with open(path, 'r', encoding="UTF-8") as f:
        return json.loads(f.read())
    
def statsbomb_to_point(location, max_width=120, max_height=80):
    '''
    Convert a point's coordinates from a StatsBomb's range to 0-1 range.
    '''
    return location[0] / max_width, 1 - (location[1] / max_height)

def point_to_meters(p):
    '''
    Convert a point's coordinates from a 0-1 range to meters.
    '''
    config = read_json("plot_config.json")
    return np.array([p[0] * config["width"], p[1] * config["height"]])

def change_range(value, old_range, new_range):
    '''
    Convert a value from one range to another one, maintaining ratio.
    '''
    return ((value-old_range[0]) / (old_range[1]-old_range[0])) * (new_range[1]-new_range[0]) + new_range[0]
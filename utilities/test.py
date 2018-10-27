#import requests
#import ast
#import json
import pandas as pd
#from assets import range_all_dates
from config import teams, seasons, season_sql
import datetime
import numpy as np
from assets import list_games, range_all_dates
#from argparse import ArgumentParser
from os.path import expanduser
import sys
import result_calculator
home_dir = expanduser("~")
syspath = '%s/projects/NBA_Jam/'%home_dir
sys.path.insert(0,syspath)
from pulls import four_factors_scraper
from utilities import db_connection_manager


engine = db_connection_manager.establish_db_connection('sqlalchemy')
conn = engine.connect()

## get list of all games from 2017-18 season
full_season = pd.read_sql("SELECT * FROM flatten_final_scores WHERE game_id LIKE '002160%%'", con = conn)
games_list = full_season['game_id'].tolist()

four_factors_scraper.player_stats(games_list = games_list)

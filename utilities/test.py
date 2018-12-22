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
from pulls import spreads_scraper
from utilities import db_connection_manager


engine = db_connection_manager.establish_db_connection('sqlalchemy')
conn = engine.connect()

## get list of all games from 2017-18 season
for d in range_all_dates("2018-12-19", "2018-12-19"):
    df = spreads_scraper.main(d)
    df.drop(columns = ['time'], inplace = True)
    df['date'] = df['date'].str[0:4] + "-" + df['date'].str[4:6] + "-" + df['date'].str[6:8]

    df.to_sql('spreads', con = conn, if_exists = 'append', index = False)

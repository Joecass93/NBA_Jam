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

### USE THIS TO SCRAPE SPREADS AND UPLOAD TO DB, AD HOC ###
engine = db_connection_manager.establish_db_connection('sqlalchemy')
conn = engine.connect()

for d in range_all_dates("2018-12-25", "2018-12-25"):
    df = spreads_scraper.main(d)
    df.drop(columns = ['time'], inplace = True)
    df['date'] = df['date'].str[0:4] + "-" + df['date'].str[4:6] + "-" + df['date'].str[6:8]

    df.to_sql('spreads', con = conn, if_exists = 'append', index = False)

#### MISC TEST FUNCTIONS ####
# class Test():
#
#     def __init__(self, *dates):
#
#         self.config(dates)
#
#     def config(self, *dates):
#         for d in dates:
#             print d[1]
#
# if __name__ == "__main__":
#     Test('test1', 'test2')

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
#from pulls import spreads_scraper
import sys
import result_calculator
home_dir = expanduser("~")
syspath = '%s/projects/NBA_Jam/db/'%home_dir
sys.path.insert(0,syspath)
import db_connection_manager

engine = db_connection_manager.establish_db_connection('sqlalchemy')
conn = engine.connect()

d_range = range_all_dates('2017-10-21', '2017-12-31')

for d in d_range:
    print d
    d_result = result_calculator.main(d)
    try:
        d_result.to_sql('results_table', con = conn, if_exists = 'append', index = False)
    except Exception as e:
        print "couldn't write results to db because: %s"%e

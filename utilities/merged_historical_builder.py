"""
MERGED HISTORICAL BUILDER

DESCRIPTION:
This script allows the user to enter start and end dates, and return a predictions dataframe for all dates
within the given range.

IMPORTED BY:

IMPORT(S): merged_data_builder_daily.main(), db_connection_manager.establish_db_connection

INPUT(S):
Date in string format - 'YYYY-MM-DD'

OUTPUT(S):
Dataframe containing each game for the date range selected with the following metrics:
vegas spread, predicted spread, differential between predicted and actual spread, and ranking
for each game

FUNCTION(S):

CREATED/REFACTORED BY: Joe Cassidy / 08.12.2018

"""

import pandas as pd
from argparse import ArgumentParser
from assets import range_all_dates
import datetime
from db_connection_manager import establish_db_connection
import sys
from os.path import expanduser
home_dir = expanduser('~')
syspath = '%s/projects/NBA_Jam/'%home_dir
sys.path.insert(0,syspath)
import merged_data_builder_daily as mdb


parser = ArgumentParser()
parser.add_argument("-s", "--start_date", help="date to start pulling final scores data from: ex. '2017-11-01'", type=str, required=False)
parser.add_argument("-e", "--end_date", help = "date to end pulling final scores data from: ex. '2017-11-01'", type=str, required=False)

flags = parser.parse_args()

if flags.start_date:
    sdate = flags.start_date
else:
    sdate = datetime.date.today().strftime('%Y-%m-%d')
if flags.end_date:
    edate = flags.end_date
else:
    edate = sdate

def main():
    date_range = range_all_dates(sdate, edate)
    sql_table = 'historical_picks_table'
    for i, d in enumerate(date_range):
        d_games = mdb.main(d)
        engine = establish_db_connection('sqlalchemy')
        conn = engine.connect()
        try:
            print "writing predictions for %s to %s"%(d, sql_table)
            d_games.to_sql(name = sql_table, con = conn, if_exists = 'append', index = False)
            print "predictions successfully written to db at %s"%datetime.datetime.now()
        except Exception as e:
            print "db write failed because: %s"%e

    return None

if __name__ == '__main__':
    main()

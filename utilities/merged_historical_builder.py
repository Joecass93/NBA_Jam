import pandas as pd
import sys
from os.path import expanduser
from argparse import ArgumentParser
from assets import range_all_dates
import datetime
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
    edate = datetime.date.today().strftime('%Y-%m-%d')

def main():
    date_range = range_all_dates(sdate, edate)
    for d in date_range:
        d_games = mdb.main(d)

    return None

if __name__ == '__main__':
    main()

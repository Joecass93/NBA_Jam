import pandas as pd
import sys
from os.path import expanduser
from argparse import ArgumentParser
from assets import range_all_dates
import datetime
from db_connection_manager import establish_db_connection
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
    for i, d in enumerate(date_range):
        d_games = mdb.main(d)
        if i == 0:
            full_results = d_games
        else:
            full_results = full_results.append(d_games)

    full_results.to_csv('%s/projects/NBA_JAM/Data/historical_picks.csv'%home_dir, sep = ',')
    print full_results

    engine = establish_db_connection('sqlalchemy')
    conn = engine.connect()
    full_results.to_sql(name = 'historical_picks', con = conn, if_exists = 'append', index = False)

    return full_results

if __name__ == '__main__':
    main()

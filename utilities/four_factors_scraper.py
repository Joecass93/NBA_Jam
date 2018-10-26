import pandas as pd
from config import request_header, teams
from db_connection_manager import establish_db_connection
import requests
import json
from argparse import ArgumentParser
from datetime import datetime, date
from assets import range_all_dates, games_daily


## API Error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)


## Argument Parsing
parser = ArgumentParser()
parser.add_argument("-s", "--start_date", help="date to start pulling final scores data from: ex. '2017-11-01'", type=str, required=False)
parser.add_argument("-e", "--end_date", help = "date to end pulling final scores data from: ex. '2017-11-01'", type=str, required=False)

flags = parser.parse_args()

if flags.start_date:
    sdate = flags.start_date
else:
    sdate = date.today().strftime('%Y-%m-%d')
if flags.end_date:
    edate = flags.end_date
else:
    edate = sdate

## functions start here
def main(start_date = sdate, end_date = edate):

    ## Get list of all game ids in the specified date range
    games_range = range_all_dates(start_date, end_date)
    games_list = []
    for d in games_range:
        scoreboard = games_daily(d)
        d_games = list(scoreboard['GAME_ID'])
        games_list.append(d_games)

    ## denest the list of game ids
    games_list = [val for sublist in games_list for val in sublist]
    full_games_list = []

    ## loop through and create a dataframe containing four factors data for each game in the list
    rerun_urls = []
    for i, g in enumerate(games_list):
        print "getting four factors data for game id = %s"%g
        try:
            games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
            response = sess.get(games_url, headers=request_header)
            print response
            data = response.text
            data = json.loads(data)
            cleaner = data['resultSets']
            cleanest = cleaner[1]
            col_names = cleanest['headers']
            game_data = cleanest['rowSet']
            if i == 0:
                game_ff_df = pd.DataFrame(game_data, columns = col_names)
            else:
                game_ff_df = game_ff_df.append(pd.DataFrame(game_data, columns = col_names))
        except:
            rerun_urls.append(games_url)
            pass

    if len(rerun_urls) > 0:
        print "The following games could not be scraped: %s"%rerun_urls

    ## upload to db
    conn = establish_db_connection('sqlalchemy').connect()
    print "writing four factors data to database..."
    #game_ff_df.to_sql('four_factors', con = conn, if_exists = 'append', index = False)

    return game_ff_df

if __name__ == "__main__":
    main()

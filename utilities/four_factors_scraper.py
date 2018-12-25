import pandas as pd
from config import request_header, teams
from db_connection_manager import establish_db_connection
import requests
import json
from argparse import ArgumentParser
from datetime import datetime, date, timedelta
from assets import games_daily, range_all_dates

## API Error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

## Argument Parsing
parser = ArgumentParser()
parser.add_argument("-s", "--start_date", help="date to start pulling final scores data from: ex. '2017-11-01'", type=str, required=False)
parser.add_argument("-e", "--end_date", help = "date to end pulling final scores data from: ex. '2017-11-01'", type=str, required=False)
parser.add_argument("-t", "--type", help = "type of scrape to perform (player or team stats), default is both", type=str, required=False)

flags = parser.parse_args()

if flags.start_date:
    sdate = flags.start_date
else:
    sdate = date.today().strftime('%Y-%m-%d')
if flags.end_date:
    edate = flags.end_date
else:
    edate = sdate
if flags.type:
    type = flags.type
else:
    type = None

def main(start_date = sdate, end_date = edate, type = type):
    drange = range_all_dates(start_date, end_date)
    for d in drange:
        pstats, tstats = _fetch_game_stats(d)
        print "Uploading stats for %s to db..."%d
        _upload_to_db(pstats, 'four_factors_player')
        print " -> Uploaded player stats!"
        _upload_to_db(tstats, 'four_factors_team')
        print " -> Uploaded team stats!"
        print ""

    return None

def _fetch_game_stats(prev_day):
    games_list = _get_games_list(prev_day)
    print "Getting stats for %s..."%prev_day
    for i, g in enumerate(games_list):
        print " -> %s/%s"%(i+1, len(games_list))
        game_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
        response = sess.get(game_url, headers=request_header)
        game_dict = json.loads(response.text)
        pcol_names = game_dict['resultSets'][0]['headers']
        player_stats = game_dict['resultSets'][0]['rowSet']
        tcol_names = game_dict['resultSets'][1]['headers']
        team_stats = game_dict['resultSets'][1]['rowSet']

        pgame_df = pd.DataFrame(data = player_stats, columns = pcol_names)
        tgame_df = pd.DataFrame(data = team_stats, columns = tcol_names)

        if i == 0:
            players_df = pgame_df
            teams_df = tgame_df
        else:
            players_df = players_df.append(pgame_df)
            teams_df = teams_df.append(tgame_df)

    return players_df, teams_df

def _get_games_list(game_date):
    games_df = games_daily(game_date)
    games_list = games_df['GAME_ID'].tolist()
    return games_list

def _upload_to_db(table, db_tbl):
    conn = establish_db_connection('sqlalchemy').connect()
    table.to_sql(db_tbl, con = conn, if_exists = 'append', index = False)
    return None

if __name__ == "__main__":
    main()

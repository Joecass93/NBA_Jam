import pandas as pd
import numpy as np
from os.path import expanduser
import sys
import datetime
import json
import requests
from argparse import ArgumentParser
home_dir = expanduser('~')
syspath = '%s/projects/NBA_Jam/'%home_dir
sys.path.insert(0,syspath)
from utilities.assets import range_all_dates
from utilities.config import teams, spread_teams, request_header
from utilities.db_connection_manager import establish_db_connection

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
        print "getting scores for %s"%d
        dirty_scores = get_scores(d)
        if len(dirty_scores) > 0:
            clean_scores = format_scores(dirty_scores)

            try:
                print "writing scores to db..."
                write_scores_to_db(clean_scores, 'historical_scores_table', 'sqlalchemy')
                print "scores for %s succesfully written to db!"%d
            except Exception as e:
                print "db write failed because: %s"%e

        else:
            pass

        print ""

    return None

def get_scores(gamedate):

    gamedate = datetime.datetime.strptime(gamedate, '%Y-%m-%d')
    gamedate = gamedate.strftime('%m/%d/%Y')

    try:
        scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%gamedate
        response = requests.get(scoreboard_url, headers=request_header)
        data = response.text
        data = json.loads(data)
        cleaner = data['resultSets'][1]
        col_names = cleaner['headers']
    except requests.ConnectionError as e:
        print e

    # Check how many games there are today
    scoreboard_len = len(cleaner['rowSet'])

    # Loop through and get each game's info
    games_today = []
    for x in range(0,scoreboard_len):
        game_info = cleaner['rowSet'][x]
        games_today.append(game_info)

    # Create dataframe containing info about today's game
    df_matches = pd.DataFrame(games_today, columns = col_names)

    return df_matches

def format_scores(dirty_scores):
    num_games = int(dirty_scores['GAME_SEQUENCE'].max())
    for i in range(1, num_games + 1):
        curr_game = dirty_scores[dirty_scores['GAME_SEQUENCE'] == i][['GAME_DATE_EST', 'GAME_SEQUENCE','GAME_ID','TEAM_ID','TEAM_NAME', 'PTS']]
        curr_game.insert(5, 'SIDE', ['away', 'home'])

        game_a = curr_game[curr_game['SIDE'] == 'away']
        game_h = curr_game[curr_game['SIDE'] == 'home']

        clean_cols = ['game_date', 'sequence', 'game_id', 'away_id', 'away_team', 'home_id', 'home_team', 'pts_away',
                        'pts_home', 'pt_diff_away', 'pts_total', 'win_side', 'win_id']
        pt_diff = game_a['PTS'].item() - game_h['PTS'].item()
        pt_total = game_a['PTS'].item() + game_h['PTS'].item()
        ## Determine winner
        if pt_diff > 0:
            win_side = 'away'
            win_id = game_a['TEAM_ID'].item()
        else:
            win_side = 'home'
            win_id = game_h['TEAM_ID'].item()

        clean_game = pd.DataFrame([[game_a['GAME_DATE_EST'].item().encode('utf-8').split("T", 1)[0],
                                    game_a['GAME_SEQUENCE'].item(), game_a['GAME_ID'].item(),
                                    game_a['TEAM_ID'].item(), game_a['TEAM_NAME'].item(),
                                    game_h['TEAM_ID'].item(), game_h['TEAM_NAME'].item(),
                                    game_a['PTS'].item(), game_h['PTS'].item(),
                                    pt_diff, pt_total, win_side, win_id]], columns = clean_cols)
        if i == 1:
            clean_scores = clean_game
        else:
            clean_scores = clean_scores.append(clean_game)





    return clean_scores

def write_scores_to_db(scores, sql_table, sql_engine, if_exists = 'append'):
    engine = establish_db_connection(sql_engine)
    conn = engine.connect()

    scores.to_sql(name = sql_table, con = conn, if_exists = if_exists, index = False)
    return None


if __name__ == "__main__":
    main()

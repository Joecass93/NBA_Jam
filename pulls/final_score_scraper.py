import pandas as pd
import numpy as np
from os.path import expanduser
import sys
import datetime
import json
import requests
home_dir = expanduser('~')
syspath = '%s/projects/NBA_Jam/'%home_dir
sys.path.insert(0,syspath)
from utilities.assets import range_all_dates
from utilities.config import teams, spread_teams, request_header

def main():
    dirty_scores = get_scores()
    clean_scores = format_scores()
    print dirty_scores
    return dirty_scores

def get_scores(gamedate = None):
    #gamedate = datetime.datetime.strptime(gamedate, '%Y-%m-%d')
    #gamedate = gamedate.strftime('%m/%d/%Y')
    gamedate = '11/01/2017' ## Remove when done testing
    print gamedate
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

    x = 0
    games_today = []
    # Loop through and get each game's info
    for x in range(0,scoreboard_len):
        game_info = cleaner['rowSet'][x]
        games_today.append(game_info)
        x = x + 1

    # Create dataframe containing info about today's game
    df_matches = pd.DataFrame(games_today, columns = col_names)

    return df_matches

def format_scores(dirty_score = None):
    return None

if __name__ == "__main__":
    main()

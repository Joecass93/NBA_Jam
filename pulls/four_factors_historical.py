import pandas as pd
import numpy as np
from utilities.assets import list_games
from utilities.config import request_header, teams
from utilities.db_connection_manager import establish_db_connection
import requests
import json

## API error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

def main():
    k_list = ['1610612740', '1610612760', '1610612761']
    for k in teams['nba_teams']:
        k = str(k)
        if k in k_list:
            team_ff = get_four_factors(k, '2018-04-11')
            store_four_factors(team_ff)
        else:
            pass

    return None

def get_four_factors(team_id, end_date):
    team_games = list_games(team_id, end_date)
    print team_games
    team_ff_list = []
    for g in team_games:
        games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
        response = sess.get(games_url, headers=request_header)
        data = response.text
        data = json.loads(data)
        cleaner = data['resultSets']
        cleanest = cleaner[1]
        col_names = cleanest['headers']
        team_data = cleanest['rowSet']
        team_id_int = int(team_id)
        if team_id_int in team_data[0]:
            team_ff = team_data[0]
        else:
            team_ff = team_data[1]

        team_ff_list.append(team_ff)

    team_ff_df = pd.DataFrame(team_ff_list, columns = col_names)
    return team_ff_df

def store_four_factors(team_data):
    engine = establish_db_connection('sqlalchemy')
    conn = engine.connect()

    team_data.to_sql('four_factors_table', con = conn, if_exists = 'append', index = False)

    return None

if __name__ == "__main__":
    main()

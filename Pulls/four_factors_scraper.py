import pandas as pd
import sys
sys.path.insert(0, "/Users/joe/projects/NBA_Jam/")
from utilities import config, db_connection_manager, assets
import requests
import json

## API Error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

class player_stats():

    def __init__(self, game_date = None, games_list = None):

        print game_date

        self._fetch_player_stats(game_date, games_list)


    def _fetch_player_stats(self, game_date, games_list):

        self.game_date = game_date
        self.games_list = games_list

        if self.game_date is not None:
            print "Getting list of games for %s"%self.game_date
            print ""
            self.games_list = get_games_list(self.game_date)

        ## loop through all games in the list and return player stats
        for i, g in enumerate(self.games_list):

            print "Getting player stats for game: %s (%s/%s)"%(g, i+1, len(self.games_list))

            game_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
            response = sess.get(game_url, headers=config.request_header)
            game_dict = json.loads(response.text)
            player_json = game_dict['resultSets'][0]
            col_names = player_json['headers']
            player_stats = player_json['rowSet']
            game_df = pd.DataFrame(data = player_stats, columns = col_names)

            print "->  Gottem"

            if i == 0:
                daily_df = game_df
            else:
                daily_df = daily_df.append(game_df)

        return daily_df


class team_stats():

    def __init__(self, game_date = None, games_list = None):

        print game_date

        self._fetch_team_stats(game_date, games_list)

    def _fetch_team_stats(self, game_date, games_list):

        self.game_date = game_date
        self.games_list = games_list

        if self.game_date is not None:
            print "Getting list of games for %s"%self.game_date
            print ""
            self.games_list = get_games_list(self.game_date)

        ## loop through all games in the list and return player stats
        for i, g in enumerate(self.games_list):

            print "Getting team stats for game: %s (%s/%s)"%(g, i+1, len(self.games_list))

            game_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
            response = sess.get(game_url, headers=config.request_header)
            game_dict = json.loads(response.text)
            team_json = game_dict['resultSets'][1]
            col_names = team_json['headers']
            team_stats = team_json['rowSet']
            game_df = pd.DataFrame(data = team_stats, columns = col_names)

            print "->  Gottem"

            if i == 0:
                daily_df = game_df
            else:
                daily_df = daily_df.append(game_df)

        return daily_df


def upload_stats_to_db(stats, table):

    print ""
    print "Uploading to db..."
    print ""
    print stats
    conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()
    stats.to_sql(table, con = conn, if_exists = 'append')

    print "Great success!"

    return None

def get_games_list(game_date):

    games_df = assets.games_daily(game_date)

    games_list = games_df['GAME_ID'].tolist()

    return games_list

if __name__ == "__main__":
    player_stats()

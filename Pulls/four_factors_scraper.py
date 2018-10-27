import pandas as pd
import sys
sys.path.insert(0, "/Users/joe/projects/NBA_Jam/")
from utilities import config, db_connection_manager
import requests
import json

## API Error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

class player_stats:

    def __init__(self, game_date = None, games_list = None):

        self.sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=10)
        self.sess.mount('http://', adapter)

        self.game_date = game_date
        self.games_list = games_list

        self.main()

    def main(self):

        if self.game_date is not None:
            print "Getting list of games for %s"%self.game_date
            print ""
            self.games_list = get_games_list(self.game_date)

        self.fetch_player_stats(self.games_list)

        return None

    def fetch_player_stats(self, games_list):

        print games_list

        ## loop through all games in the list and return player stats
        for i, g in enumerate(games_list):

            print "Getting stats for game: %s (%s/%s)"%(g, i+1, len(games_list))

            game_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
            response = sess.get(game_url, headers=config.request_header)
            game_dict = json.loads(response.text)
            player_json = game_dict['resultSets'][0]
            col_names = player_json['headers']
            player_stats = player_json['rowSet']
            game_df = pd.DataFrame(data = player_stats, columns = col_names)

            if i == 0:
                daily_df = game_df
            else:
                daily_df = daily_df.append(game_df)

            print "Gottem"
            print ""

            if not i % 10:
                upload_stats_to_db(daily_df, 'player_four_factors')
                daily_df.drop(daily_df.index, inplace = True)


        ## upload to db
        upload_stats_to_db(daily_df, 'player_four_factors')

        return None




def upload_stats_to_db(stats, table):

    print ""
    print "Uploading to db..."
    print ""
    conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()
    stats.to_sql(table, con = conn, if_exists = 'append')

    print "Great success!"

    return None

def get_games_list(game_date):

    games_list = []

    return games_list

if __name__ == "__main__":
    player_stats()

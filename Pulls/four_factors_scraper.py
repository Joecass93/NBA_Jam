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

class team_stats():

    def __init__(self, game_date = None):

        self.sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=10)
        self.sess.mount('http://', adapter)

        self.game_date = game_date
        self.games_list = games_list

        self.main()

    def main(self):

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
        upload_stats_to_db(game_ff_df, 'four_factors')

        return None


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

    print games_list

    return games_list

if __name__ == "__main__":
    player_stats()

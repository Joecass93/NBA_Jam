import pandas as pd
import numpy as np
#from algo import four_factors_builder
from datetime import datetime, date, timedelta
from utilities.db_connection_manager import establish_db_connection
from utilities import four_factors_scraper, assets
from pulls import final_score_scraper
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-dt", "--game_date", help = "enter game date as string", type = str, required = False)

flags = parser.parse_args()

if flags.game_date:
    game_date = flags.game_date
else:
    game_date = datetime.now().date().strftime("%Y-%m-%d")

class update_database:

    def __init__(self, gamedate = game_date):

        self.conn = establish_db_connection("sqlalchemy").connect()
        self.gamedate = gamedate

        self.main()

    def main(self):

        self.fetch_data()

        self.upload_data_to_db(self.final_scores, "new_final_scores")
        self.upload_data_to_db(self.stats_df, "new_team_stats")

        print ""
        print "building merged table"
        self.build_merged_table(self.final_scores, self.picks_df)

        print ""

        return None

    def fetch_data(self):

        prev_day = datetime.strptime(self.gamedate, "%Y-%m-%d").date() - timedelta(days = 1)
        prev_day = prev_day.strftime("%Y-%m-%d")

        print "fetching stats from all games on %s"%prev_day
        self.stats_df = four_factors_scraper.main(prev_day, prev_day)

        print "fetching scores from all games on %s"%prev_day
        dirty_scores = final_score_scraper.get_scores(prev_day)
        self.final_scores = final_score_scraper.format_scores(dirty_scores)

        print "fetching picks from all games on %s"%prev_day
        picks_sql = "SELECT * FROM historical_picks_table WHERE game_date = '%s'"%prev_day
        self.picks_df = pd.read_sql(picks_sql, con = self.conn)

        return None

    def build_merged_table(self, scores, picks):

        scores_cols = ['game_id', 'pts_away', 'pts_home', 'pts_total']
        results = picks.merge(scores[scores_cols], how = 'left', on = ['game_id'])
        results['final_spread'] = results['pts_home'] - results['pts_away']
        results['spread_winner'] = np.where(results['final_spread'] > results['vegas_spread'],
                                            results['away_team'], results['home_team'])
        results['pick'] = results['pick_str'].str.split(' ', 1)[0]
        print results[['away_team', 'home_team', 'vegas_spread', 'final_spread', 'spread_winner', 'pick_str', 'pick']].head()

        return None

    def upload_data_to_db(self, data, table):

        ## make this better later
        #data.to_sql(table, con = self.conn, if_exists = 'append')

        return None

class Model_Builder:

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.main()

    def main(self):

        todays_games = assets.games_daily(self.today)

        print todays_games
        print list(todays_games)


        return None

    def build_weighted_team_stats(self):



        return weighted_team_stats



if __name__ == "__main__":
    Model_Builder()
    # conn = establish_db_connection('sqlalchemy').connect()
    # scores_sql = "SELECT * FROM historical_scores_table WHERE game_id LIKE '%s'"%('002180%%')
    # picks_sql = "SELECT * FROM historical_picks_table WHERE game_id LIKE '%s'"%('002180%%')
    # scores = pd.read_sql(scores_sql, con = conn)
    # picks = pd.read_sql(picks_sql, con = conn)
    # update_database().build_merged_table(scores, picks)

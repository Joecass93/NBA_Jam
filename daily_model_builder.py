import pandas as pd
import numpy as np
#from algo import four_factors_builder
from datetime import datetime, date, timedelta
from utilities.db_connection_manager import establish_db_connection
from utilities import four_factors_scraper
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
        self.build_merged_table(self.final_scores, self.stats_df, self.picks_df)

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
        picks_sql = "SELECT * FROM historical_picks_table WHERE game_date = %s"%prev_day
        self.picks_df = pd.read_sql(picks_sql, con = self.conn)

        return None

    def build_merged_table(self, stats, scores, picks):

        print stats.head()
        print scores.head()
        print picks.head()

        return None

    def upload_data_to_db(self, data, table):

        ## make this better later
        data.to_sql(table, con = self.conn, if_exists = 'append')

        return None


if __name__ == "__main__":
    update_database()

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from utilities.db_connection_manager import establish_db_connection
from utilities import assets, result_calculator, config
from pulls.final_score_scraper import get_scores, format_scores
from argparse import ArgumentParser
import requests
import json

parser = ArgumentParser()
parser.add_argument("-dt", "--game_date", help = "enter game date as string", type = str, required = False)

flags = parser.parse_args()

if flags.game_date:
    game_date = flags.game_date
else:
    game_date = datetime.now().date().strftime("%Y-%m-%d")

## API Error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

class MasterUpdate():

    def __init__(self, gamedate = game_date):

        self.conn = establish_db_connection('sqlalchemy').connect()
        self.gamedate = gamedate

        self.today = datetime.now().date().strftime('%Y-%m-%d')
        self.prev_day = (datetime.now().date() - timedelta(days = 1)).strftime('%Y-%m-%d')

        print "Getting list of games for %s"%self.prev_day
        print ""
        self.games_list = get_games_list(self.prev_day)

        self._fetch_game_stats()
        self._fetch_final_scores()

        self._update_db()


    def _fetch_game_stats(self):

        for i, g in enumerate(self.games_list):
            print "Getting stats for game: %s (%s/%s)"%(g, i+1, len(self.games_list))

            game_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
            response = sess.get(game_url, headers=config.request_header)
            game_dict = json.loads(response.text)
            player_json = game_dict['resultSets'][0]
            team_json = game_dict['resultSets'][1]
            pcol_names = player_json['headers']
            tcol_names = team_json['headers']
            player_stats = player_json['rowSet']
            team_stats = team_json['rowSet']
            pgame_df = pd.DataFrame(data = player_stats, columns = pcol_names)
            tgame_df = pd.DataFrame(data = team_stats, columns = tcol_names)

            print " -> Gottem"

            if i == 0:
                self.players_df = pgame_df
                self.teams_df = tgame_df
            else:
                self.players_df = self.players_df.append(pgame_df)
                self.teams_df = self.teams_df.append(tgame_df)

    def _fetch_final_scores(self):

        raw_scores = get_scores(self.prev_day)

        self.scores_df = format_scores(raw_scores)


    def _update_db(self):

        for x in ['players_df', 'teams_df', 'scores_df']:
            tbl = 'self.%s'%x
            print tbl
            _tbl = eval(tbl)

            print "Uploading data to %s"%x
            _tbl.to_sql(x, con = self.conn)


def get_games_list(game_date):

    games_df = assets.games_daily(game_date)

    games_list = games_df['GAME_ID'].tolist()

    return games_list

if __name__ == "__main__":
    MasterUpdate()

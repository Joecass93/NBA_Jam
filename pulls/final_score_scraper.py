import pandas as pd
import numpy as np
from os.path import expanduser
from datetime import datetime, date, timedelta
import json, requests, sys
from argparse import ArgumentParser
sys.path.insert(0,'%s/projects/NBA_Jam/'%expanduser('~'))
from utilities.assets import range_all_dates
from utilities.config import teams, spread_teams, request_header
from utilities.db_connection_manager import establish_db_connection

class FetchResults():

    def __init__(self, start, end):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.dates = range_all_dates(start, end)
        self.clean_cols = ['game_date', 'game_id', 'away_id', 'away_team', 'home_id', 'home_team',
                           'pts_away', 'pts_home', 'pt_diff_away', 'pts_total', 'win_side', 'win_id']
        self.clean_scores = pd.DataFrame(columns = self.clean_cols)

        self._fetch_raw_scores()

    def _fetch_raw_scores(self):
        for d in self.dates:
            self._get_scores(d)
            self._format_scores()
            self._upload_to_db()


    def _get_scores(self, date):
        url_d = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%Y")
        scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%url_d
        response = requests.get(scoreboard_url, headers=request_header)
        data = json.loads(response.text)
        cleaner = data['resultSets'][1]
        col_names = cleaner['headers']

        scoreboard_len = len(cleaner['rowSet'])
        games_today = []
        for x in range(0,scoreboard_len):
            games_today.append(cleaner['rowSet'][x])

        self.scores = pd.DataFrame(games_today, columns = col_names)

    def _format_scores(self):
        df = self.scores.copy()
        _dict = {}
        for g in df['GAME_ID'].unique():
            curr_game = df[df['GAME_ID'] == g][['GAME_DATE_EST', 'GAME_SEQUENCE','GAME_ID','TEAM_ID','TEAM_NAME', 'PTS']].copy()
            curr_game.insert(5, 'SIDE', ['away', 'home'])

            game_a = curr_game[curr_game['SIDE'] == 'away'].copy()
            game_h = curr_game[curr_game['SIDE'] == 'home'].copy()
            pt_diff = game_a['PTS'].item() - game_h['PTS'].item()
            pt_total = game_a['PTS'].item() + game_h['PTS'].item()
            win_side = ('away' if pt_diff > 0 else "home")
            win_id = (game_a['TEAM_ID'].item() if pt_diff > 0 else game_h['TEAM_ID'].item())

            _dict = {'game_date': game_a['GAME_DATE_EST'].item().encode('utf-8').split("T", 1)[0],
                     'game_id': g, 'away_id': game_a['TEAM_ID'].item(),
                     'away_team': game_a['TEAM_NAME'].item(),
                     'home_id': game_h['TEAM_ID'].item(),
                     'home_team': game_h['TEAM_NAME'].item(),
                     'pts_away': game_a['PTS'].item(),
                     'pts_home': game_h['PTS'].item(),
                     'pt_diff_away': pt_diff,
                     'pts_total': pt_total,
                     'win_side': win_side,
                     'win_id': win_id,
                     }

            self.clean_scores = self.clean_scores.append(_dict, ignore_index = True)

        self._determine_b2b()

    def _determine_b2b(self):
        df = self.clean_scores.copy()

        prev_date = (datetime.strptime(self.clean_scores['game_date'].max(), "%Y-%m-%d") - timedelta(1)).date()
        prev_sql = "SELECT game_date, away_team, home_team FROM final_scores WHERE game_date = '%s'"%(prev_date)
        prev_data = pd.read_sql(prev_sql, con = self.conn)
        prev_teams = [a for a in prev_data['away_team']]
        for h in prev_data['home_team']:
            prev_teams.append(h)

        df['b2b_away'] = np.where(df['away_team'].isin(prev_teams), "Yes", "No")
        df['b2b_home'] = np.where(df['home_team'].isin(prev_teams), "Yes", "No")

        self.clean_scores = df.copy()

    def _upload_to_db(self):
        self.clean_scores.to_sql('final_scores', con = self.conn, if_exists = 'append', index = False)

parser = ArgumentParser()
parser.add_argument("-s", "--start_date", help="date to start pulling final scores data from: ex. '2017-11-01'", type=str, required=False)
parser.add_argument("-e", "--end_date", help = "date to end pulling final scores data from: ex. '2017-11-01'", type=str, required=False)

flags = parser.parse_args()
sdate = (flags.start_date if flags.start_date else datetime.now().strftime("%Y-%m-%d"))
edate = (flags.end_date if flags.end_date else sdate)

if __name__ == "__main__":
    FetchResults(start = sdate, end = edate)

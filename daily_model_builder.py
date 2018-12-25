import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from utilities.db_connection_manager import establish_db_connection
from utilities import assets, result_calculator, config, four_factors_scraper, aggregate_stats_to_date
from pulls import final_score_scraper
from pulls import spreads_scraper as ss
from algo_master import RunAlgo
import requests, json

pd.options.mode.chained_assignment = None

## API Error handlings
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

class MasterUpdate():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()

        self.today = datetime.now().strftime('%Y-%m-%d')
        self.prev_day = (datetime.strptime(self.today, '%Y-%m-%d').date() - timedelta(days = 1)).strftime('%Y-%m-%d')
        self.games_list = get_games_list(self.prev_day)

        self._fetch_game_stats()
        self._fetch_final_scores()
        self._fetch_spreads()
        self._calculate_results()
        self._update_db()

        aggregate_stats_to_date(self.prev_day, self.prev_day)

    def _fetch_game_stats(self):
        self.player_stats, self.team_stats = four_factors_scraper._fetch_game_stats(self.prev_day)

    def _fetch_final_scores(self):
        final_score_scraper()
        scores_sql = "SELECT * FROM final_scores WHERE game_date = '%s'"%self.prev_day
        self.scores_df = pd.read_sql(scores_sql, con = self.conn)

    def _fetch_spreads(self):
        spreads_df = ss.main(self.today)
        spreads_df.drop(columns = ['time'], inplace = True)
        spreads_df['date'] = spreads_df['date'].str[0:4] + "-" + spreads_df['date'].str[4:6] + "-" + spreads_df['date'].str[6:8]
        spreads_df['bovada_line'] = np.where((spreads_df['bovada_line'] == 'PK-11') | (spreads_df['bovada_line'] == 'PK-10'),
                                            "0", spreads_df['bovada_line'])
        self.spreads_df = spreads_df

    def _calculate_results(self):
        prev_picks_sql = "SELECT * FROM historical_picks WHERE game_date = '%s'"%self.prev_day
        self.prev_picks = pd.read_sql(prev_picks_sql, con = self.conn)
        self.results = result_calculator.determine_results(self.scores_df, self.prev_picks)

    def _update_db(self):
        schema = {'four_factors_player': self.player_stats,
                  'four_factors_team': self.team_stats,
                  'final_scores': self.scores_df,
                  'spreads': self.spreads_df,
                  'results_table': self.results}

        for tbl, data in schema.iteritems():
            print "Uploading data to %s"%tbl
            data.to_sql(tbl, con = self.conn, if_exists = 'append', index = False)

class BuildPredictions():

    def __init__(self, gamedate = None):
        self.conn = establish_db_connection('sqlalchemy').connect()
        if gamedate is not None:
            self.gamedate = gamedate
        else:
            self.gamedate = datetime.now().date().strftime('%Y-%m-%d')

        self.games_df = assets.games_daily(self.gamedate)
        self._fetch_agg_stats()
        self._build_predictions()
        self._merge_with_spreads()
        self._clean_merged_data()

        print self.merged_df
        # self.merged_df.to_sql('daily_picks', con = self.conn, if_exists = 'replace', index = False)
        # self.merged_df.to_sql('historical_picks', con = self.conn, if_exists = 'append', index = False)

    def _fetch_agg_stats(self):
        stats_list = ['TEAM_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT',
                      'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']

        games_dict = {}
        for index, row in self.games_df.iterrows():
            games_dict[row['GAME_ID']] = {'home': row['HOME_TEAM_ID'], 'away': row['VISITOR_TEAM_ID']}

        stats_cols = list(stats_list)
        stats_cols.append('GAME_ID')
        stats_cols.append('SIDE')
        games_data = pd.DataFrame(columns = stats_cols)

        for g, t in games_dict.iteritems():
            home_stats_str = "SELECT * FROM four_factors_team WHERE TEAM_ID = '%s' AND GAME_ID LIKE '%s' AND GAME_ID < '%s'"%(t.get('home'), g[0:6] + "%%", g)
            away_stats_str = "SELECT * FROM four_factors_team WHERE TEAM_ID = '%s' AND GAME_ID LIKE '%s' AND GAME_ID < '%s'"%(t.get('away'), g[0:6] + "%%", g)
            for x in ['home_stats_str', 'away_stats_str']:
                _eval = eval(x)
                stats_df = pd.read_sql(_eval, con = self.conn)[stats_list]
                agg_stats = stats_df.groupby(by = ['TEAM_ID'], as_index = False).mean()
                agg_stats['GAME_ID'] = g
                agg_stats['SIDE'] = x[0:4]
                games_data = games_data.append(agg_stats)

        self.agg_stats = games_data

    def _build_predictions(self):
        self.preds_df = pd.DataFrame(columns = ['game_id', 'away_team_id', 'home_team_id', 'pred_spread'])
        stats_list = ['SIDE', 'TEAM_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT',
                      'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']

        for g in self.agg_stats['GAME_ID'].unique():
            curr_game = self.agg_stats[self.agg_stats['GAME_ID'] == g]

            pred_spread = RunAlgo(curr_game[stats_list], "standard_algo")._standard_algo()

            away_id = curr_game[(curr_game['GAME_ID'] == g) & (curr_game['SIDE'] == 'away')]['TEAM_ID'].item()
            home_id = curr_game[(curr_game['GAME_ID'] == g) & (curr_game['SIDE'] == 'home')]['TEAM_ID'].item()
            curr_game_df = pd.DataFrame(data = {'game_id': [g],
                                                'away_team_id': away_id,
                                                'home_team_id': home_id,
                                                'pred_spread': [pred_spread]})

            self.preds_df = self.preds_df.append(curr_game_df)

    def _merge_with_spreads(self):
        spreads_str = "SELECT * FROM spreads WHERE date = '%s'"%self.gamedate
        spreads_df = pd.read_sql(spreads_str, con = self.conn)

        for i in ['home_team_id', 'away_team_id']:
            self.preds_df[i] = self.preds_df[i].astype(str)

        spreads_df = spreads_df[['date', 'away_team_id', 'home_team_id', 'bovada_line']]
        self.merged_df = self.preds_df.merge(spreads_df, how = 'left', on = ['home_team_id', 'away_team_id'])

    def _clean_merged_data(self):
        raw_df = self.merged_df.rename(index = str, columns = {'away_team_id':'away_id',
                                                                       'home_team_id': 'home_id',
                                                                       'date': 'game_date',
                                                                       'bovada_line': 'vegas_spread'})

        raw_df['away_team'] = raw_df['away_id'].apply(get_team_from_id)
        raw_df['home_team'] = raw_df['home_id'].apply(get_team_from_id)

        raw_df['vegas_spread_str'] = raw_df.apply(reformat_vegas_spread, axis = 1)
        raw_df['pred_spread_str'] = raw_df.apply(reformat_pred_spread, axis = 1)
        raw_df['pred_spread_str'] = np.where(raw_df['pred_spread_str'].str.contains("-"),
                                             raw_df['pred_spread_str'],
                                             raw_df['pred_spread_str'].str.replace("(", "(+"))
        raw_df['vegas_spread'] = raw_df['vegas_spread'].astype(float)
        raw_df['pred_spread'] = raw_df['pred_spread'].round(2)

        raw_df['pt_diff'] = raw_df['vegas_spread'] - raw_df['pred_spread']
        raw_df['abs_pt_diff'] = raw_df['pt_diff'].abs()
        raw_df['best_bet'] = np.where(raw_df['abs_pt_diff'] > 3.50, 'Y', 'N')
        gdate = raw_df['game_date'].max()
        raw_df['rank'] = (raw_df.groupby('game_date')['abs_pt_diff'].rank(ascending = False)).astype(int)
        raw_df.drop(columns = ['abs_pt_diff'], inplace = True)
        raw_df.sort_values(by = ['rank'], inplace = True)

        raw_df['game_date'] = gdate
        self.merged_df = raw_df
        self._make_pick()

    def _make_pick(self):
        df = self.merged_df
        df['pick_team'] = np.where(df['vegas_spread'] < df['pred_spread'],
                                   df['home_team'],
                                   df['away_team'])
        df['spread_str'] = df['vegas_spread'].astype(str)
        df['spread_str'] = np.where(df['pick_team'] == df['away_team'],
                                    np.where(df['spread_str'].str.contains("-"),
                                             df['spread_str'],
                                             "+" + df['spread_str']),
                                    np.where(df['spread_str'].str.contains("-"),
                                             df['spread_str'].str.replace("-", "+"),
                                             "-" + df['spread_str']))

        df['pick_str'] = df['pick_team'] + " (" + df['spread_str'] + ")"
        df.drop(columns = ['pick_team', 'spread_str'], inplace = True)
        self.merged_df = df

def reformat_vegas_spread(row):
    return "%s (%s)"%(row['away_team'],row['vegas_spread'])

def reformat_pred_spread(row):
    row['pred_spread'] = str(round(row['pred_spread'], 1))
    return "%s (%s)"%(row['away_team'], row['pred_spread'])

def get_team_from_id(team_id):
    team_abbrv = config.teams['nba_teams'].get(team_id)
    return team_abbrv

def get_games_list(game_date):
    games_df = assets.games_daily(game_date)
    games_list = games_df['GAME_ID'].tolist()
    return games_list

if __name__ == "__main__":
    # MasterUpdate()
    BuildPredictions()

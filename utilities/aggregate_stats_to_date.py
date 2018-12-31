import pandas as pd
from datetime import datetime, date
from assets import upload_to_db, range_all_dates, list_games
from config import teams
from db_connection_manager import establish_db_connection

class AggregateTeamStats():

    def __init__(self, *dates):
        self._config(dates)
        for id, team in self.team_dict.iteritems():
            print "Aggregating stats for %s"%team
            self._fetch_raw_stats(id)
            print "Uploaded aggregate stats for %s to db"%team
            print ""

    def _fetch_raw_stats(self, id):
        self.games_played = list_games(id, self.end_date, self.start_date)
        if len(self.games_played) > 1:
            sql_str = 'SELECT %s FROM four_factors_team WHERE TEAM_ID = %s and GAME_ID IN ("%s")'%(", ".join(self.sql_fields), id, '", "'.join(self.games_played))
            self.raw_stats = pd.read_sql(sql_str, con = self.conn)

            self._aggregate_stats()

    def _aggregate_stats(self):
        agg_stats = pd.DataFrame(columns = self.agg_fields)
        for i, g in enumerate(self.games_played):
            if i != 0:
                rolling_games = self.raw_stats[self.raw_stats['GAME_ID'] < g].copy()
                rolling_games.drop(['GAME_ID'], axis = 1, inplace = True)
                rolling_avg = rolling_games.groupby(['TEAM_ID'], as_index = False).mean()
                rolling_avg['as_of'] = g
                agg_stats = agg_stats.append(rolling_avg)

        self._upload_to_db(agg_stats)

    def _upload_to_db(self, stats):
        stats.to_sql('four_factors_thru', con = self.conn, if_exists = 'append', index = False)

    def _config(self, *dates):
        self.conn = establish_db_connection('sqlalchemy').connect()
        for i, d in enumerate(dates):
            self.start_date = d[0]
            self.end_date = d[1]
        self.sql_fields = ['TEAM_ID', 'GAME_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 'OPP_EFG_PCT',
                           'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']
        self.agg_fields =  ['TEAM_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 'OPP_EFG_PCT',
                           'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT', 'as_of']
        self.team_dict = teams.get('nba_teams')

class AggregatePlayerStats():

    def __init__(self, *dates):
        self._config(dates)
        for id, team in self.team_dict.iteritems():
            print "Aggregating player stats for %s"%team
            self._fetch_raw_stats(id)
            print "Uploaded aggregate stats for %s to db"%team
            print ""

    def _fetch_raw_stats(self, id):
        self.games_played = list_games(id, self.end_date, self.start_date)
        if len(self.games_played) > 1:
            sql_str = 'SELECT %s FROM four_factors_player WHERE TEAM_ID = %s and GAME_ID IN ("%s")'%(", ".join(self.sql_fields), id, '", "'.join(self.games_played))
            self.raw_stats = pd.read_sql(sql_str, con = self.conn)

            self._aggregate_stats()

    def _aggregate_stats(self):
        df = self.raw_stats.copy()
        for p in df['PLAYER_ID'].unique():
            p_stats = df[df['PLAYER_ID'] == p].copy()
            self._calc_player_agg(p_stats)

    def _calc_player_agg(self, stats):
        mp = float(stats['MIN']).sum()
        print stats['PLAYER_ID']
        print mp


    def _config(self, *dates):
        self.conn = establish_db_connection('sqlalchemy').connect()
        for i, d in enumerate(dates):
            self.start_date = d[0]
            self.end_date = d[1]

        self.sql_fields = ['TEAM_ID', 'GAME_ID', 'PLAYER_ID', 'MIN', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT',
                           'OREB_PCT', 'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']
        self.team_dict = teams.get('nba_teams')

if __name__ == "__main__":
    # AggregateTeamStats('2018-12-21', '2018-12-23')
    AggregatePlayerStats('2018-12-15', '2018-12-23')

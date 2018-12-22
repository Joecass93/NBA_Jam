import pandas as pd
from datetime import datetime, date
from assets import upload_to_db, range_all_dates, list_games
from config import teams
from db_connection_manager import establish_db_connection

class AggregateTeamStats():

    def __init__(self, start_date, end_date):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.start_date = start_date
        self.end_date = end_date

        self.team_dict = teams.get('nba_teams')
        for id, team in self.team_dict.iteritems():
            print "Aggregating stats for %s"%team
            self._fetch_raw_stats(id)
            print "Uploaded aggregate stats for %s to db"%team
            print ""


    def _fetch_raw_stats(self, id):
        games_played = list_games(id, self.end_date, self.start_date)
        print games_played
        sql_fields = ['TEAM_ID', 'GAME_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 'OPP_EFG_PCT',
                      'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']
        sql_str = 'SELECT %s FROM four_factors_team WHERE TEAM_ID = %s and GAME_ID IN ("%s")'%(", ".join(sql_fields), id, '", "'.join(games_played))

        raw_stats = pd.read_sql(sql_str, con = self.conn)
        agg_cols = sql_fields.append("as_of")
        agg_stats = pd.DataFrame(columns = agg_cols)
        for i, g in enumerate(games_played):
            if i != 0:
                rolling_games = raw_stats[raw_stats['GAME_ID'] < g].copy()
                rolling_games.drop(['GAME_ID'], axis = 1, inplace = True)
                rolling_avg = rolling_games.groupby(['TEAM_ID'], as_index = False).mean()

                rolling_avg['as_of'] = g
                agg_stats = agg_stats.append(rolling_avg)

                self._upload_to_db(agg_stats)


    def _upload_to_db(self, stats):
        stats.to_sql('four_factors_thru', con = self.conn, if_exists = 'append', index = False)


if __name__ == "__main__":
    AggregateTeamStats('2018-10-20', '2018-10-31')

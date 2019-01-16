import MySQLdb
from os.path import expanduser
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import sys
from utilities.db_connection_manager import establish_db_connection

class PlayerStatsTransform():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()

    def _fetch_raw_stats(self):
        player_sql = "SELECT * FROM "


class PlayerStatsPlayground():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.games = ['', '', '', '', '', '']
        self.stats = ['EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 'OPP_EFG_PCT',
                      'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']
        self._fetch_stats()
        self._weight_player_stats()
        print self._team[self.stats[:] + ['TEAM_ID']]
        print self._weighted

    def _fetch_stats(self):
        team_sql = "SELECT * FROM four_factors_team WHERE game_id = %s"%('"0021800524"')
        player_sql = "SELECT * FROM four_factors_player WHERE game_id = %s"%('"0021800524"')
        self._team = pd.read_sql(team_sql, con = self.conn)
        _player = pd.read_sql(player_sql, con = self.conn)
        self._player = _player[~(_player['MIN'].isna())]
        self._player['MIN'] = self._player['MIN'].apply(convert_minsec_to_dec)

    def _weight_player_stats(self):
        self._weighted = pd.DataFrame(columns = (self.stats[:] + ['TEAM_ID']))
        for team in self._player['TEAM_ID'].unique():
            _weighted = {}
            df = self._player[self._player['TEAM_ID'] == team].copy()
            minutes = df['MIN'].sum()
            for stat in self.stats:
                df[stat] = df[stat] * df['MIN']
                _weighted[stat] = float(df[stat].sum()) / minutes

            _weighted = pd.DataFrame(data = _weighted, index = [0])
            _weighted['TEAM_ID'] = team
            self._weighted = self._weighted.append(_weighted)

def convert_minsec_to_dec(minsec):
    minsec = datetime.strptime(minsec, "%M:%S")
    min = float(minsec.minute)
    sec = float(minsec.second)
    return (min + float(sec/60))


if __name__ == "__main__":
    PlayerStatsPlayground()

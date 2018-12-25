import pandas as pd
import numpy as  np
from datetime import datetime, date, timedelta
from utilities.db_connection_manager import establish_db_connection

class RunAlgo():

    def __init__(self, stats, model):
        self.conn = establish_db_connection('sqlalchemy').connect()

        self.stats = stats
        _model = eval("self._%s"%model)
        _model()

    def _standard_algo(self):
        df = self.stats.copy()

        temp_cols = ['TEAM_ID','efg', 'tov', 'orb', 'ftfga']
        df['efg'] = (df['EFG_PCT'] - df['OPP_EFG_PCT'])*100
        df['tov'] = (df['TM_TOV_PCT'] - df['OPP_TOV_PCT'])*100
        df['orb'] = ((100*df['OREB_PCT']) - (100*df['OPP_OREB_PCT']))
        df['ftfga'] = (df['FTA_RATE'] - df['OPP_FTA_RATE'])*100

        away_temp = df[df['SIDE'] == 'away'][temp_cols]
        home_temp = df[df['SIDE'] == 'home'][temp_cols]
        weights_dict = {'efg': 0.40, 'tov': 0.25, 'orb': 0.20, 'ftfga': 0.15}

        algo_dict = {}
        for s, w in weights_dict.iteritems():
            algo_dict[s] = (home_temp[s].item() - away_temp[s].item()) * w

        return round((sum(algo_dict.values()) * 2) + 2.47, 3)

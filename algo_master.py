import pandas as pd
import numpy as  np
from datetime import datetime, date, timedelta
from utilities.db_connection_manager import establish_db_connection

class RunAlgo():

    def __init__(self, stats):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.stats = stats

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

    def _linear_regression_algo(self):
        self.stats['id'] = 1
        self.stats['b2b'] = np.where(self.stats['b2b'] == 'Yes', 1, 0)
        home = self.stats[self.stats['SIDE'] == 'home'].copy()
        away = self.stats[self.stats['SIDE'] == 'away'].copy()

        df = home.merge(away, how = 'left', on = 'id', suffixes = ['_home', '_away'])

        intercept = 8.0185
        weights = {'EFG_PCT_home': 105.6629,
                   'TM_TOV_PCT_home': -95.0748,
                   'OREB_PCT_home': 38.8688,
                   'FTA_RATE_home': 19.4733,
                   'OPP_EFG_PCT_home': -78.8755,
                   'OPP_TOV_PCT_home': 82.6883,
                   'OPP_OREB_PCT_home': -40.1310,
                   'OPP_FTA_RATE_home': -10.9471,
                   'EFG_PCT_away': -101.9287,
                   'TM_TOV_PCT_away': 43.8020,
                   'OREB_PCT_away': -27.2638,
                   'FTA_RATE_away': -14.1483,
                   'OPP_EFG_PCT_away': 66.9014,
                   'OPP_TOV_PCT_away': -67.9887,
                   'OPP_OREB_PCT_away': 33.3448,
                   'OPP_FTA_RATE_away': 15.9683,
                   'b2b_home': -1.3703,
                   'b2b_away': 1.7195,
                   }
        pred_spread = intercept
        for stat, weight in weights.iteritems():
            pred_spread += weight * df[stat].item()

        return pred_spread

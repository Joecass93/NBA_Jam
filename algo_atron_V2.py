import pandas as pd
from pandas import *
from datetime import datetime, date
import numpy as np
from utilities.db_connection_manager import establish_db_connection
from sklearn import linear_model


class algo_atron(object):

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()

    def run_algorithm(self):

        raw_data = self.get_algo_data()
        algo_data = self.algo_data_cleaner(raw_data)
        self.upload_merged_data(algo_data)

        return algo_data

    def get_algo_data(self):

        db_tables = ['spreads', 'flatten_final_scores', 'four_factors_thru']
        raw_data = {}

        for t in db_tables:
            sql_str = "SELECT * FROM %s"%t;
            df = pd.read_sql(sql_str, con = self.conn)
            raw_data[t] = df

        return raw_data

    def algo_data_cleaner(self, raw_data):


        spreads_w_scores = self.clean_spreads_data(raw_data['spreads'], raw_data['flatten_final_scores'])
        algo_data = self.merge_stats_w_info(raw_data['four_factors_thru'], spreads_w_scores)

        return algo_data

    def clean_spreads_data(self, spreads_data, schedule):

        ## limit cols for schedule
        schedule_cols = ['game_date', 'game_id', 'away_team_id', 'home_team_id', 'away_pts', 'home_pts', 'home_pt_diff']
        schedule = schedule[schedule_cols]
        ## merge game id into spread data
        spreads_data['game_date'] = pd.to_datetime(spreads_data['date']).dt.date
        spreads = spreads_data.merge(schedule, how = 'left', on = ['game_date',
                                                                   'away_team_id',
                                                                   'home_team_id'])

        ## clean up spreads data (only use bovada lines for now...)
        spreads_clean_cols = ['game_id', 'date', 'team', 'away_team_id',
                              'opp_team', 'home_team_id', 'away_pts', 'home_pts',
                              'home_pt_diff', 'bovada_line']

        spreads = spreads[spreads_clean_cols]
        spreads = spreads.rename(index = str, columns = {'team':'away_team',
                                                        'bovada_line':'away_spread'})

        ## remove all star games etc..
        spreads = spreads[spreads['away_team_id'].notna()]
        ## remove games that were postponed from spread data
        spreads = spreads[spreads['game_id'].notna()]

        ## rounding
        spreads['away_pts'] = spreads.away_pts.astype(int)
        spreads['home_pts'] = spreads.home_pts.astype(int)
        spreads['home_pt_diff'] = spreads.home_pt_diff.astype(int)

        return spreads

    def merge_stats_w_info(self, stats, game_info):

        ## clean column names
        merged_cols = list(game_info)
        merged_cols_delete = []
        for m in merged_cols:
            m = m + "_y"
            merged_cols_delete.append(m)

        stats_cols = ["away_efg", 'away_ftr', 'away_tov', 'away_oreb', 'away_opp_efg',
                      'away_opp_ftr', 'away_opp_tov', 'away_opp_oreb','home_efg',
                      'home_ftr', 'home_tov', 'home_oreb', 'home_opp_efg',
                      'home_opp_ftr', 'home_opp_tov', "home_opp_oreb"]

        for s in stats_cols:
            merged_cols.append(s)

        # first merge in all of the away team stats
        stats['TEAM_ID'] = stats['TEAM_ID'].astype(str)
        away_merged = game_info.merge(stats, how = 'left',
                                      left_on = ['game_id', 'away_team_id'],
                                      right_on = ['GAME_ID', 'TEAM_ID'])

        print away_merged.head()
        print list(away_merged)
        merged_data = away_merged.merge(stats, how = 'left',
                                        left_on = ['game_id', 'home_team_id'],
                                        right_on = ['GAME_ID', 'TEAM_ID'])
        print merged_data.head()
        print list(merged_data)
        print merged_data[merged_data['TEAM_ID_y'].isna()]
        # print list(merged_data)
        #
        # merged_data = merged_data.drop(columns = ['TEAM_x', 'TEAM_y', 'index_x', 'index_y',
        #                                             'GAME_ID_x', 'GAME_ID_y', 'TEAM_ID_x',
        #                                             'TEAM_ID_y'])
        # merged_data = merged_data.drop(columns = merged_cols_delete)
        #
        # merged_data.columns = merged_cols
        # print merged_data.head()

        return None


    def upload_merged_data(self, merged_data):

        merged_data.to_sql('merged_data', con = self.conn, if_exists = 'append')

        return None

if __name__ == "__main__":
    algo_atron().run_algorithm()

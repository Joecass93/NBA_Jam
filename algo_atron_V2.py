import pandas as pd
from datetime import datetime, date
import numpy as np
from utilities.db_connection_manager import establish_db_connection
from sklearn import linear_model


class algo_atron(object):

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()

    def run_algorithm(self):

        algo_data = self.get_algo_data()

        clean_data = self.clean_algo_data(algo_data)

        return clean_data

    def get_algo_data(self):

        db_tables = ['games', 'spreads', 'final_scores', 'four_factors_thru']
        algo_data = {}

        for t in db_tables:
            sql_str = "SELECT * FROM %s"%t;
            df = pd.read_sql(sql_str, con = self.conn)
            algo_data[t] = df

        return algo_data

    def clean_algo_data(self, algo_data):

        ## merge game id into spread data
        algo_data['spreads']['date'] = pd.to_datetime(algo_data['spreads']['date'])
        algo_data['spreads']['date'] = algo_data['spreads']['date'].dt.date
        spreads = algo_data['spreads'].merge(algo_data['games'], how = 'left', left_on = ['date', 'away_team_id', 'home_team_id'], right_on = ['game_date', 'away_id', 'home_id'])
        spreads = spreads.drop(columns = ['away_team_id', 'home_team_id'])

        ##


        return None

if __name__ == "__main__":
    algo_atron().run_algorithm()

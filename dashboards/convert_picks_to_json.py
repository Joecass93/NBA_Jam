import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import sys
from os.path import expanduser
sys.path.insert(0, "%s/projects/NBA_Jam/"%(expanduser("~")))
from utilities import db_connection_manager
import json

today = datetime.now().date().strftime("%Y-%m-%d")

class convert_daily_picks():

    def __init__(self):
        self.conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

        self.main()

    def main(self):

        print "getting daily picks table from db..."
        self.daily_picks_df = import_sql_table('daily_picks', "", self.conn)

        print "cleaning table and reformatting as json object..."
        daily_picks_json = self.reformat_daily_picks()

        export_json_data(daily_picks_json, "/Users/joe/projects/nba_picks_daily.json")

        print "daily picks successfully converted to json object, now sending to Jamal..."
        # send_to_jamal(daily_picks_json, "today_picks")

        return None

    def reformat_daily_picks(self):

        daily_picks_dict = {}
        for index, row in self.daily_picks_df.iterrows():
            game_dict = {}
            row = self.daily_picks_df[index:index + 1]
            for c in list(self.daily_picks_df)[2:]:
                game_dict[c] = row.iloc[0][c]

            daily_picks_dict[str(row['game_id'].item())] = game_dict

        ## add date as key for entire dict
        picks_date = self.daily_picks_df['game_date'].max()
        picks_date = picks_date.strftime("%Y-%m-%d")
        daily_picks_dict = {picks_date: daily_picks_dict}

        return daily_picks_dict


class convert_historical_picks():

    def __init__(self):
        self.conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

        self.main()

    def main(self):

        print "getting historical results table from db..."
        self.hist_results_df = import_sql_table('results_table', " WHERE game_date >= '2018-10-16'", self.conn)

        print "cleaning table and reformatting as json object..."
        historical_picks_dict = {}
        for d in self.hist_results_df['game_date'].unique():
            daily_chunk_json = {}
            results_chunk = self.hist_results_df[self.hist_results_df['game_date'] == d]
            daily_chunk_json = self.reformat_hist_results(results_chunk)
            historical_picks_dict[d.strftime("%Y-%m-%d")] = daily_chunk_json

        export_json_data(historical_picks_dict, "/Users/joe/projects/nba_historical_results.json")

        print "historical results successfully converted to json object, now sending to Jamal..."
        # send_to_jamal(historical_results_json, "historical_results")

        return None

    def reformat_hist_results(self, results_chunk):

        daily_picks_dict = {}
        results_chunk.reset_index(drop = True, inplace = True)
        for index, row in results_chunk.iterrows():
            game_dict = {}
            row = results_chunk[index:index + 1]
            for c in list(results_chunk)[2:]:
                game_dict[c] = row.iloc[0][c]

            daily_picks_dict[str(row['game_id'].item())] = game_dict

        return daily_picks_dict


def export_json_data(data, table_name):

    print "writing today's picks dictionary to %s..."%table_name
    with open(table_name, 'w') as outfile:
        json.dump(data, outfile)

    return None

def import_sql_table(table_name, conditions, conn):

    sql_str = "SELECT * FROM %s%s"%(table_name, conditions)
    sql_table = pd.read_sql(sql_str, con = conn)

    return sql_table

# def send_to_jamal(data, type):
#
#
#
#     return None

if __name__ == "__main__":
    convert_historical_picks()

import pandas as pd
import numpy as np
from os.path import expanduser
home_dir = expanduser("~")
import sys
sys.path.insert(0, "%s/projects/NBA_Jam/"%home_dir)
from utilities.db_connection_manager import establish_db_connection

def main():

    conn = establish_db_connection('sqlalchemy').connect()

    raw_preds = pd.read_sql("SELECT * FROM 218_fantasy_projections", con = conn)

    stats_list = ['FGper', 'FTper', '3P', 'PTS', 'TRB', 'AST', 'STL', 'BLK']

    top_10_each_cat = get_top_10_by_stat(raw_preds, stats_list)

    master_rankings = get_master_rankings(raw_preds, stats_list, conn)


    return None

def get_top_10_by_stat(raw_preds, stats_list):

    top_10_dict = {}
    for s in stats_list:
        if s == 'TOV':
            filter_preds = raw_preds[raw_preds['TOV'] > 0.8]
            s_ranked = filter_preds[['Player_name', 'Player_id',s, s + "_rank"]].sort_values(by = [s + "_rank"], ascending = False)
        else:
            s_ranked = raw_preds[['Player_name', 'Player_id',s, s + "_rank"]].sort_values(by = [s + "_rank"])

        print s_ranked.head(10)
        top_10_dict[s] = s_ranked.head(10)


    return top_10_dict

def get_master_rankings(raw_preds, stats_list, conn):

    raw_preds['total_rank'] = 0
    for s in stats_list:
        rank = s + "_rank"
        raw_preds['total_rank'] = raw_preds['total_rank'] + raw_preds[rank]

    master_cols = stats_list[:]
    master_cols.insert(0, 'Player_id')
    master_cols.insert(1, 'Player_name')
    master_cols.insert(2, 'total_rank')
    master_rankings = raw_preds[master_cols]

    master_rankings = master_rankings.sort_values(by = ['total_rank'])

    #master_rankings.to_sql('2018_fantasy_master_rankings', con = conn)


    return None

if __name__ == "__main__":
    main()

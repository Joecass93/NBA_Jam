#import requests
#import ast
#import json
import pandas as pd
#from assets import range_all_dates
from config import teams, seasons, season_sql
import datetime
import numpy as np
from assets import list_games, range_all_dates
#from argparse import ArgumentParser
from os.path import expanduser
import sys
import result_calculator
home_dir = expanduser("~")
syspath = '%s/projects/NBA_Jam/'%home_dir
sys.path.insert(0,syspath)
from pulls import spreads_scraper
from utilities import db_connection_manager
from utilities import flatten_data
from utilities import aggregate_stats_to_date

engine = db_connection_manager.establish_db_connection('sqlalchemy')
conn = engine.connect()

teams_dict = teams['nba_teams']

ff_df = pd.read_sql("SELECT * FROM four_factors WHERE GAME_ID LIKE '002180%%'", con = conn)
print ff_df
#
# final_scores_sql = "SELECT game_id, home_team_id, away_team_id FROM flatten_final_scores WHERE game_id IN (%s)"%("', '".join(games_list))
# final_scores = pd.read_sql(final_scores_sql, con = conn)
# away_dict = dict(zip(final_scores.game_id, final_scores.away_team_id))
# home_dict = dict(zip(final_scores.game_id, final_scores.home_team_id))
#
# print home_dict
#
# for i, v in away_dict.iteritems():
#     aggregate_stats_to_date.aggregate_stats(v, to_gameid = i)
#
# for i, v in home_dict.iteritems():
#     aggregate_stats_to_date.aggregate_stats(v, to_gameid = i)

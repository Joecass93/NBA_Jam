import pandas as pd
import numpy as np
from datetime import datetime, date
from assets import list_games
from config import teams
from db_connection_manager import establish_db_connection

def get_season_agg(team_id, season_num):

    conn = establish_db_connection('sqlalchemy').connect()

    ## get all game_ids for a team in the given season
    
    games_sql = 'SELECT GAME_ID FROM final_scores WHERE TEAM_ID = "%s" and GAME_ID LIKE "%s"'%(team_id, season_num + "0%%")
    games_data = pd.read_sql(games_sql, con = conn)
    games_list = list(games_data['GAME_ID'])

    for g in games_list[1:]:
        aggregate_stats(team_id, to_gameid = g)

    return games_list

def aggregate_stats(team_id, to_date = None, to_gameid = None):

    ## get team name for logging etc..
    team_name = teams['nba_teams'].get(team_id)
    print team_name


    conn = establish_db_connection('sqlalchemy').connect()

    ## First check if the team has a game on the date listed
    if to_gameid:
        print "Aggregating stats for %s from start of season up to game_id: %s...."%(team_name, to_gameid)
        start_id = to_gameid[0:4] + "00001"
        ff_sql = "SELECT * FROM four_factors WHERE TEAM_ID = %s and GAME_ID < %s and GAME_ID > %s"%(team_id, to_gameid, start_id)
        ff_data = pd.read_sql(ff_sql, con = conn)
        curr_game = to_gameid

    else:

        game_today_sql = "SELECT GAME_ID FROM final_scores WHERE GAME_DATE_EST = '%s' AND TEAM_ID = '%s'"%(to_date, team_id)
        game_today = pd.read_sql(game_today_sql, con = conn)

        if len(game_today) > 0:
            print "Aggregating stats for %s from start of season up to %s...."%(team_name, to_date)
            game_today = game_today['GAME_ID'].item()
            games_list, curr_game = list_games(team_id, to_date)
            games_str = "', '".join(games_list)

            ## get records for all games
            ff_sql = "SELECT * FROM four_factors WHERE TEAM_ID = %s AND GAME_ID IN ('%s')"%(team_id, games_str)
            ff_data = pd.read_sql(ff_sql, con = conn)

        else:
            print "No game for %s on %s, please try a new date..."%(team_name, to_date)
            return None



    ## aggregate stats
    #  replace game ids with the id for the current game
    ff_data['GAME_ID'] = curr_game
    agg_stats = ff_data.groupby(by = ['TEAM_ID', 'GAME_ID']).mean().reset_index()

    agg_stats['TEAM'] = team_name

    print "Storing data in four_factors_thru..."
    agg_stats.to_sql('four_factors_thru', con = conn, if_exists = 'append')


    return agg_stats

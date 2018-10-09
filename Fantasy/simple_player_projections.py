import pandas as pd
import numpy as np
from os.path import expanduser
home_dir = expanduser("~")
import sys
sys.path.insert(0, "%s/projects/NBA_Jam/"%home_dir)
from utilities.db_connection_manager import establish_db_connection


## main function to build player stats projections for fantasy
def main(season_id):

    conn = establish_db_connection('sqlalchemy').connect()
    prev_seasons = [str(int(season_id)), str(int(season_id) - 1), str(int(season_id) - 2)]

    historic_data = get_prev_player_data(conn, prev_seasons)

    ## get list of active players for the selected season
    active_players = (historic_data['217'])['Player_id'].tolist()

    season_projections = build_simple_season_projections(active_players, historic_data)

    print "uploading player projections..."
    re_conn = establish_db_connection('sqlalchemy').connect()
    season_projections.to_sql('218_fantasy_projections', con = re_conn, if_exists = 'replace', index = False)

    return None

def get_prev_player_data(conn, season_id = None, game_id = None, game_date = None):

    historic_dict = {}
    if season_id:

        if type(season_id) == list:
            pass
        else:
            season_id = [season_id]

        ## get data for the selected season(s) and build dictionary
        for s in season_id:
            season_data = pd.read_sql("player_season_stats_%s"%s, con = conn)
            historic_dict[s] = season_data

    elif game_id:

        if type(game_id) == list:
            pass
        else:
            game_id = [game_id]
        ## get data for the selected game(s) and build dictionary

    elif game_date: ## need some kind of date to string formatting here

        if type(game_date) == list:
            pass
        else:
            game_date = [game_date]

        ## get data for the selected date(s) and build dictionary


    return historic_dict

def build_simple_season_projections(active_players, historic_data):

    ## get data for active players from the last 3 seasons
    # last season
    _1_seasons_ago = historic_data['217']
    # 2 seasons ago
    _2_seasons_ago = historic_data['216']
    _2_seasons_ago = _2_seasons_ago[_2_seasons_ago['Player_id'].isin(active_players)]
    # 3 seasons ago
    _3_seasons_ago = historic_data['215']
    _3_seasons_ago = _3_seasons_ago[_3_seasons_ago['Player_id'].isin(active_players)]


    ## loop through active players, get and weight stats for the previous seasons and
    ## build a new dataframe
    agg_dict = {'FGper':'mean', 'FTper':'mean', '3P':'sum', 'PTS':'sum', 'TRB':'sum',
                'AST':'sum', 'STL':'sum', 'BLK':'sum', 'TOV':'sum', 'G':'sum', 'MP': 'sum'}
    stats_list = agg_dict.keys()
    convert_stats = stats_list[:]
    convert_stats.remove('FGper')
    convert_stats.remove('FTper')
    convert_stats.remove('G')
    clean_cols = stats_list[:]
    clean_cols.append('Player_id')
    clean_cols.append('Player_name')
    clean_cols.append('Season_id')

    weighted_stats = pd.DataFrame(columns = clean_cols)
    for a in active_players:

        ## last season...
        season_1 = _1_seasons_ago[_1_seasons_ago['Player_id'] == a]
        a_name = season_1['Player_name'].max()
        season_1 = clean_and_agg_data(a, season_1, stats_list, convert_stats, agg_dict)
        season_1['Season_id'] = '217'
        weighted_stats = weighted_stats.append(season_1)
        ## 2 seasons ago...
        season_2 = _2_seasons_ago[_2_seasons_ago['Player_id'] == a]
        if len(season_2) > 0:
            season_2 = clean_and_agg_data(a, season_2, stats_list, convert_stats, agg_dict)
            season_2['Season_id'] = '216'
            weighted_stats = weighted_stats.append(season_2)
        else:
            pass
        ## 3 seasons ago...
        season_3 = _3_seasons_ago[_3_seasons_ago['Player_id'] == a]
        if len(season_3) > 0:
            season_3 = clean_and_agg_data(a, season_3, stats_list, convert_stats, agg_dict)
            season_3['Season_id'] = '215'
            weighted_stats = weighted_stats.append(season_3)
        else:
            pass

    ## weight the stats
    weighted_stats['Season_weight'] = np.where(weighted_stats['Season_id'] == '217', 6,
                                               np.where(weighted_stats['Season_id'] == '216',
                                               3, 1))
    for i in stats_list:
        weighted_stats[i] = weighted_stats[i] * weighted_stats['Season_weight']

    ## build projections player by player
    players_list = list(set(weighted_stats['Player_id'].tolist()))
    p_stats_cols = stats_list[:]
    p_stats_cols.append('Season_weight')
    projections = pd.DataFrame(columns = list(weighted_stats))
    for p in players_list:
        p_stats = weighted_stats[weighted_stats['Player_id'] == p]
        p_name = p_stats['Player_name']

        p_stats = p_stats.groupby(['Player_id', 'Player_name'], as_index = False).sum()
        for s in stats_list:
            p_stats[s] = p_stats[s] / p_stats['Season_weight']
            p_stats[s] = p_stats[s].round(2)

        projections = projections.append(p_stats)

    ## convert stats back to per game
    for c in convert_stats:
        projections[c] = projections[c] / projections['G']
        projections[c] = projections[c].round(2)

    projections = projections.drop(columns = ['Season_weight', 'Season_id'])

    ## add ranking column
    project_cols = list(projections)
    project_cols.remove('Player_name')
    project_cols.remove('Player_id')


    for p in project_cols:
        col_name = "%s_rank"%p
        projections[col_name] = projections[p].rank(ascending = False)

    return projections

def clean_and_agg_data(player_id, data, stats_list, convert_stats, agg_dict):
    p_name = data['Player_name'].max()

    for c in convert_stats:
        data[c] = data[c] * data['G']
    data = data[stats_list]
    for col in data.columns:
        data[col] = pd.to_numeric(data[col])
    season_agg = data.agg(agg_dict)

    ## add player info columns
    season_agg = season_agg.tolist()
    season_agg = pd.DataFrame([season_agg], columns = stats_list)

    season_agg['Player_name'] = p_name
    season_agg['Player_id'] = player_id

    return season_agg

## simple function for cleaning stats csvs and uploading them to the db
def upload_player_stats(season_id):

    _season_data = pd.read_csv("%s/projects/NBA_Jam/Data/%s_season_player_stats.csv"%(home_dir, season_id), sep = ",")
    _season_data[['Player_name', 'Player_id']] = _season_data['Player'].str.split('\\', expand = True)
    _season_data = _season_data.drop(columns = ['Player', 'Rk'])

    clean_cols = []
    old_cols = list(_season_data)
    for n, c in enumerate(old_cols):
        #print old_cols[n]
        if "%" in c:
            c = c.replace("%", "per")
        elif c == "PS/G":
            c = "PTS"
            pass
        clean_cols.append(c)

    _season_data.columns = clean_cols

    ## upload to db
    conn = establish_db_connection('sqlalchemy').connect()
    table_name = "player_season_stats_%s"%season_id

    print "uploading stats to %s..."%table_name
    _season_data.to_sql(table_name, con = conn, index = False, if_exists = 'replace')

    return None

if __name__ == "__main__":
    main('217')

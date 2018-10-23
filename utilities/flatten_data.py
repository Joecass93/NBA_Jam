import pandas as pd
from datetime import datetime, date
from db_connection_manager import establish_db_connection


def flatten_scores():
    #seasons = ['002120', '002110', '002100']
    games_to_fill = ['0021200628', '0021200627', '0021200626', '0021200619', '0021200618', '0021200617', '0021200616', '0021200614']
    for g in games_to_fill:
        conn = establish_db_connection("sqlalchemy").connect()

        #print "flattening scores for season_id = %s"%s
        final_scores_sql = 'SELECT * FROM final_scores WHERE GAME_ID = "%s"'%(g)
        final_scores_table = pd.read_sql(final_scores_sql, con = conn)

        i = 0
        game_cols = ['game_date', 'game_id', 'away_team_id', 'away_team_abbreviation', 'away_pts', 'home_team_id', 'home_team_abbreviation', 'home_pts', 'home_pt_diff']
        # if i <= (len(final_scores_table) + 1):
        all_games_table = pd.DataFrame(columns = game_cols)

        for i in range(0, len(final_scores_table), 2):

            curr_game = final_scores_table[i:i+2][['GAME_DATE_EST', 'GAME_ID','TEAM_ID','TEAM_ABBREVIATION', 'PTS']]
            curr_game.insert(5, 'SIDE', ['away', 'home'])

            game_date = curr_game['GAME_DATE_EST'].max()
            game_id = curr_game['GAME_ID'].max()

            away = curr_game[curr_game['SIDE'] == 'away']
            home = curr_game[curr_game['SIDE'] == 'home']

            clean_game = away.merge(home, how = 'left', on = ['GAME_ID', 'GAME_DATE_EST'])
            clean_game = clean_game.drop(columns = ['SIDE_y', 'SIDE_x'])

            clean_game['home_pt_diff'] = clean_game['PTS_y'] - clean_game['PTS_x']

            clean_game.columns = game_cols

            all_games_table = all_games_table.append(clean_game)

        ## write flattened scores to the database, game_id is the key so duplicate uploads will be blocked
        upload_flatten_data(all_games_table, 'flatten_final_scores')

        return None

def flatten_four_factors_thru(season_id):

    conn = establish_db_connection('sqlalchemy').connect()

    four_factors_sql = 'SELECT * FROM four_factors_thru WHERE GAME_ID LIKE "%s"'%(season_id + "0%%")
    #four_factors_sql = "SELECT * FROM four_factors_thru"
    four_factors_df = pd.read_sql(four_factors_sql, con = conn)
    print four_factors_df.head()

    games_list = list(set(four_factors_df['GAME_ID'].tolist()))

    #rerun_games = pd.read_sql("SELECT * FROM flatten_four_factors_thru WHERE home_team_id IS NULL", con = conn)

    flatten_cols = list(four_factors_df)
    flatten_cols.remove('SIDE')
    flatten_cols = [x.lower() for x in flatten_cols]

    away_flatten_cols = ["away_%s"%x for x in flatten_cols]
    home_flatten_cols = ["home_%s"%x for x in flatten_cols]
    flatten_cols = away_flatten_cols + home_flatten_cols
    flatten_cols.remove('home_game_id')

    ff_flatten_df = pd.DataFrame(columns = flatten_cols)
    for g in games_list:
        print "flattening %s"%g
        ff_slice = four_factors_df[four_factors_df['GAME_ID'] == g]
        slice_away = ff_slice[ff_slice['SIDE'] == 'AWAY']
        slice_home = ff_slice[ff_slice['SIDE'] == 'HOME']

        game_id = slice_away['GAME_ID'].item()
        ff_slice = slice_away.merge(slice_home, how = 'left', on = ['GAME_ID'])
        ff_slice = ff_slice.drop(columns = ['SIDE_x', 'SIDE_y'])

        ff_slice.columns = flatten_cols

        ff_flatten_df = ff_flatten_df.append(ff_slice)

    ff_flatten_df = ff_flatten_df.rename(columns = {'away_game_id':'game_id'})

    upload_flatten_data(ff_flatten_df, 'flatten_four_factors')

    return None

def upload_flatten_data(data, db_name):

    conn = establish_db_connection('sqlalchemy').connect()

    print "uploading flattened data to %s"%db_name

    try:
        data.to_sql(db_name, con = conn, index = None, if_exists = 'append')
        print "succesfully uploaded flattened data!"

    except Exception as e:
        print "could not upload data to db because: %s"%e

    return None

if __name__ == "__main__":
    flatten_four_factors_thru('00213')

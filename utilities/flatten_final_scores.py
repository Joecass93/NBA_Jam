import pandas as pd
from datetime import datetime, date
from db_connection_manager import establish_db_connection



#seasons = ['002120', '002110', '002100']
#games_to_fill = ['0021200628', '0021200627', '0021200626', '0021200619', '0021200618', '0021200617', '0021200616', '0021200614']
for g in games_to_fill:
    conn = establish_db_connection("sqlalchemy").connect()

    print "flattening scores for season_id = %s"%s
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
    db_table = 'final_scores_flatten'
    print "writing flattened scores to %s..."%db_table
    all_games_table.to_sql(db_table, con = conn, index = None, if_exists = 'append')
    print "finished writing scores for season_id = %s!"%s

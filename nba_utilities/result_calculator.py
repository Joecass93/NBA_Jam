import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from db_connection_manager import establish_db_connection
from argparse import ArgumentParser
from assets import range_all_dates


parser = ArgumentParser()
parser.add_argument("-s", "--start_date", help="start date for calculating results", type=str, required=False)
parser.add_argument("-e", "--end_date", help="end date for calculating results", type=str, required=False)

flags = parser.parse_args()

if flags.start_date:
    start_date = flags.start_date
else:
    start_date = (datetime.now().date() - timedelta(days = 1)).strftime('%Y-%m-%d')
if flags.end_date:
    end_date = flags.end_date
else:
    end_date = (datetime.now().date() - timedelta(days = 1)).strftime('%Y-%m-%d')

def main(start_date = start_date, end_date = end_date):
    conn = establish_db_connection('sqlalchemy').connect()

    date_list = range_all_dates(start_date, end_date)
    for d in date_list:
        print "getting picks and scores for %s"%d
        game_scores, game_picks = get_picks_and_scores(d)
        print "determing results..."
        daily_result = determine_results(game_scores, game_picks)
        if daily_result is not None:
            print "uploading to db..."
            try:
                daily_result.to_sql("results_table", if_exists = 'append', con = conn)
            except Exception as e:
                print "tried to upload duplicate records to results_table"
        else:
            print "no games today"
        print ""

    return daily_result

def get_picks_and_scores(game_date):
    conn = establish_db_connection('sqlalchemy').connect()

    for i, sql_table in enumerate(['final_scores', 'historical_picks']):
        game_date_query = "SELECT * FROM %s WHERE game_date = '%s'"%(sql_table, game_date)
        try:
            query_output = pd.read_sql(game_date_query, con = conn)
            if i == 0:
                game_scores = query_output
            else:
                game_picks = query_output
        except Exception as e:
            print "could not get data from %s because: %s"%(sql_table, e)

    return game_scores, game_picks

def determine_results(game_scores, game_picks):
    games_list = list(game_picks['game_id'])

    if len(games_list) > 0:
        pass
    else:
        return None

    game_scores = game_scores.drop(columns = ['away_id', 'home_id', 'home_team',
                                              'away_team', 'game_date'])
    merged_game_data = pd.merge(game_scores, game_picks, how = 'left', on = 'game_id')
    merged_game_data['vegas_spread'] = pd.to_numeric(merged_game_data['vegas_spread_str'].str[5:9], errors = 'coerce')
    merged_game_data['side_favored'] = np.where(merged_game_data['vegas_spread_str'].str[0:3] == merged_game_data['home_team'],
                                                "Home", "Away")
    merged_game_data['side_covered'] = np.where(merged_game_data['side_favored'] == "Home",
                                                np.where(merged_game_data['pts_home'] > (merged_game_data['pts_away'] - merged_game_data['vegas_spread']),
                                                         'Home', 'Away'),
                                                np.where(merged_game_data['pts_away'] > (merged_game_data['pts_home'] - merged_game_data['vegas_spread']),
                                                         'Away', 'Home'))

    merged_game_data['team_covered'] = np.where(merged_game_data['side_covered'] == 'Home',
                                                merged_game_data['home_team'], merged_game_data['away_team'])
    merged_game_data['team_picked'] = merged_game_data['pick_str'].str[0:3]
    merged_game_data['result'] = np.where(merged_game_data['team_picked'] == merged_game_data['team_covered'],
                                          "Win", "Loss")
    merged_game_data['result'] = np.where(merged_game_data['pt_diff'].abs() < 1.5, "No Bet", merged_game_data['result'])

    final_cols = ['game_date', 'game_id', 'home_team', 'away_team', 'pts_home', 'pts_away',
                  'vegas_spread_str', 'pred_spread_str', 'pick_str',
                  'team_covered', 'team_picked', 'result', 'best_bet']

    results_final = merged_game_data[final_cols]

    return results_final

if __name__ == "__main__":
    main()

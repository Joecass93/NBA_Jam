import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from db_connection_manager import establish_db_connection
from argparse import ArgumentParser
from gsheets_api_manager import df_to_gsheet

parser = ArgumentParser()
parser.add_argument("-d", "--game_date", help="date to start pulling final scores data from: ex. '2017-11-01'", type=str, required=False)

flags = parser.parse_args()

if flags.game_date:
    game_date = flags.game_date
else:
    game_date = (datetime.now().date() - timedelta(days = 1)).strftime('%Y-%m-%d')

## Accepts date in string format YYYY-MM-DD
def main(game_date = game_date):
    # Get date for run
    if game_date:
        game_date_dt = datetime.strptime(game_date, '%Y-%m-%d').date()
    else:
        game_date_dt = datetime.now().date()
        game_date = game_date_dt.strftime('%Y-%m-%d')

    game_scores, game_picks = get_picks_and_scores(game_date)

    daily_result = determine_results(game_scores, game_picks)

    print daily_result

    return daily_result

def get_picks_and_scores(game_date):

    ## Establish sql db connection
    engine = establish_db_connection('sqlalchemy')
    conn = engine.connect()

    ## Select games & picks from scores table
    for i, sql_table in enumerate(['historical_scores_table', 'historical_picks_table']):
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

    ## Get list of games ids
    games_list = list(game_picks['game_id'])
    print games_list
    if len(games_list) > 0:
        pass
    else:
        return None
    ## Do the maths
    for i, g in enumerate(games_list):
        # get score data for game
        g_score = game_scores[game_scores['game_id'] == g]
        # get pick data for game
        g_pick = game_picks[game_picks['game_id'] == g]

        g_date = g_score['game_date'].item()
        away_spread = g_pick['vegas_spread'].item()
        pred_spread = g_pick['pred_spread'].item()
        diff_pred_spread = g_pick['pt_diff'].item()
        pt_diff_away = g_score['pt_diff_away'].item()
        away_team = g_score['away_team'].item()
        away_points = g_score['pts_away'].item()
        home_team = g_score['home_team'].item()
        home_points = g_score['pts_home'].item()
        pick = g_pick['pick_str'].item()
        vegas_spread = g_pick['vegas_spread_str'].item()
        best_bet = g_pick['best_bet'].item()

        if diff_pred_spread < 0:
            if away_spread > 0:
                if (pt_diff_away < 0) & (abs(pt_diff_away) > int(away_spread)):
                    print 'WINNER: home favorite is the pick | home favorite covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'win'
                else:
                    print 'LOSER: home favorite is the pick | away underdog covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'loss'
            else:
                if away_spread < pt_diff_away:
                    print 'LOSER: home underdog is pick | away favorite covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'loss'
                else:
                    print 'WINNER: home underdog is pick | home underdog covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'win'

        elif diff_pred_spread > 0:
            if away_spread > 0:
                if pt_diff_away > 0:
                    print 'WINNER: away underdog is pick | away underdog covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'win'
                elif abs(pt_diff_away) < int(away_spread):
                    print 'WINNER: away underdog is pick | away underdog covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'win'
                else:
                    print 'LOSER: away underdog is pick | home favorite covered'
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'loss'
            else:
                if pt_diff_away < 0:
                    print "LOSER: away favorite is pick | home underdog covered"
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'loss'
                elif abs(away_spread) > int(pt_diff_away):
                    print "LOSER: away favorite is pick | home underdog covered"
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'loss'
                else:
                    print "WINNER: away favorite is pick | away favorite covered"
                    print 'away_spread: %s, away_pred: %s, diff_pred_spread: %s, actual_diff: %s'%(away_spread, pred_spread, diff_pred_spread, pt_diff_away)
                    r = 'win'

        results_cols = ['game_date', 'game_id', 'away_team', 'away_score', 'home_team', 'home_points', 'spread', 'pick', 'result', 'result_vs_spread', 'best_bet']
        results_list = [g_date, g, away_team, away_points, home_team, home_points, vegas_spread, pick, r, 0, best_bet]
        if i == 0:
            results_final = pd.DataFrame(data = [results_list], columns = results_cols)
        else:
            results_final = results_final.append(pd.DataFrame(data = [results_list], columns = results_cols))

    return results_final

if __name__ == "__main__":
    main()

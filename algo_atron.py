import pandas as pd
import numpy as np
from sklearn import linear_model
from datetime import datetime
from utilities.db_connection_manager import establish_db_connection

engine = establish_db_connection("sqlalchemy")
conn = engine.connect()

def main(season = None):

    ## Determine mulitlinear function based on last years data
    # ex. home_spread = home_efg.x1 + home_opp_efg.x2 + ... + away_ftr.x15 + away_opp_ftr.x16
    ff_data, games, scores, spreads = get_test_algo_data(season = season)

    clean_data = clean_and_aggregate_data(ff_data, games, scores, spreads)

    predictions = run_test_algo(clean_data)
    print predictions.head(10)

    best_bets = predictions[predictions.scored_diff > 3.5]
    opt_season = predictions[(predictions.game_id < '0021701100')]
    opt_season_best_bets = opt_season[opt_season.scored_diff > 3.5]
    print opt_season_best_bets.game_id.max()

    print ""
    print "Overall wins: %s"%len(predictions[predictions.result == "win"])
    print "Overall losses: %s"%len(predictions[predictions.result == "loss"])
    print ""
    print "Best bets wins: %s"%len(best_bets[best_bets.result == "win"])
    print "Best bet losses: %s"%len(best_bets[best_bets.result == "loss"])
    print ""
    print "Optimal season wins: %s"%len(opt_season[opt_season.result == "win"])
    print "Optinal season losses: %s"%len(opt_season[opt_season.result == "loss"])
    print ""
    print "Best bets in optimal season wins: %s"%len(opt_season_best_bets[opt_season_best_bets.result == "win"])
    print "Best bets in optimal season losses: %s"%len(opt_season_best_bets[opt_season_best_bets.result == "loss"])
    print ""

    return None


def get_test_algo_data(season = None, start_date = None, end_date = None):

    if season:
        sql_season = '002' + season[2:4]
        season_sql = 'SELECT * FROM four_factors WHERE GAME_ID LIKE "%s%s"'%(sql_season, '%%')
        games_sql = 'SELECT * FROM games WHERE GAME_ID LIKE "%s%s"'%(sql_season, '%%')
        scores_sql = 'SELECT GAME_ID, TEAM_ID, PTS FROM final_scores WHERE GAME_ID LIKE "%s%s"'%(sql_season, '%%')
        spreads_sql = 'SELECT game_id, vegas_spread FROM historical_picks_table'
        ff_data = pd.read_sql(season_sql, con = conn)
        ## truncate data to match games data
        ff_data = ff_data[ff_data.GAME_ID >= '0021700017']
        games = pd.read_sql(games_sql, con = conn)
        scores = pd.read_sql(scores_sql, con = conn)
        spreads = pd.read_sql(spreads_sql, con = conn) ## pull vegas spreads (pos spread means home team favored)
        spreads['vegas_spread'] = np.where(spreads.vegas_spread != 0.0, -spreads.vegas_spread, 0.0)
        scores = scores[scores.GAME_ID >= '0021700017']
    else:
        pass


    return ff_data, games, scores, spreads

def clean_and_aggregate_data(ff_data, games, scores, spreads):

    ## headers for later use
    ff_headers = ['TEAM_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']
    home_headers = ['home_id', 'home_efg', 'home_ftr', 'home_tov', 'home_orb', 'home_opp_efg', 'home_opp_ftr', 'home_opp_tov', 'home_opp_orb']
    away_headers = ['away_id', 'away_efg', 'away_ftr', 'away_tov', 'away_orb', 'away_opp_efg', 'away_opp_ftr', 'away_opp_tov', 'away_opp_orb']

    ## get list of all game ids from the time range
    s_games = list(ff_data.sort_values(by = ['GAME_ID']).GAME_ID.unique())

    ## Loop thrugh list of all game_ids, get both teams' FF aggregate data up to that game, and clean data
    for i, g in enumerate(s_games[50:125]):
        ##
        home_id = games[games.game_id == g].home_id.max()
        away_id = games[games.game_id == g].away_id.max()

        ##
        home_ff = ff_data[(ff_data.GAME_ID < g) & (ff_data.TEAM_ID == int(home_id))][ff_headers]
        away_ff = ff_data[(ff_data.GAME_ID < g) & (ff_data.TEAM_ID == int(away_id))][ff_headers]

        ## aggregate data
        curr_home = (home_ff.groupby(['TEAM_ID']).mean()).reset_index()
        curr_away = (away_ff.groupby(['TEAM_ID']).mean()).reset_index()
        curr_home.columns = home_headers
        curr_away.columns = away_headers

        ## add game_ids to merge on
        curr_away['game_id'] = g
        curr_home['game_id'] = g

        ## get final scores
        curr_away['away_pts'] = scores[(scores.GAME_ID == g) & (scores.TEAM_ID == curr_away.away_id.item())]['PTS'].item()
        curr_home['home_pts'] = scores[(scores.GAME_ID == g) & (scores.TEAM_ID == curr_home.home_id.item())]['PTS'].item()

        ## merge the 2 dfs
        curr_game = curr_home.merge(curr_away, how = 'left', on = 'game_id')
        # get point differential in terms of the home team
        curr_game['result_spread'] = curr_game.away_pts - curr_game.home_pts
        curr_game['spread'] = spreads[spreads.game_id == g].vegas_spread.item()
        curr_game['cover'] = np.where(curr_game.result_spread > curr_game.spread, "away", "home")

        if i == 0:
            clean_dataset = curr_game
        else:
            clean_dataset = clean_dataset.append(curr_game)

    return clean_dataset

def run_test_algo(data):

    training_data_cols = ['home_efg', 'home_ftr', 'home_tov', 'home_orb', 'home_opp_efg', 'home_opp_ftr',
                          'home_opp_tov', 'home_opp_orb', 'away_efg', 'away_ftr', 'away_tov', 'away_orb',
                          'away_opp_efg', 'away_opp_ftr', 'away_opp_tov', 'away_opp_orb']

    ## remove unneeded columns
    training_data = data[training_data_cols]

    algo_methods = ['LinearRegression', 'LogisticRegression']
    model_dict = {}
    model_dict['model_preds'] = {}
    model_dict['pred_labels'] = {'LinearRegression':'pred_spred', 'LogisticRegression':'cover_team'}

    for a in algo_methods:

        a_function = eval('linear_model.%s'%a)

        ## define training data
        X = training_data

        ## get model specific data
        if a == 'LinearRegression':
            target_data = data[['result_spread']]
            y = target_data.result_spread

        elif a == 'LogisticRegression':
            target_data = data[['cover']]
            y = target_data.cover

        else:
            return None

        ## build the specified linear model
        lm = a_function()
        model = lm.fit(X, y)

        ## get predicted values
        predictions = lm.predict(X)

        ## add predictions to the model dictionary
        #model_dict['model_preds'][a] = predictions

        model_df = data
        model_df[model_dict['pred_labels'].get(a)] = predictions

        print model_df

    # residuals_df = data
    # residuals_df['pred_spread'] = predictions
    #
    # residuals_df['residuals '] = residuals_df.result_spread - residuals_df.pred_spread
    # residuals_df['scored_diff'] = abs(residuals_df.pred_spread - residuals_df.spread)
    #
    # residuals_df['bet'] = np.where(residuals_df.pred_spread > residuals_df.spread, "away", "home")
    # residuals_df['result'] = np.where(residuals_df.result_spread > residuals_df.spread,
    #                             np.where(residuals_df.bet == "away", "win", "loss"),
    #                             np.where(residuals_df.bet == "away", "loss", "win"))

    print lm.score(X, y)

    return None

if __name__ == "__main__":
    main('2017-18')

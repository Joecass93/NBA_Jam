import pandas as pd
from pandas import *
from datetime import datetime, date
import numpy as np
from utilities.db_connection_manager import establish_db_connection
from sklearn.linear_model import LinearRegression
import scipy.stats as stats
import matplotlib.pyplot as pyplot
import statsmodels.api as sm

class nba_modeling(object):

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()

    def build_model(self, type, datasource):

        if type == "predictive":
            self.build_predictive_model(datasource)
        elif type == "descriptive":
            self.build_descriptive_model(datasource)
        else:
            print "Not a valid model type, please try again!"
            return None

    def build_predictive_model(self, datasource):

        algo_data = self.fetch_data(datasource)

        linear_predictions = self.run_linear_regression(algo_data)
        #logisitic_predictions = self.run_logistic_regression(algo_data)

        return None

    def build_descriptive_model(self, datasource):

        algo_data = self.fetch_data(datasource)

        self.explore_algo_data(algo_data)

        return None


    def explore_algo_data(self, algo_data):

        explore_dict = {'distinct_spread_count':"",
                        'distinct_pt_diff_count':"",
                        'winner_by_spread_count':"",
                        'pt_diff_spread_merge_count':""
                        }

        distinct_spread_count = algo_data.groupby('away_spread')['index'].nunique()
        distinct_pt_diff_count = algo_data.groupby('spread_final')['index'].nunique()
        winner_by_spread_count = algo_data.groupby(['away_spread', 'winner'])['index'].nunique().reset_index()
        pt_diff_spread_merge_count = algo_data.groupby(['spread_final', 'away_spread'])['index'].nunique().reset_index()

        for i, v in explore_dict.iteritems():
            explore_dict[i] = eval(i)

        return explore_dict

    ## get data (how = {'db', 'build'}, 'db' fetches most recent merged table from db,
    ##### 'build' builds a new merged dataset with data from start of 2012 season to current day)
    def fetch_data(self, how):
        if how == 'db':
            print "fetching latest merged dataset from the db..."
            merged_data = pd.read_sql("SELECT * FROM algo_merged_data", con = self.conn)
        else:
            print "building merged dataset with freshest data..."
            merged_data = build_clean_data().algo_data_cleaner()

        return merged_data

    def run_linear_regression(self, algo_data):

        ## remove games with na
        algo_data = algo_data[algo_data['spread_final'].notna()]

        print  algo_data.shape
        print list(algo_data)

        feature_list = ['home_efg_pct', 'home_fta_rate', 'home_tm_tov_pct', 'home_oreb_pct',
                          'home_opp_efg_pct', 'home_opp_fta_rate', 'home_opp_tov_pct',
                          'home_opp_oreb_pct', 'away_efg_pct', 'away_fta_rate', 'away_tm_tov_pct',
                          'away_oreb_pct', 'away_opp_efg_pct', 'away_opp_fta_rate',
                          'away_opp_tov_pct', 'away_opp_oreb_pct']

        # isolate just the features
        data = algo_data[feature_list]
        # merge in the final score differential
        data['score'] = algo_data.spread_final

        print data.head()

        X = data.drop('score', axis = 1)
        y = data.score

        # create the linear regression object
        lm = LinearRegression()
        lm.fit(X, y)

        print 'estimated intercept coefficient: %s'%lm.intercept_
        print 'Number of coefficients: %s'%len(lm.coef_)

        features_df = pd.DataFrame(zip(X.columns, lm.coef_), columns = ['features', 'estimatedCoefficients'])

        print features_df

        todays_stats = pd.read_sql('SELECT * FROM todays_merged_data', con = self.conn)

        i = 0
        for g in todays_stats['game_id'].unique():
            sample = todays_stats[todays_stats['game_id'] == g]

            merged_sample = sample[sample['SIDE'] == "away"].merge(sample[sample['SIDE'] == "home"], how = 'left', on = ['game_id'])
            merged_sample = merged_sample.drop(columns = ['SIDE_y', 'SIDE_x', 'game_id',
                                                          'SEQUENCE_x', 'SEQUENCE_y',
                                                          'index_x', 'index_y', 'TEAM_ID_x',
                                                          'TEAM_ID_y'])
            merged_sample.columns = feature_list
            if i == 0:
                final_sample = merged_sample
            else:
                final_sample = final_sample.append(merged_sample)

            i = i + 1


        predictions = lm.predict(final_sample)
        print predictions

        final_sample['preds'] = predictions

        print final_sample


        # pyplot.scatter(data.score, lm.predict(X))
        # pyplot.xlabel("Away final spread")
        # pyplot.ylabel("Predicted spread")
        # pyplot.title("Final spread vs predicted spread")
        # pyplot.show()
        #
        # print lm.predict(X)[0:5]
        #
        # import statsmodels.formula.api as smf
        # dat = sm.datasets.get_rdataset("Guerry", "HistData").data
        # print type(dat)
        # print dat.head()

        # results = smf.ols('score ~ %s'%(" + ".join(feature_list)), data = data.head(100)).fit()
        # results = results.fit()
        # print (results.summary())



        # feature_list = ['home_efg_pct', 'home_fta_rate', 'home_tm_tov_pct', 'home_oreb_pct',
        #                   'home_opp_efg_pct', 'home_opp_fta_rate', 'home_opp_tov_pct',
        #                   'home_opp_oreb_pct', 'away_efg_pct', 'away_fta_rate', 'away_tm_tov_pct',
        #                   'away_oreb_pct', 'away_opp_efg_pct', 'away_opp_fta_rate',
        #                   'away_opp_tov_pct', 'away_opp_oreb_pct']
        #
        # training_data = algo_data[~algo['game_id'].str.contains('002170')]
        #
        #
        # test_data = algo_data[algo_data['game_id'].str.contains('002170')]
        # y_test = test_data['spread_final']
        #
        # print len(training_data)
        # print len(test_data)
        # #algo_data_clean = algo_data.drop(columns = ['game_id', 'date', 'away_pts', 'home_pts',
        #                                           'home_team', 'away_team', 'home_team_id',
        #                                           'away_team_id', 'spread_final', 'away_spread',
        #                                           'index', 'winner'])
        #
        # ## define training data
        # X_train = training_data[feature_list]
        # y_train = training_data['spread_final']
        #
        # ## define testing data
        # X_test = testing_data[feature_list]
        # y_test = testing_data['spread_final']
        #
        # ## build linear model
        # lm = linear_model.LinearRegression()
        # model = lm.fit(X_train, y_train)
        #
        # ## get list of predictions
        # pred_train = lm.predict(X_train)
        # pred_test = lm.predict(X_test)
        #
        # #residuals_df = algo_data
        # #residuals_df['pred_away_spread'] = predictions
        #
        # #print residuals_df.head()
        #
        # #residuals_df['residuals'] = residuals_df.spread_final - residuals_df.pred_away_spread
        # #residuals_df['bet'] = np.where(residuals_df.pred_away_spread > residuals_df.away_spread, 'home', 'away')
        #
        # print lm.score(X, y)
        #
        # ## build df of features and their coefficients
        # features = pd.DataFrame(zip(X.columns, lm.coef_),
        #                         columns = ['features', 'estimatedCoefficients'])
        #
        # print features
        #
        # pyplot.scatter(predictions, y)
        # print pyplot.show()


        return None


    def spread_vs_score_breakdowns(self, algo_data):

        ##

        return None


class build_clean_data(object):

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()

    def algo_data_cleaner(self):

        ## get tables from database
        print "pulling tables.."
        print ""
        raw_data = self.get_algo_data()
        ## merge final scores and spreads_scraper
        print "merging scores and spreads data..."
        print ""
        spreads_w_scores = self.clean_spreads_data(raw_data['spreads'], raw_data['flatten_final_scores'])
        stats = raw_data['flatten_four_factors_thru']
        ## merge game info with each teams' season stats up to that game
        print "merging in four factors stats..."
        print ""
        algo_data = spreads_w_scores.merge(stats, how = 'right', on = ['game_id'])
        ## upload data to the db
        algo_data.to_sql('algo_merged_data', con = self.conn, if_exists = 'replace')

        return algo_data

    def get_algo_data(self):

        db_tables = ['spreads', 'flatten_final_scores', 'flatten_four_factors_thru']
        raw_data = {}

        for t in db_tables:
            sql_str = "SELECT * FROM %s"%t;
            df = pd.read_sql(sql_str, con = self.conn)
            raw_data[t] = df

        return raw_data

    def clean_spreads_data(self, spreads_data, schedule):

        ## limit cols for schedule
        schedule_cols = ['game_date', 'game_id', 'away_team_id', 'home_team_id', 'away_pts', 'home_pts', 'home_pt_diff']
        schedule = schedule[schedule_cols]
        ## merge game id into spread data
        spreads_data['game_date'] = pd.to_datetime(spreads_data['date']).dt.date
        spreads = spreads_data.merge(schedule, how = 'left', on = ['game_date',
                                                                   'away_team_id',
                                                                   'home_team_id'])

        ## clean up spreads data (only use bovada lines for now...)
        spreads_clean_cols = ['game_id', 'date', 'team', 'away_team_id',
                              'opp_team', 'home_team_id', 'away_pts', 'home_pts',
                              'home_pt_diff', 'bovada_line']

        spreads = spreads[spreads_clean_cols]
        spreads = spreads.rename(index = str, columns = {'team':'away_team',
                                                        'bovada_line':'away_spread',
                                                        'home_pt_diff':'spread_final'})

        ## remove all star games etc..
        spreads = spreads[spreads['away_team_id'].notna()]
        ## remove games that were postponed from spread data
        spreads = spreads[spreads['game_id'].notna()]

        ## transform spread from str to int for maths
        spreads['away_spread'] = spreads['away_spread'].str.replace("+", "")
        ## replace pickems with 0
        spreads['away_spread'] = np.where((spreads['away_spread'].str.contains("PK")) | (spreads['away_spread'] == ""), "0", spreads['away_spread'])

        ## rounding, forcing integers etc..
        spreads['away_pts'] = spreads.away_pts.astype(int)
        spreads['home_pts'] = spreads.home_pts.astype(int)
        spreads['away_spread'] = pd.to_numeric(spreads['away_spread'])
        spreads['away_spread'] = spreads.away_spread.astype(int)
        spreads['spread_final'] = spreads.spread_final.astype(int)

        ## limit to just >= 213 season games
        spreads = spreads[spreads['game_id'] >= '0021300000']

        ## remove team columns, they will be merged back in with stats
        spreads = spreads.drop(columns = ['home_team_id', 'away_team_id', 'away_team', 'opp_team'])
        spreads['winner'] = np.where(spreads['spread_final'] < spreads['away_spread'], "away", "home")

        return spreads


if __name__ == "__main__":
    nba_modeling().build_model(type = 'predictive', datasource = 'db')

"""
MERGED DATA BUILDER DAILY

DESCRIPTION:
This script allows the user to enter a date as a string, and return a dataframe containing game
predictions for that date.

IMPORTED BY:
merged_historical_builder

IMPORT(S): config.teams, config.spread_teams, request_header, assets.list_games,
pulls.spreads_scraper

INPUT(S):
Date in string format - 'YYYY-MM-DD'

OUTPUT(S):
Dataframe containing each game for the date selected with the following metrics:
vegas spread, predicted spread, differential between predicted and actual spread, and ranking
for each game

FUNCTION(S):
-- todays_matches(gamedate) -> sends pull request to nba api and returns a dataframe containing information
about games for a given date
-- get_cumulative_ff(team_id, gamedate, season, side, sequence) ->
-- format_and_run_daily_stats(dirty_stats) ->
-- run_daily_algo(match) ->
-- merged_daily_data(daily_preds, daily_vegas) ->
-- clean_predictions(daily_final) ->

CREATED/REFACTORED BY: Joe Cassidy / 08.12.2018

"""

import pandas as pd
import numpy as np
import datetime
import requests
import json
from utilities.config import teams, spread_teams, request_header, season_sql
from utilities.assets import list_games
from utilities.db_connection_manager import establish_db_connection
from pulls import spreads_scraper
from os.path import expanduser
from argparse import ArgumentParser

## API error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

## Establish home directory
home_dir = expanduser("~")

## Establish db Connection
engine = establish_db_connection('sqlalchemy')
conn = engine.connect()

## Main function
def main(gamedate = None):

	if gamedate:
		pass
	else:
		gamedate = '2017-11-01'

	print "getting matchups for %s..."%gamedate
	matches = todays_matches(gamedate)

	print "getting stats for each team..."
	for i, g in enumerate(matches['GAME_ID']):
		away = matches.VISITOR_TEAM_ID.astype(str)[i]
		home = matches.HOME_TEAM_ID.astype(str)[i]
		print "getting %s: %s @ %s"%(g, away, home)
		away_ff_cum = get_cumulative_ff(away, gamedate, '2017-18', 'away', i)
		home_ff_cum = get_cumulative_ff(home, gamedate, '2017-18', 'home', i)
		if i == 0:
			todays_ff_cum = away_ff_cum
			todays_ff_cum = todays_ff_cum.append(home_ff_cum)
		else:
			todays_ff_cum = todays_ff_cum.append(away_ff_cum)
			todays_ff_cum = todays_ff_cum.append(home_ff_cum)

	print "formatting stats..."
	daily_preds = format_and_run_daily_stats(todays_ff_cum)

	print "getting todays spreads..."
	daily_vegas = spreads_scraper.main(gamedate)

	print "merging data..."
	merged_data = merged_daily_data(daily_preds, daily_vegas)

	print "making predictions..."
	output = clean_predictions(merged_data)

	## if daily run then write dataframe to daily_picks sql table
	if gamedate == '2017-11-01':
		print "writing predictions to daily picks sql table..."
		daily_engine = establish_db_connection('sqlalchemy')
		daily_conn = daily_engine.connect()
		output.to_sql(name = 'daily_picks', con = daily_conn, if_exists = 'replace', index = False)
	else:
		pass

	print "predictions finished at %s"%datetime.datetime.now()

	return output

def todays_matches(gamedate):
	# Reformat gamedate to conform with api endpoint
	gamedate = datetime.datetime.strptime(gamedate, '%Y-%m-%d')
	gamedate= gamedate.strftime('%m/%d/%Y')
	try:
		scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%gamedate
		response = requests.get(scoreboard_url, headers=request_header)
		data = response.text
		data = json.loads(data)
		cleaner = data['resultSets'][0]
		col_names = cleaner['headers']
	except requests.ConnectionError as e:
		print e

	# Check how many games there are today
	scoreboard_len = len(cleaner['rowSet'])

	# Loop through and get each game's info
	games_today = []
	for x in range(0,scoreboard_len):
		game_info = cleaner['rowSet'][x]
		games_today.append(game_info)

	# Create dataframe containing info about today's game
	df_matches = pd.DataFrame(games_today, columns = col_names)

	return df_matches

## Need to get four factors stats at current point in season
def get_cumulative_ff(team_id, game_date, season, side = None, sequence = None):
    games_played = list_games(team_id, game_date)
    games_str = ",".join(games_played)
    season = season_sql[season]
    r_stats = pd.read_sql("SELECT * FROM four_factors_table WHERE TEAM_ID = " + team_id + " AND FIND_IN_SET(GAME_ID,'" + games_str + "') > 0;", con = conn)

    trunc_cols = list(r_stats)[6:]
    trunc_cols.insert(0, 'TEAM_ID')
    trunc_cols.insert(1, 'SIDE')
    trunc_cols.insert(2, 'SEQUENCE')

    ## Get averages for each field
	# team averages
    team_stats = pd.DataFrame(data = [[team_id, side, sequence, r_stats['EFG_PCT'].mean(),
                                        r_stats['FTA_RATE'].mean(), r_stats['TM_TOV_PCT'].mean(),
                                        r_stats['OREB_PCT'].mean(), r_stats['OPP_EFG_PCT'].mean(),
                                        r_stats['OPP_FTA_RATE'].mean(), r_stats['OPP_TOV_PCT'].mean(),
                                        r_stats['OPP_OREB_PCT'].mean()]], columns = trunc_cols)

    return team_stats

def format_and_run_daily_stats(dirty_stats):
	unq_sequence = dirty_stats.SEQUENCE.unique()
	preds_cols = ['home_id', 'away_id', 'pred_spread']
	for i in unq_sequence:
		match = dirty_stats[dirty_stats['SEQUENCE'] == i]

		predict = run_daily_algo(match)
		if i == 0:
			daily_preds = pd.DataFrame([predict], columns = preds_cols)
		else:
			temp_daily_preds = pd.DataFrame([predict], columns = preds_cols)
			daily_preds = daily_preds.append(temp_daily_preds)

	# Transform spreads to be in terms of away teams (this is how spreads_scraper pulls the vegas spreads)
	daily_preds['pred_spread'] = daily_preds['pred_spread'].str.replace('-', '+')
	daily_preds['pred_spread'] = np.where(daily_preds['pred_spread'].str.contains("+", regex = False), daily_preds['pred_spread'], "-" + daily_preds['pred_spread'].astype(str))
	daily_preds['pred_spread'] = daily_preds['pred_spread'].str.replace('+', '')

	# Transform back into an integer
	daily_preds['pred_spread'] = pd.to_numeric(daily_preds['pred_spread'])

	return daily_preds

def run_daily_algo(match):
	math_cols = ['efg', 'tov', 'orb', 'ft/fga', 'side']
	home = match[match['SIDE'] == 'home']
	away = match[match['SIDE'] == 'away']
	i = 0
	for s in ['away', 'home']:
		side = match[match['SIDE'] == s]
		efg = (side['EFG_PCT'].item() - side['OPP_EFG_PCT'].item())*100
		tov = (side['TM_TOV_PCT'].item() - side['OPP_TOV_PCT'].item())*100
	 	orb = (100*side['OREB_PCT'].item()) - (100*side['OPP_OREB_PCT'].item())
	 	ftfga = (side['FTA_RATE'].item() - side['OPP_FTA_RATE'].item())*100
		side_list = [efg, tov, orb, ftfga]

		if i == 0:
			side_list.append('away')
			math_df = pd.DataFrame([side_list], columns = math_cols)
		else:
			side_list.append('home')
			temp_math_df = pd.DataFrame([side_list], columns = math_cols)
			math_df = math_df.append(temp_math_df)
		i += 1
	math_df.reset_index()

	efg = ((math_df[math_df['side'] == 'away'])['efg'].item() - (math_df[math_df['side'] == 'home'])['efg'].item())*0.4
	tov = ((math_df[math_df['side'] == 'away'])['tov'].item() - (math_df[math_df['side'] == 'home'])['tov'].item())*0.25
	orb = ((math_df[math_df['side'] == 'away'])['orb'].item() - (math_df[math_df['side'] == 'home'])['orb'].item())*0.2
	ftfga = ((math_df[math_df['side'] == 'away'])['ft/fga'].item() - (math_df[math_df['side'] == 'home'])['ft/fga'].item())*0.15
	pred_spread  = ((efg + tov + orb + ftfga)*2)-2.47

	pred_spread = str(pred_spread)
	pred_final = [home['TEAM_ID'].item(), away['TEAM_ID'].item(), pred_spread]

	return pred_final

def merged_daily_data(daily_preds, daily_vegas):

	daily_final = pd.merge(daily_preds, daily_vegas[['away_team_id', 'home_team_id', 'bovada_line']],
						   left_on = ['home_id', 'away_id'], right_on = ['home_team_id', 'away_team_id'], how = 'left')


	daily_final['vegas_spread'] = daily_final['bovada_line'].str.replace("+","")
	daily_final['vegas_spread'] = pd.to_numeric(daily_final['vegas_spread'])
	daily_final = daily_final.drop(columns = ['home_team_id', 'away_team_id', 'bovada_line'])

	return daily_final

def clean_predictions(daily_final):

	## get team names
    daily_final['away_team'] = daily_final['away_id'].map(teams['nba_teams'])
    daily_final['home_team'] = daily_final['home_id'].map(teams['nba_teams'])

	## get differential
    daily_final['pt_diff'] = daily_final['vegas_spread'] - daily_final['pred_spread']

	## rank games based on score
    daily_final['abs_pt_diff'] = daily_final['pt_diff'].abs()
    daily_final = daily_final.sort_values(by = ['abs_pt_diff'], ascending = False)
    daily_final['rank'] = daily_final['abs_pt_diff'].rank(ascending = False)

	## get pick
    daily_final['pick'] = np.where(daily_final['vegas_spread'] < daily_final['pred_spread'], daily_final['home_team'], daily_final['away_team'])

    daily_final['pick_away'] = np.where(daily_final['pt_diff'] > 0, daily_final['vegas_spread'], "")
    daily_final['pick_away'] = np.where(daily_final['vegas_spread'] < 0, daily_final['pick_away'], "+" + daily_final['pick_away'].apply(str))
    daily_final['pick_home'] = np.where((daily_final['pt_diff'] < 0) & (daily_final['vegas_spread'] < 0),
										daily_final['vegas_spread'].apply(str), "")
    daily_final['pick_home'] = np.where(daily_final['pick_home'] == "", '-' + daily_final['vegas_spread'].apply(str), daily_final['pick_home'].str.replace('-', '+'))

    daily_final['pick_str'] = np.where(daily_final['pt_diff'] > 0, daily_final['pick'] + " (" + daily_final['pick_away'] + ")",
									   daily_final['pick'] + " (" + daily_final['pick_home'] + ")")

    daily_final['vegas_spread'] = np.where(daily_final['vegas_spread'] < 0, daily_final['away_team'] + " (" + daily_final['vegas_spread'].apply(str) + ")",
                                            daily_final['home_team'] + " (-" + daily_final['vegas_spread'].apply(str) + ")")

	## Some cleaning real quick
    clean = daily_final.drop(columns = ['pick', 'pick_away', 'pick_home', 'abs_pt_diff'])
    clean = clean.round({'pt_diff': 2, 'pred_spread': 2})

    ## Get prediction as string
    clean['pred_spread_str'] = np.where(clean['pred_spread'] < 0, clean['away_team'] + " (" + clean['pred_spread'].apply(str) + ")",
                                    clean['home_team'] + " (" + clean['pred_spread'].apply(str) + ")")
    ## Rearrange columns
    clean_cols = clean.columns.tolist()
    final_cols = clean_cols[:2] + clean_cols[-1:] + clean_cols[3:-1] + clean_cols[2:3]
    final = clean[final_cols]

    return final


if __name__ == '__main__':
	main()

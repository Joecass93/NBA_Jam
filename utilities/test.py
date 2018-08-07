import requests
import ast
import json
import pandas as pd
from assets import range_all_dates
from config import teams, seasons
import datetime
import numpy as np
from argparse import ArgumentParser
from os.path import expanduser
from pulls import spreads_scraper

#from merged_data_builder import scoreboard, get_daily_stats
#from pulls import spreads_scraper

def main():
	home = expanduser("~")
	dirty_stats = pd.read_csv("%s/projects/NBA_Jam/dirty_stats_test.csv"%home, sep = ',')

	daily_preds = format_and_run_daily_stats(dirty_stats)
	print daily_preds

	daily_vegas = spreads_scraper.main('20171201')
	print daily_vegas

	daily_final = pd.merge(daily_preds, daily_vegas[['away_team_id', 'home_team_id', 'bovada_line']],
						   left_on = ['home_id', 'away_id'], right_on = ['home_team_id', 'away_team_id'], how = 'left')


	daily_final['vegas_spread'] = daily_final['bovada_line'].str.replace("+","")
	daily_final['vegas_spread'] = pd.to_numeric(daily_final['vegas_spread'])
	daily_final = daily_final.drop(columns = ['home_team_id', 'away_team_id', 'bovada_line'])

	output = clean_predictions(daily_final)

	print output
	return output

def clean_predictions(daily_final):

	## get team names
	# get dataframe of team_ids and abbrevations
	team_cities = pd.DataFrame.from_dict(teams['nba_teams'],
										orient = 'index',
										dtype = 'object',
										columns = ['team'])
	team_cities['team_id'] = team_cities.index
	# merge away teams first
	daily_final = pd.merge(daily_final, team_cities, left_on = 'away_id', right_on = 'team_id', how = 'left')
	daily_final['away_team'] = daily_final['team']
	daily_final = daily_final.drop(columns = ['team_id', 'team'])
	# now merge home teams
	daily_final = pd.merge(daily_final, team_cities, left_on = 'home_id', right_on = 'team_id', how = 'left')
	daily_final['home_team'] = daily_final['team']
	daily_final = daily_final.drop(columns = ['team_id', 'team'])

	## get differential
	daily_final['pt_diff'] = daily_final['vegas_spread'] - daily_final['pred_spread']

	## rank games based on score
	daily_final['abs_pt_diff'] = daily_final['pt_diff'].abs()
	daily_final = daily_final.sort_values(by = ['abs_pt_diff'], ascending = False)
	daily_final['rank'] = daily_final['abs_pt_diff'].rank(ascending = False)
	daily_final = daily_final.drop(columns = ['abs_pt_diff'])

	## get pick
	daily_final['pick'] = np.where(daily_final['vegas_spread'] < daily_final['pred_spread'], daily_final['home_team'], daily_final['away_team'])

	daily_final['pick_away'] = np.where(daily_final['pt_diff'] > 0, daily_final['vegas_spread'], "")
	daily_final['pick_away'] = np.where(daily_final['vegas_spread'] < 0, daily_final['pick_away'], "+" + daily_final['pick_away'].apply(str))
	daily_final['pick_home'] = np.where((daily_final['pt_diff'] < 0) & (daily_final['vegas_spread'] < 0),
										daily_final['vegas_spread'].apply(str), "")
	daily_final['pick_home'] = np.where(daily_final['pick_home'] == "", '-' + daily_final['vegas_spread'].apply(str), daily_final['pick_home'].str.replace('-', '+'))

	daily_final['pick_str'] = np.where(daily_final['pt_diff'] > 0, daily_final['pick'] + " " + daily_final['pick_away'],
									   daily_final['pick'] + " " + daily_final['pick_home'])

	clean = daily_final.drop(columns = ['pick', 'pick_away', 'pick_home'])

	return clean


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
	print math_df
	efg = ((math_df[math_df['side'] == 'away'])['efg'].item() - (math_df[math_df['side'] == 'home'])['efg'].item())*0.4
	tov = ((math_df[math_df['side'] == 'away'])['tov'].item() - (math_df[math_df['side'] == 'home'])['tov'].item())*0.25
	orb = ((math_df[math_df['side'] == 'away'])['orb'].item() - (math_df[math_df['side'] == 'home'])['orb'].item())*0.2
	ftfga = ((math_df[math_df['side'] == 'away'])['ft/fga'].item() - (math_df[math_df['side'] == 'home'])['ft/fga'].item())*0.15
	pred_spread  = ((efg + tov + orb + ftfga)*2)-2.47

	pred_spread = str(pred_spread)
	pred_final = [home['TEAM_ID'].item(), away['TEAM_ID'].item(), pred_spread]



	print pred_final
	return pred_final

if __name__ == "__main__":
	main()

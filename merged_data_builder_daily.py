import pandas as pd
import numpy as np
import datetime
import requests
import json
import time
from utilities.config import teams, spread_teams, request_header
from utilities.assets import list_games
from pulls import spreads_scraper
from os.path import expanduser

## API error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)

## remove when done testing
#gamedate = '2017-11-01'

##
home_dir = expanduser("~")

def main(gamedate = None):

	if gamedate:
		pass
	else:
		gamedate = datetime.date.today().strftime('%Y-%m-%d')

	print "getting matchups for %s..."%gamedate
	matches = todays_matches(gamedate)

	print "getting stats for each team..."
	for i, g in enumerate(matches['GAME_ID']):
		away = matches.VISITOR_TEAM_ID.astype(str)[i]
		home = matches.HOME_TEAM_ID.astype(str)[i]
		print "getting %s: %s @ %s"%(g, away, home)

		almost = cum_ff_stats(away, home, gamedate, i)
		if i == 0:
			todays_ff_cum = almost
		else:
			todays_ff_cum = todays_ff_cum.append(almost)
	todays_ff_cum.to_csv("dirty_stats_test.csv", sep=',')

	print "formatting stats..."
	daily_preds = format_and_run_daily_stats(todays_ff_cum)

	print "getting todays spreads..."
	daily_vegas = spreads_scraper.main('20171101')
	print daily_vegas

	print "merging data..."
	merged_data = merged_daily_data(daily_preds, daily_vegas)
	print merged_data

	print "making predictions..."
	output = clean_predictions(merged_data)

	output.to_csv('%s/projects/NBA_Jam/test_daily.csv'%home_dir, sep = ',')

	print output
	return output

def todays_matches(gamedate):
	gamedate = datetime.datetime.strptime(gamedate, '%Y-%m-%d')
	gamedate= gamedate.strftime('%m/%d/%Y')
	gamedate = '11/01/2017' ## Remove when done testing
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

	x = 0
	games_today = []
	# Loop through and get each game's info
	for x in range(0,scoreboard_len):
		game_info = cleaner['rowSet'][x]
		games_today.append(game_info)
		x = x + 1

	# Create dataframe containing info about today's game
	df_matches = pd.DataFrame(games_today, columns = col_names)


	return df_matches

## Need to get four factors stats at current point in season
def cum_ff_stats(away_id, home_id, gamedate, sequence):
	ff_list = []

	away_stats_list = []
	home_stats_list = []

	## Get the list of game_ids for games played so far by each team
	away_g = list_games(away_id, gamedate)
	home_g = list_games(home_id, gamedate)

	## Get away teams data first
	for ag in away_g:
		try:
			time.sleep(3)
			a_games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%ag
			response = sess.get(a_games_url, headers=request_header)
			data = response.text
			data = json.loads(data)
			cleaner = data['resultSets']
			cleanest = cleaner[1]
			col_names = cleanest['headers']
			away_data = cleanest['rowSet']

			if away_id in away_data[0]:
				away_data_daily = away_data[0]
			else:
				away_data_daily = away_data[1]
			away_stats_list.append(away_data_daily)
		except Exception as e:
			print e


	## Circle back and get data for the home team
	for hg in home_g:
		try:
			time.sleep(3)
			h_games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%hg
			response = sess.get(h_games_url, headers = request_header)
			data = response.text
			data = json.loads(data)
			cleaner = data['resultSets']
			cleanest = cleaner[1]
			col_names = cleanest['headers']
			home_data = cleanest['rowSet']

			if home_id in home_data[0]:
				home_data_daily = home_data[0]
			else:
				home_data_daily = home_data[1]
			home_stats_list.append(home_data_daily)
		except Exception as e:
			print e

	a = pd.DataFrame(away_stats_list, columns = col_names)
	h = pd.DataFrame(home_stats_list, columns = col_names)

	trunc_col_names = col_names[6:]
	trunc_col_names.insert(0, 'TEAM_ID')
	trunc_col_names.insert(1, 'SIDE')
	trunc_col_names.insert(2, 'SEQUENCE')
	## Get averages for each field
	# away averages
	away_stats = pd.DataFrame(data = [[away_id, 'away', sequence, a['EFG_PCT'].mean(),
								a['FTA_RATE'].mean(), a['TM_TOV_PCT'].mean(),
								a['OREB_PCT'].mean(), a['OPP_EFG_PCT'].mean(),
								a['OPP_FTA_RATE'].mean(), a['OPP_TOV_PCT'].mean(),
								a['OPP_OREB_PCT'].mean()]], columns = trunc_col_names)

	# home averages
	home_stats = pd.DataFrame(data = [[home_id, 'home', sequence, h['EFG_PCT'].mean(),
								h['FTA_RATE'].mean(), h['TM_TOV_PCT'].mean(),
								h['OREB_PCT'].mean(), h['OPP_EFG_PCT'].mean(),
								h['OPP_FTA_RATE'].mean(), h['OPP_TOV_PCT'].mean(),
								h['OPP_OREB_PCT'].mean()]], columns = trunc_col_names)

	# Append home and away stats
	stats = home_stats.append(away_stats)
	print stats
	return stats

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


if __name__ == '__main__':
	main('2017-11-01')

import pandas as pd 
import numpy as np 
import requests
import json
from utilities.assets import range_all_dates
from utilities.config import teams, seasons, request_header
from pulls import spreads_scraper
from argparse import ArgumentParser
import datetime


parser = ArgumentParser()
parser.add_argument("-t", "--only_today", help = "either enter 'yes', or skip for a defined date range")
parser.add_argument("-ss", "--start_season", help="season to start pulling final scores data from: ex. 2000-01", type=str, required=False)
parser.add_argument("-es", "--end_season", help = "season to end pulling final scores data from: ex. 2000-01", type=str, required=False)


## ThIs iS JuSt FoR tEsTiNG
#gameday = ['12/01/2017', '12/02/2017']
#gameday_reform = ['20171201', '20171202']

flags = parser.parse_args()

if flags.start_season:
	sdate = seasons['start_date'].get(flags.start_season)
else:
	sdate = datetime.datetime.now()
	sdate = '2017-12-01'
if flags.end_season:
	edate = seasons['end_date'].get(flags.end_season)
else:
	edate = datetime.datetime.now()
	edate = '2017-12-01'

gameday = range_all_dates(sdate, edate)
gameday_reform = []
for m in gameday:
	reformat_date = datetime.datetime.strptime(m, "%Y/%m/%d").strftime("%Y%m%d")
	gameday_reform.append(reformat_date)


def main():
	print "Getting scores..."
	for j, a in enumerate(gameday):
		print a
		try:
			games = scoreboard(a)
			if j == 0:
				games_all = games
			else:
				games_all = games_all.append(games)
		except:
			pass

	print "Getting spreads..."
	for k, b in enumerate(gameday_reform):
		print b
		try:
			spreads = spreads_scraper.main(b)
			if k == 0:
				spreads_all = spreads
			else:
				spreads_all = spreads_all.append(spreads)
		except:
			pass

	print "Getting stats..."
	daily_data = get_daily_stats(games_all)

	print "Creating merged dataset..."
	merged = merge_stats_and_spreads(games_all, daily_data, spreads_all)

	print merged
	merged.to_csv('merged_data_file.csv', sep =',')
	return merged


### Start by importing list of today's matchups
def scoreboard(gameday):

	scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%gameday
	response = requests.get(scoreboard_url, headers=request_header)
	data = response.text
	data = json.loads(data)
	if gameday == datetime.date.today().strftime("%m/%d/%Y"):
		# Pull just pre-game data
		cleaner = data['resultSets']
		cleaner = cleaner[0]
	else: 
		cleaner = data['resultSets']
		cleaner = cleaner[1]

	col_names = cleaner['headers']
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
	df = pd.DataFrame(games_today, columns = col_names)

	if gameday == datetime.date.today().strftime("%m/%d/%Y"):
		# do nothing
		print "only today's games"
	else:
		df['SIDE'] = "away"
		df.loc[1::2, "SIDE"] = "home"
		df_home = df[df['SIDE'] == "home"]
		df_away = df[df['SIDE'] == "away"]

		df = df_home.merge(df_away, how = 'left', on = 'GAME_ID', suffixes = ['_HOME', '_AWAY'])
		df['HOME_TEAM_ID'] = df['TEAM_ID_HOME']
		df['AWAY_TEAM_ID'] = df['TEAM_ID_AWAY']
		df = df.drop(columns = ['TEAM_ID_AWAY', 'TEAM_ID_HOME'])
	return df

### Loop through each of today's games and get stats for each team
def get_daily_stats(input_table):
	four_factors_list = []
	## Make API call and build resulting dataframe
	#col_names = ['TEAM_ID', 'EFG_PCT', 'FTA_RATE', 'TM_TOV_PCT', 'OREB_PCT', 'OPP_EFG_PCT', 'OPP_FTA_RATE', 'OPP_TOV_PCT', 'OPP_OREB_PCT']
	for g in input_table['GAME_ID']:
		print "getting %s"%g
		games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
		response = requests.get(games_url, headers=request_header)
		## Data cleaning
		data = response.text
		data = json.loads(data)
		cleaner = data['resultSets']
		cleanest = cleaner[1]
		col_names = cleanest['headers']
		try:
			stats1 = cleanest['rowSet'][0]
			stats2 = cleanest['rowSet'][1]
			four_factors_list.append(stats1)
			four_factors_list.append(stats2)
		except Exception as e:
			print e
	ff_daily = pd.DataFrame(four_factors_list, columns = col_names)
	# Test dataframe, remove this later
	# ff_daily = daily_stats_pull.main()

	# ff_daily = pd.read_csv('daily_ff_test.csv', sep = ',', header = 0)
	## Do some data cleaning on the four factors dataframe here
	for i, y in enumerate(input_table['GAME_ID']):
		match = input_table[input_table['GAME_ID'] == y]
		home = match['HOME_TEAM_ID'].item()
		home_d = match['GAME_ID'].item()
		visitor = match['AWAY_TEAM_ID'].item()
		visitor_d = match['GAME_ID'].item()
		
		daily_home = ff_daily[(ff_daily['TEAM_ID'] == home) & (ff_daily['GAME_ID'] == home_d)]
		daily_away = ff_daily[(ff_daily['TEAM_ID'] == visitor) & (ff_daily['GAME_ID'] == visitor_d)]
		
		# add game number and home/away column
		daily_home['GAME_NUM'] = i
		daily_away['GAME_NUM'] = i
		daily_home['SIDE'] = "home"
		daily_away['SIDE'] = "away"

		if i == 0:
			col_names1 = list(daily_home.columns.values)
			daily_full = pd.DataFrame(daily_home, columns = col_names1)
			daily_full = daily_full.append(daily_away)
		else:
			daily_full = daily_full.append(daily_home)
			daily_full = daily_full.append(daily_away)

	daily_full_home = daily_full[daily_full['SIDE'] == "home"]
	daily_full_away = daily_full[daily_full['SIDE'] == "away"]

	daily_full_scores = daily_full_home.merge(daily_full_away, how = "left", on = "GAME_ID", suffixes = ['_HOME', '_AWAY'])

	return daily_full_scores

### Merge spreads data with team stats
def merge_stats_and_spreads(scores, daily_data, spreads):
	## Merge box score and four factors data
	# Remove some unneeded columns from box score
	scores = scores.drop(columns = ['TEAM_NAME_HOME', 'TEAM_ABBREVIATION_HOME', 'TEAM_CITY_NAME_HOME',
									'TEAM_NAME_AWAY', 'TEAM_ABBREVIATION_AWAY', 'TEAM_CITY_NAME_AWAY',
									'SIDE_HOME', 'SIDE_AWAY', 'GAME_DATE_EST_AWAY'])
	daily_data = daily_data.drop(columns = ['SIDE_HOME', 'SIDE_AWAY'])
	# merge the dataframs
	stats = scores.merge(daily_data, how = 'left', on = 'GAME_ID')
	stats['GAME_DATE'] = (pd.to_datetime(stats['GAME_DATE_EST_HOME'])).astype(str)
	stats['GAME_DATE'] = stats['GAME_DATE'].replace('-', '', regex = True)
	print stats
	## Merge box score/ff data and spread data (using date, and team ids)

	full_merged = stats.merge(spreads, how = 'left', left_on = ['GAME_DATE','TEAM_ID_HOME', 'TEAM_ID_AWAY'], right_on = ['date', 'home_team_id', 'away_team_id'])

	return full_merged
### Math stuffs
def run_algorithm():


	return None 

### Formatting of output 
def format_daily_output():


	return None

if __name__ == '__main__':
	main()
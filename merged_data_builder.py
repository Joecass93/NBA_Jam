import pandas as pd 
import numpy as np 
import requests
import json
from utilities.config import teams, seasons, request_header
from pulls import spreads_scraper
from argparse import ArgumentParser
import datetime


parser = ArgumentParser()
parser.add_argument("-t", "--only_today", help = "either enter 'yes', or skip for a defined date range")
parser.add_argument("-s", "--start_season", help="season to start pulling final scores data from: ex. 2000-01", type=str, required=False)
parser.add_argument("-e", "--end_season", help = "season to end pulling final scores data from: ex. 2000-01", type=str, required=False)


## ThIs iS JuSt FoR tEsTiNG
gameday = '12/01/2017'

### Main function here
def main():
	games = scoreboard(gameday)
	print games
	daily_data = get_daily_stats(games)
	spreads = spreads_scraper.main()

	print daily_data


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

	return df

### Loop through each of today's games and get stats for each team
def get_daily_stats(input_table):

	# Test dataframe, remove this later
	# ff_daily = daily_stats_pull.main()

	ff_daily = pd.read_csv('daily_ff_test.csv', sep = ',', header = 0)

	for i, y in enumerate(input_table['GAME_ID']):
		match = input_table[input_table['GAME_ID'] == y]
		home = match['HOME_TEAM_ID'].item()
		visitor = match['VISITOR_TEAM_ID'].item()	
		
		daily_home = ff_daily[ff_daily['TEAM_ID'] == home]
		daily_away = ff_daily[ff_daily['TEAM_ID'] == visitor]
		
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

	return daily_full

### Merge spreads data with team stats
def merge_stats_and_spreads(spreads, daily_data):

	return None
### Math stuffs
def run_algorithm():


	return None 

### Formatting of output 
def format_daily_output():


	return None

if __name__ == '__main__':
	main()
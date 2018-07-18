import pandas as pd 
import numpy as np 
import requests
import json
from utilities.config import teams, seasons, request_header


## ThIs iS JuSt FoR tEsTiNG
gameday = '12/01/2017'

### Main function here
def main():
	games = scoreboard(gameday)
	daily_data = get_daily_stats(games)

	print daily_data


### Start by importing list of today's matchups
def scoreboard(date):
	scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%gameday
	response = requests.get(scoreboard_url, headers=request_header)
	data = response.text
	data = json.loads(data)

	# Pull just pre-game data
	cleaner = data['resultSets']
	cleanest = cleaner[0]
	col_names = cleanest['headers']

	# Check how many games there are today
	scoreboard_len = len(cleanest['rowSet'])
	x = 0
	games_today = []

	# Loop through and get each game's info
	for x in range(0,scoreboard_len):
		game_info = cleanest['rowSet'][x]
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




### Math stuffs




### Formatting of output 

if __name__ == '__main__':
	main()
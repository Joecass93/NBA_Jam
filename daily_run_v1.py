import pandas as pd 
import numpy as np 
import requests
import json
from utilities.config import teams, seasons, request_header


### Start by importing list of today's matchups

gameday = '12/01/2017'
def scoreboard(date = gameday):
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


	df = pd.DataFrame(games_today, columns = col_names)
	
	print df

	return df



### Loop through each of today's games and get stats for each team





### Math stuffs




### Formatting of output 

if __name__ == '__main__':
	scoreboard()
import requests
import ast
import json
import pandas as pd

##### Constants ######
## Request header
request_header = {'Connection': 'keep-alive',
'Cache-Control': 'max-age=0',
'Upgrade-Insecure-Requests': '1',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'en-US,en;q=0.9',
                 }
## Team IDs
teams = pd.read_csv('teams.csv', sep=',')
teams = list(teams)

## Game IDs for 2017-18 season
#season = raw_input('What season? ')
games = pd.read_csv('FinalScores2010-2018.csv', sep=',')
games = games[games['GAME_DATE_EST'] >= '2017-10-17T00:00:00']
games = games['GAME_ID'].tolist()
games = list(set(games))

# Add 00 to beginning of all game ids, in order to match formatting
games = ['00' + str(x) for x in games]

###### Get four factors stats by game #####

## API Call
test = ['0021700609', '0021700610', '0021700611']
four_factors_list = []
for g in games:
	games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
	response = requests.get(games_url, headers=request_header)

	## Data cleaning
	data = response.text
	data = json.loads(data)
	cleaner = data['resultSets']
	cleanest = cleaner[1]
	col_names = cleanest['headers']
	stats1 = cleanest['rowSet'][0]
	stats2 = cleanest['rowSet'][1]
	four_factors_list.append(stats1)
	four_factors_list.append(stats2)

## Create dataframe containing four factors data by game by team
four_factors = pd.DataFrame(four_factors_list, columns = col_names)
four_factors.to_csv("four_factors_stats.csv")




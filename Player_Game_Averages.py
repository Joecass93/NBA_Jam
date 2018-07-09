import requests
import ast
import json
import pandas as pd


## Info needed to make api call
url = 'http://stats.nba.com/stats/commonallplayers?LeagueID=00&Season=2017-18&IsOnlyCurrentSeason=0'
request_header = {'Connection': 'keep-alive',
'Cache-Control': 'max-age=0',
'Upgrade-Insecure-Requests': '1',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'en-US,en;q=0.9',
                 }
response = requests.get(url, headers = request_header)
data = response.text

new_data = json.loads(data)

first = new_data['resultSets']

col_names = []
for w in first:
    for col in w['headers']:
        col_names.append(col)
        
list = []        
for x in first:
   for z in x['rowSet']:
       list.append(z)

df = pd.DataFrame(list, columns = col_names)

## Limit to only recent players
seasons = ['2010','2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018']
players_df = df[df['TO_YEAR'].isin(seasons)]
currentplayers_df = df[df['TO_YEAR'] == '2018']

## Get gamelogs for a given player
# List of active player IDs
player_ids = currentplayers_df['PERSON_ID'].tolist()
player_ids = ['1628389', '201167', '203500']

for p in player_ids:
	print p
	gamelog_url = 'http://stats.nba.com/stats/playergamelogs?%s&Season=2017-18&SeasonType=Regular Season'%(p) 
	response = requests.get(gamelog_url, headers = request_header)
	gamelogs_data = response.text
	gamelogs_data = json.loads(gamelogs_data)
	first = gamelogs_data['resultSets']

	col_names = []
	for w in first:
	    for col in w['headers']:
	        col_names.append(col)

	list = []        
	for x in first:
	   for z in x['rowSet']:
	       list.append(z)

	currentplayer_df = pd.DataFrame(list, columns = col_names)


import requests
import ast
import json
import pandas as pd
import numpy as np
from utilities.config import teams, seasons
from argparse import ArgumentParser
from datetime import datetime

######### Constants ############

## Get most recent season ##
now = datetime.now()
curr_year = str(now.year)
last_year = str(now.year - 1)
curr_season = "%s-%s"%(last_year, curr_year[2:])

## Command line argument parsing ##
parser = ArgumentParser()
parser.add_argument("-s", "--start_season", help="season to start pulling final scores data from: ex. 2000-01", type=str, required=False)
parser.add_argument("-e", "--end_season", help = "season to end pulling final scores data from: ex. 2000-01", type=str, required=False)

flags = parser.parse_args()

if flags.start_season:
	first = flags.start_season
else:
	first = '2000-01'

if flags.end_season:
	second = flags.end_season
else:
	second = curr_season

## Request header
request_header = {'Connection': 'keep-alive',
'Cache-Control': 'max-age=0',
'Upgrade-Insecure-Requests': '1',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate',
'Accept-Language': 'en-US,en;q=0.9',
                 }
## Get Team IDs
team_list = list(teams['nba_teams'].keys())

################################

######### Functions ############
def scores_by_season(start_season = '2000-01', end_season = curr_season):
	# Get start date of the start season selected
	sdate = "%sT00:00:00"%seasons['start_date'].get(start_season)
	print sdate
	# Get end date of the end season selected
	edate = "%sT00:00:00"%seasons['end_date'].get(end_season) 
	print edate
	# Import Final Scores data
	games = pd.read_csv('Data/FinalScores2010-2018.csv', sep=',', index_col = False)
	# Slice the dataframe to get only games from the range selected
	games = games[(games['GAME_DATE_EST'] >= sdate) & (games['GAME_DATE_EST'] <= edate)]
	# Return only regular season games from this time span
	games['GAME_ID'] = "00" + games['GAME_ID'].astype(str)
	games = games[games['GAME_ID'].astype(str).str.contains("002")]

	return games

################################

print "getting final score data for %s to %s seasons"%(first, second)
games = scores_by_season(start_season = first, end_season = second)
# Get list of game ids from the final score dataframe
game_ids = games['GAME_ID'].tolist()
game_ids = list(set(game_ids))

###### Get four factors stats by game #####
## API Call
print "getting four factors data by game for %s to %s seasons %s"%(first, second, datetime.time(datetime.now()))
four_factors_list = []
counter = 0
for g in game_ids:
	games_url = 'https://stats.nba.com/stats/boxscorefourfactorsv2?StartPeriod=1&StartRange=0&EndPeriod=10&EndRange=2147483647&GameID=%s&RangeType=0'%g
	response = requests.get(games_url, headers=request_header)
	counter = counter + 1
	## Data cleaning
	data = response.text
	data = json.loads(data)
	cleaner = data['resultSets']
	cleanest = cleaner[1]
	col_names = cleanest['headers']
	print counter
	try:
		stats1 = cleanest['rowSet'][0]
		stats2 = cleanest['rowSet'][1]
		four_factors_list.append(stats1)
		four_factors_list.append(stats2)
	except Exception as e:
		print data 
		print e

## Create dataframe containing four factors data by game by team, and save as csv
print "Creating dataframe from four factors data %s"%(datetime.time(datetime.now()))
four_factors = pd.DataFrame(four_factors_list, columns = col_names)
four_factors.to_csv("Data/four_factors_stats_%s-%s.csv"%(first, second))

## Join the two dataframes and clean data
# Join data on GAME_ID and TEAM_ID
df = games.merge(four_factors, how = 'inner', on = ['GAME_ID', 'TEAM_ID'])
# Remove/Rename columns
df['TEAM_ABBREVIATION'] = df['TEAM_ABBREVIATION_x']
df = df.drop(['TEAM_ABBREVIATION_x', 'TEAM_ABBREVIATION_y', 'TEAM_NAME', 'TEAM_CITY'], axis=1)

print "creating WL and point differential columns %s"%(datetime.time(datetime.now()))
# Create some columns
for i, x in enumerate(game_ids):
    temp = df[df['GAME_ID'] == x]
    try:
	    home_score = temp['PTS'].iloc[0]
	    home_id = temp['TEAM_ID'].iloc[0]
	    away_score = temp['PTS'].iloc[1]
	    away_id = temp['TEAM_ID'].iloc[1]

	    # Create win loss & point differential columns and determine winner of each game
	    if home_score > away_score:
	        temp['WL'] = np.where(temp['TEAM_ID'] == home_id, "w", "l")
	        temp['PTDIFF'] = np.where(temp['TEAM_ID'] == home_id, home_score - away_score, away_score - home_score)
	    else:
	        temp['WL'] = np.where(temp['TEAM_ID'] == away_id, 'w', 'l')
	        temp['PTDIFF'] = np.where(temp['TEAM_ID'] == away_id, away_score - home_score, home_score - away_score)
	    
	    # Build dataframe containing every game
	    if i == 0:
	        final = temp
	    else:
	        final = final.append(temp)
    except Exception as e:
		print e

# Print merged data to csv
print "saving dataframe as csv %s"%(datetime.time(datetime.now()))
final.to_csv('Data/four_factors_final_%s-%s.csv'%(first, second), sep=',')






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
print (games[1])
## API Call
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
## Write dataframe to csv
#four_factors.to_csv("four_factors_stats.csv")

#### Merge with game final score data
# Import final score data
s_df = pd.read_csv('FinalScores2010-2018.csv', sep = ',')

# Fix GAME_ID by appending 00 to start of each
s_df['GAME_ID'] = "00" + s_df['GAME_ID'].astype(str)

# Limit to just 2017-18 season
s_df = s_df[s_df['GAME_ID'].str.contains("00217")]

## Join the two dataframes and clean data
# Join data on GAME_ID and TEAM_ID
df = s_df.merge(four_factors, how = 'inner', on = ['GAME_ID', 'TEAM_ID'])

# Remove/Rename columns
df['TEAM_ABBREVIATION'] = df['TEAM_ABBREVIATION_x']
df = df.drop(['Unnamed: 0_x', 'Unnamed: 0_y', 'TEAM_ABBREVIATION_x', 'TEAM_ABBREVIATION_y', 'TEAM_NAME', 'TEAM_CITY'], axis=1)

# Create some columns
game_ids = df['GAME_ID'].tolist()
game_ids = list(set(game_ids))

for i, x in enumerate(game_ids):
    temp = df[df['GAME_ID'] == x]
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

# Print merged data to csv
final.to_csv('four_factors_final.csv', sep=',')






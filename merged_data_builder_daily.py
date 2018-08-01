import pandas as pd
import numpy as np
import datetime
import requests
import json
import time
from utilities.config import teams, spread_teams, request_header
from utilities.assets import list_games

## API error handling
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
sess.mount('http://', adapter)


def main():
	print "getting today's matchups..."
	matches = todays_matches()

	## remove when done testing
	gamedate = '2017-11-01'

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


	print todays_ff_cum
	return matches

def todays_matches():
	today = datetime.date.today()
	today = today.strftime("%m/%d/%Y")
	today = '12/01/2017'
	try:
		scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%today
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
## Get four factors stats from each game that a team played so far????
## Is there an nba api endpoint with stats up to a certain point in a season???
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



if __name__ == '__main__':
	main()

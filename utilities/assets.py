from datetime import date, timedelta, datetime
import pandas as pd
from os.path import expanduser
from db_connection_manager import establish_db_connection
from config import seasons, request_header
import requests
import json

home = expanduser("~")

## Enter dates as string of format 'YYYY-MM-DD'
def range_all_dates(start_date, end_date):
	date_range_list = []
	start_date = datetime.strptime(start_date, "%Y-%m-%d")
	end_date = datetime.strptime(end_date, "%Y-%m-%d")
	for n in range(int ((end_date - start_date).days)+1):
		d = start_date + timedelta(n)
		d = d.strftime("%Y-%m-%d")
		date_range_list.append(d)

	return date_range_list

def games_daily(gamedate): ## Get dataframe containing basic information about NBA games that occurred or are occurring on a given date
	gamedate = datetime.strptime(gamedate, '%Y-%m-%d')
	gamedate = gamedate.strftime('%m/%d/%Y')
	try:
		scoreboard_url = 'http://stats.nba.com/stats/scoreboardV2?GameDate=%s&LeagueID=00&DayOffset=0'%gamedate
		response = requests.get(scoreboard_url, headers=request_header)
		data = json.loads(response.text)
		cleaner = data['resultSets'][0]
		col_names = cleaner['headers']
	except requests.ConnectionError as e:
		print e

	# Check how many games there are today
	scoreboard_len = len(cleaner['rowSet'])

	# Loop through and get each game's info
	games_today = []
	for x in range(0,scoreboard_len):
		game_info = cleaner['rowSet'][x]
		games_today.append(game_info)

	# Create dataframe containing info about today's game
	df_matches = pd.DataFrame(games_today, columns = col_names)

	return df_matches

## Get list of game_ids for each game played by a team up to a specified point in seasons (not including the defined date)
# Enter date as string YYYY-MM-DD
def list_games(team_id, date, start_date = None):
	clean_date = datetime.strptime(date, '%Y-%m-%d').date()
	engine = establish_db_connection('sqlalchemy')
	conn = engine.connect()
	data = pd.read_sql("SELECT * FROM final_scores", con = conn)
	if start_date is None:
		start_date = '2018-10-16'

	start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
	data = data[data['game_date'] >= start_date]
	trunc_data = data[data['game_date'] < clean_date]
	trunc_data['away_id'] = trunc_data['away_id'].astype(str)
	trunc_data['home_id'] = trunc_data['home_id'].astype(str)
	team_data = trunc_data[(trunc_data['away_id'] == team_id) | (trunc_data['home_id'] == team_id)].copy()
	games_list = team_data['game_id'].tolist()

	return games_list

def season_from_date_str(gamedate):

	gamedate = datetime.strptime(gamedate, "%Y-%m-%d").date()

	seasons_list = ['2000-01', '2001-02', '2002-03', '2003-04', '2004-05', '2005-06', '2006-07',
					'2007-08', '2009-10', '2010-11', '2011-12', '2012-13', '2013-14', '2014-15',
					'2015-16', '2016-17', '2017-18', '2018-19']

	season_start = seasons['start_date']
	season_end = seasons['end_date']

	#inv_season_start = {v: k for k, v in seasons['start_date'].iteritems()}
	#inv_season_end = {v: k for k, v in seasons['end_date'].iteritems()}

	for ding in seasons_list:

		ding_start = season_start.get(ding)
		ding_start = datetime.strptime(ding_start, "%Y-%m-%d").date()
		ding_end = season_end.get(ding)
		ding_end = datetime.strptime(ding_end, "%Y-%m-%d").date()

		if (gamedate >= ding_start) and (gamedate <= ding_end):
			season = ding
		else:
			pass

	return season

def round_to_nearest(x, base):
	return int(base * round(float(x)/base))

def upload_to_db(data, tbl, append = False):
	conn = establish_db_connection('sqlalchemy').connect()
	if append == True:
		data.to_sql(tbl, con = conn, if_exists = 'append', index = False)
	else:
		data.to_sql(tbl, con = conn, if_exists = 'replace', index = False)


if __name__ == "__main__":
	main()

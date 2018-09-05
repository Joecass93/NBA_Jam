from datetime import date, timedelta, datetime
import pandas as pd
from os.path import expanduser
from db_connection_manager import establish_db_connection
from config import seasons

home = expanduser("~")

def main():
	games = list_games('1610612738', '2017-11-01')
	print games
	return games

## Enter dates as string of format 'YYYY-MM-DD'
def range_all_dates(start_date, end_date):
	date_range_list = []
	start_date = datetime.strptime(start_date, "%Y-%m-%d")
	end_date = datetime.strptime(end_date, "%Y-%m-%d")
	print "first %s"%start_date
	print "second %s"%end_date
	for n in range(int ((end_date - start_date).days)+1):
		d = start_date + timedelta(n)
		d = d.strftime("%Y-%m-%d")
		date_range_list.append(d)
	return date_range_list

## Get list of game_ids for each game played by a team up to a specified point in seasons (not including the defined date)
# Enter date as string YYYY-MM-DD
def list_games(team_id, date):
	## Transform date from string
	clean_date = datetime.strptime(date, '%Y-%m-%d').date()

	# Get games from db
	engine = establish_db_connection('sqlalchemy')
	conn = engine.connect()
	data = pd.read_sql("SELECT * FROM final_scores", con = conn)

	## Replace this with some intelligent method of knowing the start date of the season in which the user-inputed date exists
	tdate = '2017-10-17'
	tdate = datetime.strptime(tdate, '%Y-%m-%d').date()
	data = data[data['GAME_DATE_EST'] >= tdate]

	## Limit data based on specified date
	trunc_data = data[data['GAME_DATE_EST'] < clean_date]

	## Limit data to just the selected team
	trunc_data['TEAM_ID'] = trunc_data.TEAM_ID.astype(str)
	team_data = trunc_data[trunc_data['TEAM_ID'] == team_id]

	games_list = team_data['GAME_ID'].tolist()

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

if __name__ == "__main__":
	main()

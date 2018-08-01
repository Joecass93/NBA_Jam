from datetime import date, timedelta, datetime
import pandas as pd
from os.path import expanduser

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
		d = d.strftime("%Y/%m/%d")
		date_range_list.append(d)
	return date_range_list

## Get list of game_ids for each game played by a team up to a specified point in seasons
def list_games(team_id, date):
	## Transform date
	xdate = "%sT00:00:00"%date
	clean_date = datetime.strptime(xdate, '%Y-%m-%dT%H:%M:%S')

	## Navigate to table containing the correct season's full box score dataset
	# Replace this with database connection eventually.....
	data = pd.read_csv(("%s/projects/NBA_Jam/Data/FinalScores2010-2018.csv")%home, sep =',')

	## Comment these section out once database integration takes place
	data['GAME_DATE_EST'] = pd.to_datetime(data['GAME_DATE_EST'])
	tdate = "2017-10-17T00:00:00"
	clean_tdate = datetime.strptime(tdate, '%Y-%m-%dT%H:%M:%S')
	data = data[data['GAME_DATE_EST'] >= tdate]

	## Limit data based on specified date
	trunc_data = data[data['GAME_DATE_EST'] <= clean_date]

	## Limit data to just the selected team
	trunc_data['TEAM_ID'] = trunc_data.TEAM_ID.astype(str)
	team_data = trunc_data[trunc_data['TEAM_ID'] == team_id]

	games_list = ["00" + str(x) for x in team_data['GAME_ID']]

	return games_list

if __name__ == "__main__":
	main()

import sqlalchemy
from datetime import datetime, date, timedelta
import pandas as pd

def establish_db_connection(connection_package, db):

	if db == 'moneyteam':
		engine = sqlalchemy.create_engine('mysql://' + 'moneyteamadmin' + ':' + 'moneyteam2018' +
			'@' + 'nba-jam.c5tgdlkxq25p.us-east-2.rds.amazonaws.com' + ':' + '3306' + '/nba_master', encoding='utf-8')

		return engine
	elif db == 'nbaapi':
		engine = sqlalchemy.create_engine('mysql://' + 'nbajamadmin' + ':' + 'moneyteam2018' +
			'@' + 'aas6wo5k9lybv0.c5tgdlkxq25p.us-east-2.rds.amazonaws.com' + ':' + '3306' + '/nba_api', encoding='utf-8')

		return engine
	else:
		raise ValueError('Invalid connection package - ' + str(connection_package) )

## Get list of game_ids for each game played by a team up to a specified point in seasons (not including the defined date)
# Enter date as string YYYY-MM-DD
def list_games(team_id, date, start_date = None):
	## Transform date from string
	clean_date = datetime.strptime(date, '%Y-%m-%d').date()

	# Get games from db
	conn = establish_db_connection('sqlalchemy', 'moneyteam').connect()

	if start_date is None:
		start_date = '2018-10-16'

	sql_str = "SELECT * FROM historical_scores_table WHERE (home_id = '%s' OR away_id = '%s') AND game_date >= '%s' AND game_date < '%s'"%(team_id, team_id, start_date, date)
	team_data = pd.read_sql(sql_str, con = conn)

	games_list = team_data['game_id'].tolist()

	return games_list


teams = {
		 '1610612737': 'ATL',
		 '1610612738': 'BOS',
		 '1610612739': 'CLE',
		 '1610612740': 'NOP',
		 '1610612741': 'CHI',
		 '1610612742': 'DAL',
		 '1610612743': 'DEN',
		 '1610612744': 'GSW',
		 '1610612745': 'HOU',
		 '1610612746': 'LAC',
		 '1610612747': 'LAL',
		 '1610612748': 'MIA',
		 '1610612749': 'MIL',
		 '1610612750': 'MIN',
		 '1610612751': 'BKN',
		 '1610612752': 'NYK',
		 '1610612753': 'ORL',
		 '1610612754': 'IND',
		 '1610612755': 'PHI',
		 '1610612756': 'PHX',
		 '1610612757': 'POR',
		 '1610612758': 'SAC',
		 '1610612759': 'SAS',
		 '1610612760': 'OKC',
		 '1610612761': 'TOR',
		 '1610612762': 'UTA',
		 '1610612763': 'MEM',
		 '1610612764': 'WAS',
		 '1610612765': 'DET',
		 '1610612766': 'CHA'
		 }

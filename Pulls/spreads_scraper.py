from urllib import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import requests
import datetime
from datetime import date, timedelta
import time
import sys
sys.path.insert(0, "/Users/joe/projects/NBA_Jam/")
from utilities.config import spread_teams
#from config import spread_teams

## gameday should be str of format 'YYYY-MM-DD'
def main(gameday = None):
	## User enters start date of range
	if gameday:
		gameday = datetime.datetime.strptime(gameday, '%Y-%m-%d')
		gameday = gameday.strftime('%Y%m%d')
		gameday = datetime.datetime.strptime(gameday, '%Y%m%d')
		start_date = gameday
		end_date = gameday
	else:
		try:
			start_date = raw_input("Select a start date for the scraper (leave blank to get today's spreads): ")
			start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
			end_date = raw_input("Select an end date for the scraper: ")
			end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
		except ValueError:
			start_date = datetime.date.today()
			start_date = start_date.strftime("%Y%m%d")
			start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
			end_date = start_date
		start_date = start_date.date()
		end_date = end_date.date()

	print "getting spreads from %s to %s"%(start_date, end_date)

	## Get all dates from user-defined range
	date_range = range_all_dates(start_date, end_date)

	## Scrape all of the spread data from the date range
	for i, d in enumerate(date_range):
		try:
			soup_rl, time_rl = get_spread_soup('Spreads', d)
			games = parse_spread_data(soup_rl, d, time_rl)
			if i == 0:
				spreads = games
			else:
				spreads = spreads.append(games)
			spreads_final = format_spreads_data(spreads)
		except Exception as e:
			print "no games on %s"%d
			print "or %s"%e
			empty_spreads = pd.DataFrame(columns = ['date','time','side',
                         'team','opp_team','pinnacle_line','pinnacle_odds',
                         '5dimes_line','5dimes_odds',
                         'heritage_line','heritage_odds',
                         'bovada_line','bovada_odds',
                         'betonline_line','betonline_odds', 'away_team_id',
                         'home_team_id']
                         )
			if i == 0:
				spreads = empty_spreads
			else:
				spreads.append(empty_spreads)
			spreads_final = spreads

	return spreads_final


def get_spread_soup(type_of_line, tdate = str(date.today()).replace('-','')):

	if type_of_line == 'Spreads':
		url_addon = ''
	elif type_of_line == 'ML':
		url_addon = 'money-line/'
	elif type_of_line == 'Totals':
		url_addon = 'totals/'


	url = "https://classic.sportsbookreview.com/betting-odds/nba-basketball/%s?date=%s"%(url_addon, tdate)
	now = datetime.datetime.now()
	read_url = requests.get(url)

	soup_dirty = BeautifulSoup(read_url.text, 'html.parser')

	games = soup_dirty.find_all('div', id='OddsGridModule_5')[0]
	timestamp = time.strftime("%H:%M:%S")

	return games, timestamp

def parse_spread_data(soup, date, time, not_ML = True):
	def book_line(book_id, line_id, homeaway):
		line = soup.find_all('div', attrs = {'class':'el-div eventLine-book', 'rel':book_id})[line_id].find_all('div')[homeaway].get_text().strip()
		return line

	if not_ML:
		df = pd.DataFrame(columns=('date','time','side',
                         'team','opp_team','pinnacle_line','pinnacle_odds',
                         '5dimes_line','5dimes_odds',
                         'heritage_line','heritage_odds',
                         'bovada_line','bovada_odds',
                         'betonline_line','betonline_odds'))
	else:
		df = DataFrame(
			columns=('key','date','time',
                     'team',
                     'opp_team',
                     'pinnacle','5dimes',
                     'heritage','bovada','betonline'))
	counter = 0
	number_of_games = len(soup.find_all('div', attrs = {'class':'el-div eventLine-rotation'}))

	for i in range(0, number_of_games):
		A = []
		H = []
		print (str(i+1)+'/'+str(number_of_games))

   		## Get useful data from all of the sportsbooks
   		## Handle blank errors
   		info_A = soup.find_all('div', attrs = {'class': 'el-div eventLine-team'})[i].find_all('div')[0].get_text().strip()
   		team_A = info_A

   		try:
   			pinnacle_A = book_line('238', i, 0)
		except IndexError:
			pinnacle_A = ''
		try:
   			fivedimes_A = book_line('19', i, 0)
		except IndexError:
			fivedimes_A = ''
   		try:
   			heritage_A = book_line('169', i, 0)
		except IndexError:
			heritage_A = ''
		try:
   			bovada_A = book_line('999996', i, 0)
		except IndexError:
			bovada_A = ''
		try:
			betonline_A	= book_line('1096', i, 0)
		except IndexError:
			betonline_A	= ''

		info_H = soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[1].get_text().strip()
		team_H = info_H

		try:
   			pinnacle_H = book_line('238', i, 0)
		except IndexError:
			pinnacle_H = ''
		try:
   			fivedimes_H = book_line('19', i, 0)
		except IndexError:
			fivedimes_H = ''
   		try:
   			heritage_H = book_line('169', i, 0)
		except IndexError:
			heritage_H = ''
		try:
   			bovada_H = book_line('999996', i, 0)
		except IndexError:
			bovada_H = ''
		try:
			betonline_H	= book_line('1096', i, 0)
		except IndexError:
			betonline_H	= ''

		A.append(date)
		A.append(time)
		A.append('away')
		A.append(team_A)
		A.append(team_H)
		pinnacle_A = pinnacle_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
		pinnacle_A_line = pinnacle_A[:pinnacle_A.find(' ')]
		pinnacle_A_odds = pinnacle_A[pinnacle_A.find(' ') + 1:]
		A.append(pinnacle_A_line)
		A.append(pinnacle_A_odds)
		fivedimes_A = fivedimes_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
		fivedimes_A_line = fivedimes_A[:fivedimes_A.find(' ')]
		fivedimes_A_odds = fivedimes_A[fivedimes_A.find(' ') + 1:]
		A.append(fivedimes_A_line)
		A.append(fivedimes_A_odds)
		heritage_A = heritage_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
		heritage_A_line = heritage_A[:heritage_A.find(' ')]
		heritage_A_odds = heritage_A[heritage_A.find(' ') + 1:]
		A.append(heritage_A_line)
		A.append(heritage_A_odds)
		bovada_A = bovada_A.replace(u'\xa0', ' ').replace(u'\xbd', '.5')
		bovada_A_line = bovada_A[:bovada_A.find(' ')]
		bovada_A_odds = bovada_A[bovada_A.find(' ') + 1:]
		A.append(bovada_A_line)
		A.append(bovada_A_odds)
		betonline_A = betonline_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
		betonline_A_line = betonline_A[:betonline_A.find(' ')]
		betonline_A_odds = betonline_A[betonline_A.find(' ') + 1:]
		A.append(betonline_A_line)
		A.append(betonline_A_odds)

		H.append(date)
		H.append(time)
		H.append('home')
		H.append(team_H)
		H.append(team_A)

		pinnacle_H = pinnacle_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
		pinnacle_H_line = pinnacle_H[:pinnacle_H.find(' ')]
		pinnacle_H_odds = pinnacle_H[pinnacle_H.find(' ') + 1:]
		H.append(pinnacle_H_line)
		H.append(pinnacle_H_odds)
		fivedimes_H = fivedimes_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
		fivedimes_H_line = fivedimes_H[:fivedimes_H.find(' ')]
		fivedimes_H_odds = fivedimes_H[fivedimes_H.find(' ') + 1:]
		H.append(fivedimes_H_line)
		H.append(fivedimes_H_odds)
		heritage_H = heritage_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
		heritage_H_line = heritage_H[:heritage_H.find(' ')]
		heritage_H_odds = heritage_H[heritage_H.find(' ') + 1:]
		H.append(heritage_H_line)
		H.append(heritage_H_odds)
		bovada_H = bovada_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
		bovada_H_line = bovada_H[:bovada_H.find(' ')]
		bovada_H_odds = bovada_H[bovada_H.find(' ') + 1:]
		H.append(bovada_H_line)
		H.append(bovada_H_odds)
		betonline_H = betonline_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
		betonline_H_line = betonline_H[:betonline_H.find(' ')]
		betonline_H_odds = betonline_H[betonline_H.find(' ') + 1:]
		H.append(betonline_H_line)
		H.append(betonline_H_odds)

		## Take data from A and H and build a dataframe
		df.loc[counter] = ([A[j] for j in range(len(A))])
		df.loc[counter + 1] = ([H[j] for j in range(len(H))])
		counter = counter + 2

		print "Getting %s vs %s"%(team_A, team_H)

	return df



def range_all_dates(start_date, end_date):
	date_range_list = []
	for n in range(int ((end_date - start_date).days)+1):
		d = start_date + timedelta(n)
		d = d.strftime("%Y%m%d")
		date_range_list.append(d)
	return date_range_list

def format_spreads_data(spreads): ## Get team_ids and merge them into spreads dataframe
	team_cities = pd.DataFrame.from_dict(spread_teams['nba_teams'],
										orient = 'index',
										dtype = 'object',
										columns = ['team_city'])
	team_cities['team_id'] = team_cities.index
	spreads = spreads.merge(team_cities, how = 'left', left_on = 'team', right_on = 'team_city')
	spreads['away_team_id'] = spreads['team_id']
	spreads = spreads.drop(columns = ['team_id', 'team_city'])
	spreads = spreads.merge(team_cities, how = 'left', left_on = 'opp_team', right_on = 'team_city')
	spreads['home_team_id'] = spreads['team_id']
	spreads = spreads.drop(columns = ['team_id', 'team_city'])

	spreads = spreads[spreads['side'] == 'away']

	return spreads

if __name__ == "__main__":
	main()

# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import re
from nba_utilities import mongo_connector as mc


class Main:

    def __init__(self, date):

        print "Running daily spread scraper for games on: {}".format(date)
        self.url = 'https://classic.sportsbookreview.com/betting-odds/nba-basketball'

        self.date = date
        _mongo = mc.main()
        self.db = _mongo.warehouse

        self._daily_scraper(date)

    def _daily_scraper(self, date):
        url = '{}/?date={}'.format(self.url, date)

        html = requests.request("GET", url).text
        soup = BeautifulSoup(html)

        # check if currently selected date is today, in order to check for correct div
        today = datetime.now().date().strftime('%Y%m%d')
        if self.date == today:
            games = soup.find_all('div', {'class': 'event-holder holder-scheduled'})
        else:
            games = soup.find_all('div', {'class': 'event-holder holder-complete'})

        for game in games:
            try:
                # parse out teams from html
                teams = game.find_all('div', {'class': 'el-div eventLine-team'})[0]
                teams = teams.find_all('div', {'class': 'eventLine-value'})

                # determine away team
                away_team = str(teams[0]).split('</a>')[0]
                away_team = away_team.split('>', away_team.count('>'))[away_team.count('>')]

                # determine home team
                home_team = str(teams[1]).split('</a>')[0]
                home_team = home_team.split('>', home_team.count('>'))[home_team.count('>')]

                # determine game_id
                score = str(game.find_all('div', {'class': 'score'})[0])
                game_id = (score.split('id="score-', 1)[1]).split('"', 1)[0]

                # determine away team points
                away_score = (score.split('{}-o">'.format(game_id))[1]).split('</span')[0]

                # determine home team points
                home_score = (score.split('{}-u">'.format(game_id))[1]).split('</span')[0]

                # determine "final spread" - final score differential expressed in terms of home team spread
                final_spread = int(away_score) - int(home_score)
                if final_spread > 0:
                    final_spread = '+{}'.format(final_spread)
                else:
                    final_spread = str(final_spread)

                # determine point spread, based on home team
                bovada_odds = (str(game.find_all('div', {'rel': '999996'})[0]).split('<b>', 2)[2]).split('</b>')[0]
                bovada_odds = (bovada_odds.split(' ')[0]).replace('½', '.5')

                # build game_id to match the ones used in various stats by game _data
                game_id = "{}{}".format(self.date, team_map[home_team])

                print '  -> uploading info for: {} @ {} ({})'.format(away_team, home_team, bovada_odds)

                _key = {'_id': '{}'.format(game_id)}
                _data = {'home_team': team_map[home_team], 'away_team': team_map[away_team],
                         'home_spread': bovada_odds.split('\xc2')[0], 'away_points': away_score,
                         'home_points': home_score, 'final_spread': final_spread,
                         'game_id': game_id, 'date': self.date}

                self.db.spreads_by_game.update(_key, _data, upsert=True)
                print ""

            except Exception as e:
                print e

        print ""


team_map = {'Atlanta': 'ATL',
            'Boston': 'BOS',
            'Brooklyn': 'BKN',
            'Philadelphia': 'PHI',
            'Chicago': 'CHI',
            'Charlotte': 'CHA',
            'Cleveland': 'CLE',
            'Dallas': 'DAL',
            'Denver': 'DEN',
            'Detroit': 'DET',
            'Golden State': 'GSW',
            'Houston': 'HOU',
            'Indiana': 'IND',
            'L.A. Clippers': 'LAC',
            'L.A. Lakers': 'LAL',
            'Miami': 'MIA',
            'Memphis': 'MEM',
            'Milwaukee': 'MIL',
            'Minnesota': 'MIN',
            'New Orleans': 'NOP',
            'New York': 'NYK',
            'Oklahoma City': 'OKC',
            'Orlando': 'ORL',
            'Philadelphia': 'PHI',
            'Phoenix': 'PHO',
            'Portland': 'POR',
            'Sacramento': 'SAC',
            'San Antonio': 'SAS',
            'Toronto': 'TOR',
            'Utah': 'UTA',
            'Washington': 'WAS',
            }

if __name__ == "__main__":
    start = datetime(2019, 11, 18).date()
    end = datetime(2019, 11, 30).date()

    dates = [ (start + timedelta(1 * i)).strftime('%Y%m%d') for i in range(0, (end - start).days + 1) ]
    for d in dates:
        Main(d)

# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime, date
import re
from nba_utilities import mongo_connector as mc


class Main:

    def __init__(self, date):

        self.url = 'https://classic.sportsbookreview.com/betting-odds/nba-basketball'

        self.date = date
        _mongo = mc.main()
        self.db = _mongo.warehouse

        self._daily_scraper(date)

    def _daily_scraper(self, date):
        url = '{}/?date={}'.format(self.url, date)

        html = requests.request("GET", url).text
        soup = BeautifulSoup(html)

        games = soup.find_all('div', {'class': 'event-holder holder-complete'})
        for game in games:
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

            # determine point spread, based on home team
            bovada_odds = (str(game.find_all('div', {'rel': '999996'})[0]).split('<b>', 2)[2]).split('</b>')[0]
            bovada_odds = (bovada_odds.split(' ')[0]).replace('½', '.5')

            # determine final spread of game once it has concluded

            print '{} @ {} ({})'.format(away_team, home_team, bovada_odds)

            _data = {'home_team': team_map[home_team], 'away_team': team_map[away_team],
                     'home_spread': bovada_odds.split('\xc2')[0], 'away_points': away_score,
                     'home_points': home_score}

            print _data
            print ""



team_map = {'Philadelphia': 'PHI',
            'Boston': 'BOS',
            'Oklahoma City': 'OKC',
            'Golden State': 'GSW'
            }

# teams = {'ATL': 'Atlanta Hawks',
#          'BOS': 'Boston Celtics',
#          'BKN': 'Brooklyn Nets',
#          'NJN': 'Brooklyn Nets',
#          'CHA': 'Charlotte Hornets',
#          'CHO': 'Charlotte Hornets',
#          'CHI': 'Chicago Bulls',
#          'CLE': 'Cleveland Cavaliers',
#          'DAL': 'Dallas Mavericks',
#          'DEN': 'Denver Nuggets',
#          'DET': 'Detroit Pistons',
#          'GSW': 'Golden State Warriors',
#          'HOU': 'Houston Rockets',
#          'IND': 'Indiana Pacers',
#          'LAC': 'Los Angeles Clippers',
#          'LAL': 'Los Angeles Lakers',
#          'MEM': 'Memphis Grizzlies',
#          'MIA': 'Miami Heat',
#          'MIL': 'Milwaukee Bucks',
#          'MIN': 'Minnesota Timberwolves',
#          'NOH': 'New Orleans Pelicans',
#          'NOP': 'New Orleans Pelicans',
#          'NYK': 'New York Knicks',
#          'OKC': 'Oklahoma City Thunder',
#          'ORL': 'Orlando Magic',
#          'PHI': 'Philadelphia 76ers',
#          'PHO': 'Phoenix Suns',
#          'POR': 'Portland Trail Blazers',
#          'SAC': 'Sacramento Kings',
#          'SAS': 'San Antonio Spurs',
#          'TOR': 'Toronto Raptors',
#          'UTA': 'Utah Jazz',
#          'WAS': 'Washington Wizards'
#          }

if __name__ == "__main__":
    Main('20181016')
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import re
from nba_utilities import mongo_connector as mc
from config import teams

class Main:

    def __init__(self):
        # establish connection to mongodb
        _mongo = mc.main()
        self.db = _mongo.warehouse

        # get list of teams
        self.teams = [ team for team in teams.keys() ]
        # todays date (for timestamping roster updates)
        self.today = datetime.now().strftime('%Y%m%d')
        # master url for basketball-reference
        self.url = 'https://www.basketball-reference.com'
        # season to pull rosters for
        self.season = '2020'

        self._team_looper()

    def _team_looper(self):
        for team in self.teams:
            _data = {}

            # build url for team homepage
            url = '{}/teams/{}/{}.html'.format(self.url, team, self.season)
            try:
                html = requests.request("GET", url).text
                soup = BeautifulSoup(html)
            except Exception as e:
                print e

            roster_html = soup.find('table', {'id': 'roster'})
            rows = [ str(item) for item in str(roster_html).split('<tr>') ][2:]
            for row in rows:
                # parse out important info (name, position etc..)
                player_id = row.split('href')[1].split('/')[3].split('.html')[0]
                position = row.split('"pos">')[1].split('<')[0]
                name = row.split('csk="')[1].split('"')[0]

                # build _key, and _data for upload to mongodb
                _key = {'_id': '{}-{}-{}'.format(player_id, team, self.season)}
                _data = {'name': name, 'position': position,
                         'team': team, 'player_id': player_id,
                         'season': self.season, 'last_update': self.today}

                # now upload to mongodb
                print "Uploading roster data for {}".format(team)
                self.db.rosters.update(_key, _data, upsert=True)
                print ""


if __name__ == "__main__":
    Main()

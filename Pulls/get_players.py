from bs4 import BeautifulSoup
from nba_utilities import mongo_connector as mc
import pandas as pd
import requests
from string import ascii_lowercase
from datetime import datetime, date


class Main:

    def __init__(self):
        _mongo = mc.main()
        self.db = _mongo.warehouse
        self.url = 'https://www.basketball-reference.com'

        self._player_looper()

    def _player_looper(self):

        # for c in ascii_lowercase:
        for c in ['x', 'y', 'z']:
            print "uploading players starting with letter: {}".format(c)
            # build ulr based on current letter
            url = '{}/players/{}/'.format(self.url, c)

            # html of the url
            html = requests.request("GET", url).text
            soup = BeautifulSoup(html)

            # fetch raw table of players
            try:
                raw = soup.find_all('table')[0]

                players = str(raw).split('<tr>')
                for player in players[ 2:len(players) + 1 ]:
                    key = {'_id': (player.split('data-append-csv="'))[1].split('"')[0]}
                    data = {'name': (player.split('.html">'))[1].split('</a')[0],
                            'from': (player.split('year_min">'))[1].split('</td')[0],
                            'to': (player.split('year_max">'))[1].split('</td')[0],
                            'weight': (player.split('weight">'))[1].split('</td')[0],
                            'height': (player.split('height">'))[1].split('</td')[0]
                            }

                    # upload to db
                    self.db.players.update(key, data, upsert=True)
            except Exception as e:
                print e


if __name__ == "__main__":
    Main()
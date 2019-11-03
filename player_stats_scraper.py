from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime, date
import re
from nba_utilities import mongo_connector as mc


class Main:

    def __init__(self, date):

        self.url = 'https://www.basketball-reference.com'
        self.teams = teams
        self.date = date
        _mongo = mc.main()
        self.db = _mongo.warehouse

        self._fetch_games_by_date()
        self._fetch_player_stats()

    def _fetch_games_by_date(self):
        # url page of game stats
        self.games = []

        print "checking which games were played on: {}".format(self.date)
        for id, team in self.teams.iteritems():
            url = '{}/boxscores/{}0{}.html'.format(self.url, self.date, id)
            request = requests.get(url)

            if request.status_code == 200:
                self.games.append(url)
            else:
                pass

    def _fetch_player_stats(self):

        for game in self.games:
            print game
            game_info = {}

            home_team = ( game.split('/{}0'.format(self.date))[1] ).split('.html')[0]
            game_id = '{}{}'.format(self.date, home_team)

            # html of the url
            html = requests.request("GET", game).text
            soup = BeautifulSoup(html)

            # fetch all tables
            all_tables = soup.find_all('table')

            # limit to just the basic, and advanced game stats tables
            home_tables = { table.get('id'): table for table in all_tables if ('game-basic' in table.get('id')
                                                                              or 'game-advanced' in table.get('id'))
                                                                              and home_team in table.get('id') }

            away_tables = {table.get('id'): table for table in all_tables if ('game-basic' in table.get('id')
                                                                              or 'game-advanced' in table.get('id'))
                                                                              and home_team not in table.get('id')}

            self._upload_player_data(game_id, home_tables, home_team, away_tables)

            print ""

    def _upload_player_data(self, game_id, home, home_team, away):
        # loop over home team stats and upload to db
        for id, data in home.iteritems():
            if 'basic' in id:
                rows = [ str(item) for item in str(data).split('<tr>') if 'data-append-csv' in str(item) ]

                for row in rows:
                    try:
                        player = (row.split('data-append-csv="')[1]).split('"')[0]
                        _key = {'_id': '{}_{}'.format(game_id, player)}
                        _data = { stat: (row.split('{}">'.format(stat))[1]).split('</td')[0] for stat in basic_stats }
                        _data['player'] = player
                        _data['team'] = home_team
                        _data['game_id'] = game_id
                        _data['date'] = re.sub('[^0-9]','', game_id)

                        self.db.basic_stats_by_game.update(_key, _data, upsert=True)

                    except:
                        pass

            elif 'advanced' in id:
                rows = [str(item) for item in str(data).split('<tr>') if 'data-append-csv' in str(item)]

                for row in rows:
                    try:
                        _id = {'_id': '{}_{}_{}'.format(game_id, home_team, (row.split('data-append-csv="')[1]).split('"')[0])}
                        _data = { stat: (row.split('{}">'.format(stat))[1]).split('</td')[0] for stat in advanced_stats }

                    except:
                        pass

        # loop over away team stats and upload to db
        for id, data in away.iteritems():
            away_team = (id.split('box-', 1)[1]).split('-')[0]

            if 'basic' in id:
                rows = [str(item) for item in str(data).split('<tr>') if 'data-append-csv' in str(item)]

                for row in rows:
                    try:
                        player = (row.split('data-append-csv="')[1]).split('"')[0]
                        _key = {'_id': '{}_{}'.format(game_id, player)}
                        _data = {stat: (row.split('{}">'.format(stat))[1]).split('</td')[0] for stat in basic_stats}
                        _data['player'] = player
                        _data['team'] = away_team
                        _data['game_id'] = game_id
                        _data['date'] = re.sub('[^0-9]', '', game_id)

                        self.db.basic_stats_by_game.update(_key, _data, upsert=True)

                    except:
                        pass

            elif 'advanced' in id:
                rows = [str(item) for item in str(data).split('<tr>') if 'data-append-csv' in str(item)]

                for row in rows:
                    try:
                        player = (row.split('data-append-csv="')[1]).split('"')[0]
                        _id = {'_id': '{}_{}'.format(game_id, player)}
                        _data = {stat: (row.split('{}">'.format(stat))[1]).split('</td')[0] for stat in advanced_stats}

                    except:
                        pass


basic_stats = ['mp', 'fg', 'fga', 'fg_pct', 'fg3', 'fg3_pct', 'ft', 'fta', 'ft_pct', 'orb',
               'drb', 'trb', 'ast', 'stl', 'blk', 'tov', 'pf', 'pts', 'plus_minus']

advanced_stats = ['ts_pct', 'efg_pct', 'fg3a_per_fga_pct', 'fta_per_fga_pct', 'orb_pct', 'drb_pct',
                  'trb_pct', 'ast_pct', 'stl_pct', 'blk_pct', 'tov_pct', 'usg_pct', 'off_rtg', 'def_rtg']

teams = {'ATL': 'Atlanta Hawks',
         'BOS': 'Boston Celtics',
         'BKN': 'Brooklyn Nets',
         'NJN': 'Brooklyn Nets',
         'CHA': 'Charlotte Hornets',
         'CHO': 'Charlotte Hornets',
         'CHI': 'Chicago Bulls',
         'CLE': 'Cleveland Cavaliers',
         'DAL': 'Dallas Mavericks',
         'DEN': 'Denver Nuggets',
         'DET': 'Detroit Pistons',
         'GSW': 'Golden State Warriors',
         'HOU': 'Houston Rockets',
         'IND': 'Indiana Pacers',
         'LAC': 'Los Angeles Clippers',
         'LAL': 'Los Angeles Lakers',
         'MEM': 'Memphis Grizzlies',
         'MIA': 'Miami Heat',
         'MIL': 'Milwaukee Bucks',
         'MIN': 'Minnesota Timberwolves',
         'NOH': 'New Orleans Pelicans',
         'NOP': 'New Orleans Pelicans',
         'NYK': 'New York Knicks',
         'OKC': 'Oklahoma City Thunder',
         'ORL': 'Orlando Magic',
         'PHI': 'Philadelphia 76ers',
         'PHO': 'Phoenix Suns',
         'POR': 'Portland Trail Blazers',
         'SAC': 'Sacramento Kings',
         'SAS': 'San Antonio Spurs',
         'TOR': 'Toronto Raptors',
         'UTA': 'Utah Jazz',
         'WAS': 'Washington Wizards'
         }

if __name__ == "__main__":
    for m in [10, 11, 12]:
        for x in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                  17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]:

            try:
                date = (datetime(2017, m, x).date()).strftime('%Y%m%d')
                Main(date)
            except:
                pass
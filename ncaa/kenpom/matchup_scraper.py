from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import os
from os.path import expanduser
import pyrebase
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from nba_utilities.db_connection_manager import establish_db_connection


class Main():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.date = '2019-03-21'
        self.url = "https://kenpom.com/fanmatch.php?d=%s"%self.date
        path = "%s/Documents/knockout_creds.json"%expanduser("~")
        config = {
            'apiKey': "AIzaSyDEhRpfi82QXYfDqo8L0Y54SLUUuTp7Vk0",
            'authDomain': "ncaa-knockout-2019.firebaseapp.com",
            'databaseURL': "https://ncaa-knockout-2019.firebaseio.com",
            'projectId': "ncaa-knockout-2019",
            'storageBucket': "ncaa-knockout-2019.appspot.com",
            'messagingSenderId': "104831088386",
            'serviceAccount':path
          }
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()

        # self._get_teams()

        self.teams = pd.read_sql('SELECT id, team, rank FROM knockout_teams', con=self.conn)

        self._start_session()

        self._send_to_jamal()

    def _get_teams(self):

        teams = self.db.child('teams').get()
        teams = [ {'id':t.key() , 'team':t.val().get('team'), 'rank': '' }  for t in teams.each() ]

        df = pd.DataFrame(teams)
        df.to_sql('knockout_teams', con=self.conn, index=False, if_exists='replace')


    def _start_session(self):
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')
        self.driver.implicitly_wait(30)
        self.driver.get(self.url)
        # self.driver.get(self.url_team(team, 2019))

        inputElement = self.driver.find_element_by_name("email")
        inputElement.send_keys('joecass93@gmail.com')
        inputElement = self.driver.find_element_by_name("password")
        inputElement.send_keys('6-9conferenceman')
        inputElement.send_keys(Keys.ENTER)

        self._import_raw_matches()

    def _import_raw_matches(self):
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        table_html = soup.find_all('table', {'id': 'fanmatch-table'})

        cols = ['Game', 'Time (ET)', 'Location']

        df = pd.read_html(str(table_html[0]))[0]
        self.df = df[cols].copy()

        self.driver.close()
        self._clean_data()

    def _clean_data(self):
        df = self.df[self.df['Game'].str.contains('NCAA')].copy()
        df['team_a'] = df.apply(lambda row: get_team(row['Game'], 'a', self.teams), axis=1)
        df['team_b'] = df.apply(lambda row: get_team(row['Game'], 'b', self.teams), axis=1)
        df['pts_a'] = df.apply(lambda row: get_points(row['Game'], 'a', self.teams), axis=1)
        df['pts_b'] = df.apply(lambda row: get_points(row['Game'], 'b', self.teams), axis=1)
        df['winner'] = np.where(df['pts_a'] > df['pts_b'], df['team_a'], df['team_b'])
        df['loser'] = np.where(df['pts_a'] > df['pts_b'], df['team_b'], df['team_a'])

        df.reset_index(drop=True, inplace=True)

        results_df = df[~df['pts_a'].isna()].copy()

        games = {}
        for index, row in df.iterrows():
            if row['team_a'] is not None:
                games[index + 1] = {'away_id':row['team_a'], 'home_id':row['team_b']}
        results = {}
        for index, row in results_df.iterrows():
            if row['team_a'] is not None:
                results[index + 1] = {'away_id':row['team_a'], 'home_id':row['team_b'], 'winner':row['winner'], 'loser':row['loser']}

        self.games = {self.date : games}
        self.results = {self.date: results}

    def _send_to_jamal(self):
        # for dt, data in self.games.iteritems():
        #     for id, game in data.iteritems():
        #         self.db.child('games/%s/%s'%(dt, id)).set({'home_id': game['home_id'], 'away_id': game['away_id']})

        for dt, data in self.results.iteritems():
            for id, game in data.iteritems():
                self.db.child('results/%s/%s'%(dt, id)).set({'winner':game['winner'], 'loser':game['loser']})

def get_team(game, side, teams):

    validate = teams['team'].tolist()

    if 'MVP'in game:
        game = game.split('[', 1)[0]
        team = re.split('[0-9]+ ', game, 1)[1]
        if side == 'a':
            team = team.split(',', 1)[0]
            team = re.split( '[0-9]+', team, 1)[0]
        elif side == 'b':
            team = team.split(', ', 1)[1]
            team = re.split( '[0-9]+', team, 2)[1]
    else:
        game = game.split('NCAA', 1)[0]
        team = re.split('[0-9]+ ', game, 1)[1]
        if side == 'a':
            team = team.split(' vs.', 1)[0]
        elif side == 'b':
            team = re.split(' [0-9]+', team, 1)[1]

    team = team.strip()
    ## validate team name against list of teams currently in db tables
    if team in validate:
        id = teams[teams['team'] == team]['id'].max()
        return id
    else:
        return None

def get_points(game, side, teams):
    validate = teams['team'].tolist()

    if 'MVP'in game:
        game = game.split('[', 1)[0]
        if side == 'a':
            team = game.split(',', 1)[0]
        elif side == 'b':
            team = game.split(', ', 1)[1]
        team = re.split("[0-9]+ ", team, 1)[1]

    else:
        return None

    points = [ int(s) for s in team.split() if s.isdigit() ]

    return points[0]

def hasnumbers(str):
    return bool(re.search(r'\d', str))

def cleantime(raw):
    if isinstance(raw, float):
        return None
    elif 'pm' in raw:
        clean = raw.split(' pm', 1)[0]
        return "%s pm"%clean

if __name__ == "__main__":
    Main()

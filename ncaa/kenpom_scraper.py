from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from nba_utilities.db_connection_manager import establish_db_connection


######################
#### Game Results by Team
######################
class GameResults():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.url = "https://kenpom.com/team.php"
        self.url_team = lambda x, y: '%s?team=%s&y=%s' % (self.url, str(x), str(y))

        self.df = pd.DataFrame()

        self._determine_teams()

        for i, team in enumerate(self.teams):
            if i == 0:
                self._start_session(team)
                self._import_raw_team(team)
            else:
                time.sleep(5)
                self._import_raw_team(team)

        self.driver.close()

        self._clean_data()
        self._upload_data()

    def _determine_teams(self):
        teams = pd.read_sql('SELECT Team FROM kenpom_season_data WHERE Year = 2019 AND Rank < 80', con=self.conn)
        curr_teams = pd.read_sql('SELECT Team FROM kenpom_game_results', con=self.conn)
        curr_teams = [ row['Team'] for index, row in curr_teams.iterrows() ]
        self.teams = [ row['Team'] for index, row in teams.iterrows() ]
        [ self.teams.remove(team) for team in curr_teams if team in self.teams ]

    def _start_session(self, team):
        if ' ' in team:
            team = team.replace(' ', '+')
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')
        self.driver.implicitly_wait(30)
        self.driver.get(self.url_team(team, 2019))

        inputElement = self.driver.find_element_by_name("email")
        inputElement.send_keys('emac1144@yahoo.com')
        inputElement = self.driver.find_element_by_name("password")
        inputElement.send_keys('futurecane4')
        inputElement.send_keys(Keys.ENTER)

    def _import_raw_team(self, team):
        for year in [2015, 2016, 2017, 2018, 2019]:
            self.driver.get(self.url_team(team, year))
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            table_html = soup.find_all('table', {'id': 'schedule-table'})

            cols = ['Date', 'Rank', 'Opp Rank', 'Opponent', 'Score', 'Pace',
                    'Overtime', 'Location', 'Record', 'Conf Record', 'Blog']

            df = pd.read_html(str(table_html[0]))[0]
            df.drop([0], inplace=True)

            df.columns = cols
            df['Team'] = team
            df['Year'] = year

            self.df = self.df.append(df)

    def _clean_data(self):
        df = self.df.copy()
        df.drop(['Blog'], axis=1, inplace=True)

        df['Result'] = np.where(df['Score'].str.contains('W'), 'W',
                                np.where(df['Score'].str.contains('L'), 'L', None))
        df['Pts'] = df.apply(lambda row: self._fix_points('own', row['Result'], row['Score']), axis=1)
        df['Opp Pts'] = df.apply(lambda row: self._fix_points('opp', row['Result'], row['Score']), axis=1)

        self.df = df.copy()

    def _fix_points(self, side, result, score):
        if type(score) == float:
            return None
        else:
            w_pts = (score.split(", ")[1]).split("-")[0]
            l_pts = (score.split(", ")[1]).split("-")[1]

            if (result == 'W') & (side == 'own'):
                return w_pts
            elif (result == 'W') & (side == 'opp'):
                return l_pts
            elif (result == 'L') & (side == 'own'):
                return l_pts
            elif (result == 'L') & (side == 'opp'):
                return w_pts

    def _upload_data(self):
        self.df.to_sql('kenpom_game_results', con=self.conn, if_exists='append', index=False)

######################
#### Kenpom Regular Season Team Four Factors Data Scraper
######################
class FourFactorsData():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.url = "https://kenpom.com/stats.php"
        self.url_year = lambda x: '%s?y=%s' % (self.url, str(x))

        self.df = pd.DataFrame()

        for i, year in enumerate([2019]):
            if i == 0:
                self._start_session(year)
                self._import_raw_year(year)
            else:
                self.driver.get(self.url_year(year))
                self._import_raw_year(year)

        self._clean_data()
        self._upload_data()

    def _start_session(self, year):
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')
        self.driver.implicitly_wait(30)
        self.driver.get(self.url_year(year))

        inputElement = self.driver.find_element_by_name("email")
        inputElement.send_keys('joecass93@gmail.com')
        inputElement = self.driver.find_element_by_name("password")
        inputElement.send_keys('6-9conferenceman')
        inputElement.send_keys(Keys.ENTER)

    def _import_raw_year(self, year):
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        table_html = soup.find_all('table', {'id': 'ratings-table'})
        thead = table_html[0].find_all('thead')[0].find_all('tr')[1]

        cols = []
        thead = [ t.string for t in thead ]

        for t in thead:
            if t != '\n':
                cols.append(t)
                if (t != 'Team') & (t != 'Conf'):
                    cols.append('{} Rank'.format(t))

        df = pd.read_html(str(table_html[0]))[0]
        df.columns = [ str(x) for x in cols ]
        df['year'] = year

        self.df = self.df.append(df)

    def _clean_data(self):

        cols = ['Team', 'Conf', 'AdjTempo', 'AdjTempo Rank', 'AdjOE', 'AdjOE Rank', 'eFG Perc',
                'eFG Perc Rank', 'Turnover Perc', 'Turnover Perc Rank', 'Off Rebound Perc',
                'Off Rebound Perc Rank', 'FTRate', 'FTRate Rank', 'AdjDE', 'AdjDE Rank',
                'Opp eFG Perc', 'Opp eFG Perc Rank', 'Opp Turnover Perc', 'Opp Turnover Perc Rank',
                'Opp Off Rebound Perc',  'Opp Off Rebound Perc Rank', 'Opp FTRate',
                'Opp FTRate Rank', 'Year']
        self.df.columns = cols
        # Lambda that returns true if given string is a number and a valid seed number (1-16)
        valid_seed = lambda x: True if str(x).replace(' ', '').isdigit() and int(x) > 0 and int(x) <= 16 else False
        # Use lambda to parse out seed/team
        self.df['Seed'] = self.df['Team'].apply(lambda x: x[-2:].replace(' ', '') if valid_seed(x[-2:]) else np.nan)
        self.df['Team'] = self.df['Team'].apply(lambda x: x[:-2] if valid_seed(x[-2:]) else x)

    def _upload_data(self):
        self.df.to_sql('kenpom_four_factors_data', con=self.conn, if_exists='append', index=False)
        # master = pd.read_sql('SELECT * FROM kenpom_four_factors_data', con=self.conn)
        # update_seasons = self.df['Year'].unique().tolist()
        # subset = master[~master['Year'].isin(update_seasons)].copy()
        # clean = self.df.append(subset)
        # clean.to_sql('kenpom_four_factors_data', con=self.conn, if_exists='replace', index=False)

######################
#### Kenpom Regular Season Front Page Team Scraper
######################
class SeasonData():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.base_url = 'http://kenpom.com/index.php'
        self.url_year = lambda x: '%s?y=%s' % (self.base_url, str(x))
        self.df = pd.DataFrame()

        for year in [2019]:
            self._import_raw_year(year)

        self._clean_data()
        self._upload_data()

    def _import_raw_year(self, year):
        f = requests.get(self.url_year(year))
        soup = BeautifulSoup(f.text)
        table_html = soup.find_all('table', {'id': 'ratings-table'})
        thead = table_html[0].find_all('thead')

        table = table_html[0]
        for x in thead:
            table = str(table).replace(str(x), '')

        df = pd.read_html(table)[0]
        df['year'] = year

        self.df = self.df.append(df)

    def _clean_data(self):
        # Column rename based off of original website
        self.df.columns = ['Rank', 'Team', 'Conference', 'W-L', 'Pyth',
                           'AdjustO', 'AdjustO Rank', 'AdjustD', 'AdjustD Rank',
                           'AdjustT', 'AdjustT Rank', 'Luck', 'Luck Rank',
                           'SOS Pyth', 'SOS Pyth Rank', 'SOS OppO', 'SOS OppO Rank',
                           'SOS OppD', 'SOS OppD Rank', 'NCSOS Pyth', 'NCSOS Pyth Rank', 'Year']

        # Lambda that returns true if given string is a number and a valid seed number (1-16)
        valid_seed = lambda x: True if str(x).replace(' ', '').isdigit() and int(x) > 0 and int(x) <= 16 else False
        # Use lambda to parse out seed/team
        self.df['Seed'] = self.df['Team'].apply(lambda x: x[-2:].replace(' ', '') if valid_seed(x[-2:]) else np.nan)
        self.df['Team'] = self.df['Team'].apply(lambda x: x[:-2] if valid_seed(x[-2:]) else x)
        # Split W-L column into wins and losses
        self.df['Wins'] = self.df['W-L'].apply(lambda x: int(re.sub('-.*', '', x)) )
        self.df['Losses'] = self.df['W-L'].apply(lambda x: int(re.sub('.*-', '', x)) )
        self.df.drop('W-L', inplace=True, axis=1)
        # Re-org columns
        self.df=self.df[[ 'Year', 'Rank', 'Team', 'Conference', 'Wins', 'Losses', 'Seed','Pyth',
                          'AdjustO', 'AdjustO Rank', 'AdjustD', 'AdjustD Rank',
                          'AdjustT', 'AdjustT Rank', 'Luck', 'Luck Rank',
                          'SOS Pyth', 'SOS Pyth Rank', 'SOS OppO', 'SOS OppO Rank',
                          'SOS OppD', 'SOS OppD Rank', 'NCSOS Pyth', 'NCSOS Pyth Rank']]

    def _upload_data(self):
        master = pd.read_sql('SELECT * FROM kenpom_season_data', con=self.conn)
        update_seasons = self.df['Year'].unique().tolist()
        subset = master[~master['Year'].isin(update_seasons)].copy()
        clean = self.df.append(subset)
        clean.to_sql('kenpom_season_data', con=self.conn, if_exists='replace', index=False)

if __name__ == "__main__":
    # SeasonData()
    FourFactorsData()
    # GameResults()

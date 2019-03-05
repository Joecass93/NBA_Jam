from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from nba_utilities.db_connection_manager import establish_db_connection

######################
#### Kenpom Regular Season Team Four Factors Data Scraper
######################
class FourFactorsData():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.url = "https://kenpom.com/stats.php"

        self.df = pd.DataFrame()
        self._start_session()

        for year in [2015, 2016, 2017, 2018, 2019]:
            self._import_raw_year(year)

        self._clean_data()
        self._upload_data()

    def _start_session(self):
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')
        self.driver.implicitly_wait(30)
        self.driver.get(self.url)

        inputElement = self.driver.find_element_by_name("email")
        inputElement.send_keys('emac1144@yahoo.com')
        inputElement = self.driver.find_element_by_name("password")
        inputElement.send_keys('futurecane4')
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
        self.df.to_sql('kenpom_four_factors_data', con=self.conn, if_exists='replace', index=False)

######################
#### Kenpom Regular Season Front Page Team Scraper
######################
class SeasonData():

    def __init__(self):
        self.conn = establish_db_connection('sqlalchemy').connect()
        self.base_url = 'http://kenpom.com/index.php'
        self.url_year = lambda x: '%s?y=%s' % (self.base_url, str(x) if x != 2019 else self.base_url)
        self.df = pd.DataFrame()

        for year in [2015, 2016, 2017, 2018, 2019]:
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
        self.df.to_sql('kenpom_season_data', con=self.conn, if_exists='replace', index=False)

if __name__ == "__main__":
    # SeasonData()
    FourFactorsData()

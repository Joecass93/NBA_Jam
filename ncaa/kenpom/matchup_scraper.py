import requests, re, json, time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Firefox


class Main():

    def __init__(self):
        self.gameday = datetime.now().date() - timedelta(1)

    def _start_session(self):
        self.driver = Firefox()
        self.driver.get( f"https://kenpom.com/fanmatch.php?d={self.gameday}" )

        inputElement = self.driver.find_element_by_name("email")
        inputElement.send_keys('joecass93@gmail.com')
        inputElement = self.driver.find_element_by_name("password")
        inputElement.send_keys('6-9conferenceman')
        inputElement.send_keys(Keys.ENTER)

        time.sleep(2)

        self._import_raw_matches()

    def _import_raw_matches(self):
        soup = BeautifulSoup(self.driver.page_source)
        table_html = soup.find_all('table', {'id': 'fanmatch-table'})

        self.df = (pd.read_html(str(table_html[0]))[0])[ ['Game', 'Time (ET)', 'Location'] ]
        self.driver.close()

        self._clean_data()

    def _clean_data(self):
        self.df['team_a'] = self.df.apply(lambda row: row['Game'].split(' ', 1)[1].split(',')[0], axis=1)
        self.df['team_b'] = self.df.apply(lambda row: row['Game'].split(', ', 1)[1].split(' ', 1)[1].split(' [')[0] if ', ' in row['Game'] else row['Game'], axis=1)

        for team in ['team_a', 'team_b']:
            self.df[f'{team}_space'] = self.df.apply(lambda row: row[team].count(' '), axis=1)
            self.df[f'{team}_score'] = self.df.apply(lambda row: row[team].split(' ', row[f'{team}_space'])[row[f'{team}_space']], axis=1)
            self.df[team] = self.df.apply(lambda row: re.split(" [0-9]+", row[team])[0], axis=1)

        self.df = self.df[ ['team_a', 'team_a_score', 'team_b', 'team_b_score'] ].reset_index(drop=True, inplace=False)

        for team in ['team_a', 'team_b']:
            self.df[team] = self.df.apply(lambda row: row[team].replace('+', ' ').replace('St.', 'State').replace('%27', "'").replace('%26', '&'), axis=1)
            self.df[team] = self.df.apply(lambda row: row[team].replace("State John's", "St. John's"), axis=1)

        games = []
        for index, row in self.df.iterrows():
            games.append({ col: row[col] for col in self.df.columns })

        self.games = { self.gameday.strftime('%Y-%m-%d') : games }

        with open('games.json', 'w') as fp:
            json.dump(self.games, fp)

if __name__ == "__main__":
    Main()._start_session()

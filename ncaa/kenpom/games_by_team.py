from bs4 import BeautifulSoup
from datetime import datetime
from nba_utilities import mongo_connector as mc
import pandas as pd
import requests, re, time
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys

"""
This section contains code for the Game Results by Team scraper.
"""
class GameResults:

    def __init__(self):
        """ Declare class variables. """
        self.db = mc.main().warehouse
        self.today = datetime.now().strftime('%Y-%m-%d')

        self._team_looper()

    def _team_looper(self):
        """ Main function for looping over teams and scraping game results """
        self._determine_teams()
        for i, team in enumerate(self.teams):
            self._start_session(team) if i == 0 else self._table_master(team)

        # self.browser.close()

    def _determine_teams(self):
        """ Return a list of teams from the database. """
        teams = pd.DataFrame( [ team for team in self.db.kenpom_teams.find({}) ] )
        teams['rank'] = teams['rank'].astype(float)
        self.teams = [ team for team in teams.sort_values('rank', ascending=True).head(1)['team'] ]

    def _start_session(self, team):
        """ Start the selenium session. """
        url = 'https://kenpom.com/team.php?'
        self.browser = Firefox()
        self.browser.get(url)

        time.sleep(2)

        inputElement = self.browser.find_element_by_name("email")
        inputElement.send_keys('Smbeyman@gmail.com')
        inputElement = self.browser.find_element_by_name("password")
        inputElement.send_keys('Kemba19!')
        inputElement.send_keys(Keys.ENTER)

        time.sleep(3)

        self._table_master(team)

    def _table_master(self, team):
        """ Main function for scraping various tables from team breakdown pages. """
        url = build_url(team.replace(' ', '+'), '2020')
        self.browser.get(url)

        time.sleep(3)
        tbl1 = self._scrape_scouting_report(team)

    def _scrape_scouting_report(self, team):
        tbl = self.browser.find_element_by_id('report-table')
        df = pd.read_html(tbl.get_attribute('outerHTML'))[0]

        data = {}
        for index, row in df.iterrows():
            label = row['Category']
            cat_headers = ['Four Factors', 'Miscellaneous Components', 'Style Components',
                           'Point Distribution (% of total points)', 'Strength of Schedule',
                           'Personnel']
            skip_fields = ['Bench Minutes:', 'Experience:', 'Minutes Continuity:', 'Average Height:', '2-Foul Participation:']
            if label in cat_headers + skip_fields:
                pass
            elif label in ['3-Pointers:', '2-Pointers:', 'Free Throws:']:
                label = label.replace('.', '').replace(' ', '_').replace(':', '').lower()
                label = 'pt_dist_' + label
                for x in ['Offense', 'Defense', 'D-I Avg']:
                    val = row[x]
                    if ' ' in val:
                        data[label + '_' + x.replace(' ', '_').lower() + '_val'] = val.split(' ')[0]
                        data[label + '_' + x.replace(' ', '_').lower() + '_rk'] = val.split(' ')[1]
                    else:
                        data[label + '_' + x.replace(' ', '_').lower()] = val

            elif label in ['Components:', 'Overall:', 'Non-conference:']:
                label = label.replace('.', '').replace(' ', '_').replace(':', '').lower()
                label = 'str_sched_' + label
                for x in ['Offense', 'Defense', 'D-I Avg']:
                    val = row[x]
                    if ' ' in val:
                        data[label + '_' + x.replace(' ', '_').lower() + '_val'] = val.split(' ')[0]
                        data[label + '_' + x.replace(' ', '_').lower() + '_rk'] = val.split(' ')[1]
                    else:
                        data[label + '_' + x.replace(' ', '_').lower()] = val

            else:
                label = label.replace('.', '').replace(' ', '_').replace(':', '').lower()
                for x in ['Offense', 'Defense', 'D-I Avg']:
                    val = row[x]
                    if ' ' in val:
                        data[label + '_' + x.replace(' ', '_').lower() + '_val'] = val.split(' ')[0]
                        data[label + '_' + x.replace(' ', '_').lower() + '_rk'] = val.split(' ')[1]
                    else:
                        data[label + '_' + x.replace(' ', '_').lower()] = val

        id = {'_id': team + '_' + self.today}
        self.db.kenpom_scouting_by_day.update(id, data, upsert=True)


def build_url(team, year):
    return 'https://kenpom.com/team.php?team=%s&y=%s' % (team, year)

if __name__ == "__main__":
    GameResults()

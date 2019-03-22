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
        conn = establish_db_connection('sqlalchemy').connect()
        self.url = "https://kenpom.com/team.php"
        self.url_team = lambda x, y: '%s?team=%s&y=%s' % (self.url, str(x), str(y))
        self.df = pd.DataFrame()

        teams = pd.read_sql('SELECT DISTINCT Team FROM kenpom_season_data WHERE Year = 2019 AND Rank <= 60', con=conn)
        teams = teams['Team'].tolist()
        skip_teams = pd.read_sql('SELECT DISTINCT Team FROM kenpom_madness_table', con=conn)
        skip_teams = skip_teams['Team'].tolist()
        for team in skip_teams:
            teams.remove(team)

        for team in teams:
            self._start_session(team)
            print "Fetching game results for %s"%team
            self.team = team
            self._fetch_team_results()
            print "Uploading to db..."
            self._upload_data()
            print ""

        print self.df
        self.driver.close()

    def _start_session(self, team):
        if ' ' in team:
            team = team.replace(' ', '+')
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')
        self.driver.implicitly_wait(30)
        self.driver.get(self.url_team(team, 2019))

        inputElement = self.driver.find_element_by_name("email")
        inputElement.send_keys('joecass93@gmail.com')
        inputElement = self.driver.find_element_by_name("password")
        inputElement.send_keys('6-9conferenceman')
        inputElement.send_keys(Keys.ENTER)

    def _fetch_team_results(self):
        self.driver.get(self.url_team(self.team, 2019))
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        table_html = soup.find_all('table', {'id': 'schedule-table'})
        games = [ link.get('href') for link in soup.findAll('a', attrs={'href': re.compile("^box.php")}) ]
        for g in games:
            try:
                self._get_raw_game(g)
                self._clean_game_data(str(g.split("=", 1)[1]))
                self.df = self.df.append(self.stats)
            except Exception as e:
                print e

    def _get_raw_game(self, game):
        self.driver.get("https://kenpom.com/%s"%game)
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        table_html = soup.find_all('div', {'id': 'box-wrapper'})
        teams = [ str(a) for a in soup.find_all('a') ]
        teams = [ team.split('team=', 1)[1] for team in teams if 'team.php' in team][1:3]
        teams = [ team.split('">', 1)[0] for team in teams ]
        str_fix = {'+':' ', '%27':"'", '%26':'&amp;'}
        for bad, fix in str_fix.iteritems():
            teams = [ team.replace(bad, fix) for team in teams ]

        print " -> fetching %s vs. %s"%(teams[0], teams[1])
        ## get scores
        header = str(soup.find_all('h2')[0])
        scores = {}
        for team in teams:
            if team == self.team:
                key = 'own'
            else:
                key = 'opp'
            scores[key] = (header.split(team, 1)[1]).split(" <span", 1)[0]
        for team, score in scores.iteritems():
            scores[team] = ((score.replace(',', '')).replace('(OT)', '')).strip()

        ##
        data = {}
        for i in [0,1]:
            df = pd.read_html(str(table_html[i]))[0]
            df.dropna(subset=['Name'], inplace=True)
            df = df[~df['Name'].str.contains('TOTAL')].copy()
            df = df[df['Name'] != 'Team'].copy()
            data[teams[i]] = df.copy()

        self.data = data
        self.scores = scores

    def _clean_game_data(self, id):
        data = self.data
        cols = ['Team', 'Name', 'Min', 'Pts', '2PM-A', '3PM-A', 'FTM-A', 'TO', 'OR', 'DR']
        orb = [ {'team':team, 'orb':df['OR'].sum()} for team, df in data.iteritems() ]
        drb = [ {'team':team, 'drb':df['DR'].sum()} for team, df in data.iteritems() ]
        stats = {}
        for team, df in data.iteritems():
            df['Team'] = team
            df = df[cols]
            for col in ['Min', 'Pts', 'TO', 'OR', 'DR']:
                df[col] = pd.to_numeric(df[col])
            df['FGA'] = df.apply(lambda row: get_fga(row['2PM-A'], row['3PM-A']), axis=1)
            df['2PM'] = df.apply(lambda row: get_2pm(row['2PM-A']), axis=1)
            df['3PM'] = df.apply(lambda row: get_3pm(row['3PM-A']), axis=1)
            df['3PA'] = df.apply(lambda row: get_3pa(row['3PM-A']), axis=1)
            df['FTA'] = df.apply(lambda row: get_fta(row['FTM-A']), axis=1)
            df['FTM'] = df.apply(lambda row: get_ftm(row['FTM-A']), axis=1)
            stats[team] = self._build_four_factors(df, orb, drb)

        clean = pd.DataFrame.from_dict(stats.get(self.team))
        clean['team'] = self.team
        clean['game'] = id
        for team, data in stats.iteritems():
            if team != self.team:
                for col, val in data.iteritems():
                    clean['opp_%s'%col] = val
                clean['opp'] = team

        pts = ""
        ints = [ x for x in self.scores.get('own') if x.isdigit() ]
        for i, pt in enumerate(ints):
            pts += pt
        opp_pts = ""
        ints = [ x for x in self.scores.get('opp') if x.isdigit() ]
        for i, pt in enumerate(ints):
            opp_pts += pt

        clean['pts'] = int(pts)
        clean['opp_pts'] = int(opp_pts)
        clean['result'] = np.where(clean['pts'] > clean['opp_pts'], 'w', 'l')
        clean['year'] = 2019
        self.stats = clean

    def _build_four_factors(self, df, orb, drb):
        ## get overall team stats
        # build efg
        efg = (df['2PM'].sum() + (1.5 * df['3PM'].sum())) / df['FGA'].sum()
        # build turnover percentage
        tov_per = (100 * df['TO'].sum()) / (df['FGA'].sum() + (.44 * df['FTA'].sum()) + df['TO'].sum())
        # build orb
        team_orb = [ x.get('orb') for x in orb if x['team'] == self.team][0]
        opp_drb = [ x.get('drb') for x in drb if x['team'] != self.team ][0]
        df['Min'] = np.where(df['Min'] == 0, 1, df['Min'])
        df['orb'] = df.apply(lambda row: get_orb(row['OR'], row['Min'], df['Min'].sum(), team_orb, opp_drb), axis=1)
        orb = df['orb'].sum()
        # df['wght_orb'] = df['orb'] * df['Min']
        # orb = df['wght_orb'].sum() / df['Min'].sum()
        # build ft_rate
        ft_rate = float(df['FTM'].sum()) / float(df['FGA'].sum())

        ## extra stats
        three_pt_pct = float(df['3PM'].sum()) / float(df['3PA'].sum())

        return {'efg': [efg], 'tov': [tov_per], 'orb': [orb], 'ft_rate': [ft_rate], '3pt_pct': [three_pt_pct]}

    def _upload_data(self):
        conn = establish_db_connection('sqlalchemy').connect()
        self.df.to_sql('kenpom_madness_table', con=conn, if_exists='append', index=None)

def get_fga(fg2, fg3):
    fga2 = fg2.split("-", 1)[1]
    fga3 = fg3.split("-", 1)[1]
    return (int(fga2) + int(fga3))

def get_2pm(fg2):
    return int(fg2.split("-", 1)[0])

def get_3pm(fg3):
    return int(fg3.split("-", 1)[0])

def get_3pa(fg3):
    return int(fg3.split("-", 1)[1])

def get_fta(ft):
    return int(ft.split("-", 1)[0])

def get_ftm(ft):
    return int(ft.split("-", 1)[1])

def get_orb(orb, min, team_min, team_orb, opp_drb):
    return (100 * (int(orb) * (int(team_min) / 5)) / (int(min) * (int(team_orb) + int(opp_drb))))


if __name__ == "__main__":
    Main()

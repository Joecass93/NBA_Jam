from bs4 import BeautifulSoup
from bs4 import Comment
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import re
from nba_utilities import mongo_connector as mc


class Main:

    def __init__(self, date=None):

        self.root_url = 'https://www.basketball-reference.com'
        self.date = datetime.now().strftime('%Y%m%d') if date is None else date
        self.db = mc.main().warehouse

    def _determine_games_by_date(self):
        print( f'Fetching list of games for {self.date}')

        ## build date specific url, for fetch list of box scores from that date
        url = f'{self.root_url}/boxscores/?month={self.date[4:6]}&day={self.date[6:8]}&year={self.date[0:4]}'

        ## retrieve the raw html output of the above url
        html = requests.request("GET", url).text
        soup = BeautifulSoup(html, features='lxml')

        ## initialize empty list for holding box score urls
        self.games = []

        ## determine games from the selected date, and add the urls to a list
        all_tables = soup.find_all('table')
        for tbl in all_tables:
            hrefs = tbl.find_all('a')
            for href in [ x for x in hrefs if f'boxscores/{self.date}' in str(x) ]:
                if href is not None and href != '':
                    link = str(href).split('href="')[1].split('"')[0]
                    self.games.append(link)

    ## Loops through the important data from each box score page, and stores in the appropriate db tables
    def _fetch_box_score_by_game(self):
        for game in self.games[0:1]:
            print( f'  -> {game.split("/boxscores/")[1]}' )

            ## build url for the specific game's box score
            url = f'{self.root_url}{game}'

            ## retrieve the raw html output of the above url
            html = requests.request("GET", url).text
            soup = BeautifulSoup(html, features='lxml')

            ## basic game info (game id, home vs away, score by quarter)
            # self._handle_game_info(soup, game)

            ## scores (by quarter & final)
            self._handle_scores(soup, game)

            ## four factors data
            # self._handle_four_factors(soup, game)

    ## Pulls & stores game info, including home & away teams
    def _handle_game_info(self, soup, game):
        ## return the game info section of the html
        info_soup = soup.find_all('div', {'class': 'scorebox'})[0]

        ## get home & away team names from scoreboard
        info_links = info_soup.find_all('a', {'itemprop': 'name'})
        away_id = str(info_links[0]).split('/teams/')[1].split('/')[0]
        home_id = str(info_links[1]).split('/teams/')[1].split('/')[0]

        ## determine game id
        game_id = game.split('/boxscores/')[1].split('.html')[0]

        ## clean up the data we've gathered
        info = {
            '$set': {
                'home_id': home_id,
                'away_id': away_id,
                'date': (re.split('[A-z]+', game_id)[0])[0:-1]
            }
        }

        key = {'_id': game_id}

        ## store in the data warehouse
        try:
            self.db.games.insert_one(key, info)
        # handle update exception, if record already exists
        except:
            self.db.games.update_one(key, info)

    ## Pulls & stores scores by quarter + total score for each team
    def _handle_scores(self, soup, game):
        ## return the line score section of the html
        score_soup = soup.find_all('div', {'id': 'all_line_score'})[0]

        ## line score data is stored as a comment, lets clean that up
        score_comment = score_soup.find_all(string=lambda text: isinstance(text, Comment))[0]
        score_soup = BeautifulSoup(score_comment, features='lxml')

        ## now extract the four factors table from the comment & build a pandas dataframe
        score_tbl = score_soup.find_all('table')[0]
        score_df = pd.read_html(str(score_tbl))[0]

        ## clean up the columns
        score_df.columns = score_df.columns.droplevel()
        score_df = score_df.rename(columns={'Unnamed: 0_level_1': 'Team'})

        ## determine game id
        game_id = game.split('/boxscores/')[1].split('.html')[0]

        ## store away team's scores
        away_scores = score_df.iloc[0:1]
        away_team = away_scores['Team'].max()

        away_key = {'_id': f"{game_id}.{away_team}"}
        away_info = {
            '$set': {
                'game_id': game_id,
                'team_id': away_team,
                'score_1q': str(away_scores['1'].max()),
                'score_2q': str(away_scores['2'].max()),
                'score_3q': str(away_scores['3'].max()),
                'score_4q': str(away_scores['4'].max()),
                'score_tot': str(away_scores['T'].max()),
                'type': 'away'
            }
        }

        try:
            self.db.four_factors.insert_one(away_key, away_info)
        # handle update exception, if record already exists
        except:
            self.db.four_factors.update_one(away_key, away_info)

        ## store home team's scores
        home_scores = score_df.iloc[0:1]
        home_team = home_scores['Team'].max()

        home_key = {'_id': f"{game_id}.{home_team}"}
        home_info = {
            '$set': {
                'game_id': game_id,
                'team_id': home_team,
                'score_1q': str(home_scores['1'].max()),
                'score_2q': str(home_scores['2'].max()),
                'score_3q': str(home_scores['3'].max()),
                'score_4q': str(home_scores['4'].max()),
                'score_tot': str(home_scores['T'].max()),
                'type': 'home'
            }
        }

        try:
            self.db.four_factors.insert_one(home_key, home_info)
        # handle update exception, if record already exists
        except:
            self.db.four_factors.update_one(home_key, home_info)

    ## Pulls & stores four factors data, for each team
    def _handle_four_factors(self, soup, game):
        ## return the four factor section of the html
        ff_soup = soup.find_all('div', {'id': 'all_four_factors'})[0]

        ## four factors data is stored as a comment, lets clean that up
        ff_comment = ff_soup.find_all(string=lambda text: isinstance(text, Comment))[0]
        ff_soup = BeautifulSoup(ff_comment, features='lxml')

        ## now extract the four factors table from the comment & build a pandas dataframe
        ff_tbl = ff_soup.find_all('table')[0]
        ff_df = pd.read_html(str(ff_tbl))[0]

        ## clean up the columns
        ff_df.columns = ff_df.columns.droplevel()
        ff_df = ff_df.rename(columns={'Unnamed: 0_level_1': 'Team'})

        ## determine game id
        game_id = game.split('/boxscores/')[1].split('.html')[0]




def runtime(date):

    Games = Main(date)
    Games._determine_games_by_date()
    Games._fetch_box_score_by_game()

if __name__ == "__main__":
    runtime(date='20191030')

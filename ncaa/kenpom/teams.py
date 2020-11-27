from nba_utilities import mongo_connector as mc
from bs4 import BeautifulSoup
import requests

class TeamMaster:
    """ Declare class variables. """
    db, url = mc.main().warehouse.kenpom_teams, 'https://kenpom.com/index.php'

    def __init__(self):
        """ Main class function """
        soup = BeautifulSoup(requests.get(self.url).content) # parse the kenpom front page

        # loop over the rows and store team rankings
        for row in [ tr for tr in soup.find_all('tr')[2:] if len(tr) == 22 ]:
            rank = str(row.find_all('td')[0]).split('>')[1].split('<')[0] # extract rank and team items from row
            team = str(row.find_all('td')[1]).split('team=')[1].split('"')[0] # extract rank and team items from row
            self.db.update({'_id': team.replace('+', '_').replace('%27', '').lower()}, {'team': team, 'rank': rank}, upsert=True) # update db with daily rankings

if __name__ == "__main__":
    TeamMaster()

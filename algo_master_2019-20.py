import requests
import json
from nba_utilities import mongo_connector as mc


class Main:

    def __init__(self):
        self.url = 'https://free-nba.p.rapidapi.com'
        _mongo = mc.main()
        self.db = _mongo.warehouse

        # self._get_teams()
        # self._get_games()
        self._get_stats_by_date()

    def _get_stats_by_date(self):
        # get stats by date
        url = "https://free-nba.p.rapidapi.com/stats"

        querystring = {"seasons":"2016","page":"0","per_page":"25"}

        headers = {
            'x-rapidapi-host': "free-nba.p.rapidapi.com",
            'x-rapidapi-key': "65923f9d14msh728e06e4472cedfp1c3959jsndd2e798035c2"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)
        data = response.json()['data']
        for item in data:
            print item

    def _get_games(self):
        url = "https://free-nba.p.rapidapi.com/games"

        querystring = {"page": "4", "per_page": "25"}

        headers = {
            'x-rapidapi-host': "free-nba.p.rapidapi.com",
            'x-rapidapi-key': "65923f9d14msh728e06e4472cedfp1c3959jsndd2e798035c2"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)

        print(response.text)

    def _get_teams(self):
        url = "{}/teams".format(self.url)

        querystring = {"page":"0"}

        headers = {
            'x-rapidapi-host': "free-nba.p.rapidapi.com",
            'x-rapidapi-key': "65923f9d14msh728e06e4472cedfp1c3959jsndd2e798035c2"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)
        teams = response.json()['data']

        for team in teams:
            team['_id'] = team['id']
            self.db.teams.insert_one(team)


if __name__ == "__main__":
    Main()
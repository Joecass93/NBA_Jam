from bs4 import BeautifulSoup
import pandas as pd
import requests

class FantasyProjections:

    def __init__(self):

        self.url = "https://datagolf.com/fantasy-projections"

        self._weekly_projections_scraper()

    def _weekly_projections_scarper(self):
        html = requests.request("GET", self.url).text
        soup = BeautifulSoup(html)

        proj_tbl = soup.find_all('div', {'class': 'table'})

        print( proj_tbl )

if __name__ == "__main__":
    FantasyProjections()

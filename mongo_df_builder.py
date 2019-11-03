import pandas as pd
from nba_utilities import mongo_connector as mc

class Main:

    def __init__(self, table):
        _mongo = mc.main()
        self.db = _mongo.warehouse

        self._fetch_data(table)

    def _fetch_data(self, table):
        data = self.db.basic_stats_by_game.find({'date': '20190101'})

        # loop through attribution data and create dataframe
        stats_list = []
        for x in data:
            stats_list.append(x)

        self.df = pd.DataFrame(stats_list)

    # def _data_cleaner(self):
    #     self.df['efg'] = (self.df['fg'] + 0.5 * self.df['fg3']) / self.df['fga']
    #
    #     print self.df[['player', 'efg']]


collections = {'basic stats': 'basic_stats_by_game'}


if __name__ == "__main__":
    Main('basic stats')
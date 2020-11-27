import pandas as pd
from datetime import datetime, date, timedelta
from nba_utilities import mongo_connector as mc

class Main:

    def __init__(self, table, date=None):
        _mongo = mc.main()
        self.db = _mongo.warehouse

        self._fetch_data(table, date)

    def _fetch_data(self, table, date=None):
        # determine correct collection to pull documents from
        # basic stats
        if (table == 'basic stats') & (date is not None):
            data = self.db.basic_stats_by_game.find({'date': date})
        elif (table == 'basic stats') & (date is None):
            data = self.db.basic_stats_by_game.find({})

        # spreads
        elif (table == 'spreads') & (date is not None):
            data = self.db.spreads_by_game.find({'date': date})
        elif (table == 'spreads') & (date is None):
            data = self.db.spreads_by_game.find({})

        # rosters
        elif table == 'rosters':
            data = self.db.rosters.find({})

        # loop through data and create dataframe
        field_list = []
        for field in data:
            field_list.append(field)

        # build pandas dataframe
        self.df = pd.DataFrame(field_list)
        if 'date' in self.df.columns:
            self.df['date'] = self.df.apply(lambda row: datetime.strptime(row['date'], '%Y%m%d'), axis=1)

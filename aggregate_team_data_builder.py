import mongo_df_builder
import pandas
import numpy as np
from nba_utilities import mongo_connector as mc
from datetime import datetime


class Main:

    def __init__(self):
        self.df = mongo_df_builder.Main('basic stats').df
        self.teams = [ team for team in self.df['team'].unique() ]

        # establish connection to mongodb
        _mongo = mc.main()
        self.db = _mongo.warehouse

        # limit to just data from 18-19 season
        self.df = self.df[(self.df['date'] >= '2017-10-17') & (self.df['date'] <= '2018-04-11')]

        # for team in self.teams:
        for team in ['BOS']:
            print "aggregating data for {}...".format(team)
            self._team_looper(team)

    def _team_looper(self, team):
        games = self.df[self.df['team'] == team]['game_id'].unique()
        df = self.df[self.df['game_id'].isin(games)]

        cols = ['ast', 'blk', 'drb', 'fg', 'fg3', 'fg3_pct', 'fg_pct', 'fga',
                'ft', 'ft_pct', 'fta', 'orb', 'pf', 'pts', 'stl', 'tov', 'trb']

        df = df.replace('', '0')

        for col in cols:
            df[col] = df[col].astype(float)

        df['fg3a'] = df['fg3'] / df['fg3_pct']

        df = df.groupby(['game_id', 'team'], as_index=False).agg({'date': 'min',
                                                                  'ast': 'sum',
                                                                  'blk': 'sum',
                                                                  'drb': 'sum',
                                                                  'fg': 'sum',
                                                                  'fga': 'sum',
                                                                  'fg3': 'sum',
                                                                  'fg3a': 'sum',
                                                                  'ft': 'sum',
                                                                  'fta': 'sum',
                                                                  'orb': 'sum',
                                                                  'pf': 'sum',
                                                                  'stl': 'sum',
                                                                  'tov': 'sum',
                                                                  'pts': 'sum'})

        own_df = df[df['team'] == team]
        opp_df = df[df['team'] != team]

        df = own_df.merge(opp_df, how='left', on='game_id', suffixes=('', '_opp'))
        df.drop(['date_opp'], axis=1, inplace=True)

        print df['pts'].sum()
        print df['pts_opp'].sum()
        print ""
        print df['ast'].sum()
        print df['ast_opp'].sum()
        print ""
        print df['drb'].sum() + df['orb'].sum()
        print df['drb_opp'].sum() + df['orb_opp'].sum()
        # float_cols = [ col for col in df.columns if col not in ['game_id', 'team', 'date', 'team_opp']]
        # for col in float_cols:
        #     df[col] = df[col].astype(float)
        #
        # df['poss'] = ((df['fga'] + df['fga_opp'])+ (.44 * (df['fta'] * df['fta_opp'])) - (df['orb'] + df['orb_opp'])) / 2
        #
        # for x in df['date'].unique():
        #     sub = df[df['date'] <= x]
        #     game_id = sub[sub['date'] == x]['game_id'].max()
        #
        #     # fix date
        #     x = (str(x).split('T')[0]).replace('-', '')
        #
        #     # now remove data for current game
        #     sub = sub[sub['game_id'] != game_id]
        #
        #     _data = {}
        #     for col in sub.columns:
        #         if col == 'date':
        #             _data['date'] = x
        #         elif col == 'game_id':
        #             _data['game_id'] = game_id
        #         elif (col == 'team') | (col == 'team_opp'):
        #             _data[col] = sub[col].max()
        #         else:
        #             _data[col] = sub[col].sum()
        #
        #     _key = {'_id': '{}.{}'.format(game_id, sub['team'].max())}
        #     self.db.aggregate_team_data.update(_key, _data, upsert=True)

if __name__ == "__main__":
    Main()

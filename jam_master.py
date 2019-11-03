import pandas as pd
import mongo_df_builder
import matplotlib.pyplot as plt

class Main:

    def __init__(self):
        self.df = mongo_df_builder.Main('basic stats').df

        self._game_looper()

    def _game_looper(self):
        for id in self.df['game_id'].unique():
            df = self.df[self.df['game_id'] == id]

            self._algo_master(df)

    def _algo_master(self, df):
        for col in ['fg', 'fg3', 'fga', 'tov', 'ft', 'fta', 'orb', 'drb', 'trb']:
            df[col] = df[col].astype(float)

        home_team = [ team for team in df['team'].unique() if team in df['game_id'].max() ][0]
        away_team = [ team for team in df['team'].unique() if team not in df['game_id'].max() ][0]

        home_df = df[df['team'] == home_team]
        away_df = df[df['team'] == away_team]

        home_ff = {'efg': (home_df['fg'].sum() + 0.5 * home_df['fg3'].sum()) / home_df['fga'].sum(),
                   'tov': ((100 * home_df['tov'].sum()) / (home_df['fga'].sum() + 0.44 * home_df['fta'].sum() + home_df['tov'].sum())) / 100,
                   'orb': home_df['orb'].sum() / (home_df['orb'].sum() + df[df['team'] == away_team]['drb'].sum()),
                   'ftrate': home_df['ft'].sum() / home_df['fga'].sum()
                   }

        away_ff = {'efg': (away_df['fg'].sum() + 0.5 * away_df['fg3'].sum()) / away_df['fga'].sum(),
                   'tov': ((100 * away_df['tov'].sum()) / (away_df['fga'].sum() + 0.44 * away_df['fta'].sum() + away_df['tov'].sum())) / 100,
                   'orb': away_df['orb'].sum() / (away_df['orb'].sum() + home_df['drb'].sum()),
                   'ftrate': away_df['ft'].sum() / away_df['fga'].sum()
                   }

        weights_dict = {'efg': 0.40, 'tov': 0.25, 'orb': 0.20, 'ftfga': 0.15}


if __name__ == "__main__":
    Main()
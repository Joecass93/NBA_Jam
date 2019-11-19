import pandas as pd
import mongo_df_builder

class Main:

    def __init__(self, date=None):
        self.stats = mongo_df_builder.Main('basic stats', date=date).df
        self.spreads = mongo_df_builder.Main('spreads', date=date).df

        self._game_looper()

    def _game_looper(self):
        for id in self.stats['game_id'].unique():
            df = self.stats[self.stats['game_id'] == id]

            self._algo_master(df)

    def _algo_master(self, df):
        for col in ['fg', 'fg3', 'fga', 'tov', 'ft', 'fta', 'orb', 'drb', 'trb']:
            df[col] = df[col].astype(float)

        home_team = [ team for team in df['team'].unique() if team in df['game_id'].max() ][0]
        away_team = [ team for team in df['team'].unique() if team not in df['game_id'].max() ][0]

        home_df = df[df['team'] == home_team]
        away_df = df[df['team'] == away_team]

        # clean up home stats
        home_ff = {'efg': (home_df['fg'].sum() + 0.5 * home_df['fg3'].sum()) / home_df['fga'].sum(),
                   'tov': ((100 * home_df['tov'].sum()) / (home_df['fga'].sum() + 0.44 * home_df['fta'].sum() + home_df['tov'].sum())),
                   'orb': (home_df['orb'].sum() / (home_df['orb'].sum() + df[df['team'] == away_team]['drb'].sum())) * 100,
                   'ftrate': home_df['ft'].sum() / home_df['fga'].sum()
                   }
        # clean up away stats
        away_ff = {'efg': (away_df['fg'].sum() + 0.5 * away_df['fg3'].sum()) / away_df['fga'].sum(),
                   'tov': ((100 * away_df['tov'].sum()) / (away_df['fga'].sum() + 0.44 * away_df['fta'].sum() + away_df['tov'].sum())),
                   'orb': (away_df['orb'].sum() / (away_df['orb'].sum() + home_df['drb'].sum())) * 100,
                   'ftrate': away_df['ft'].sum() / away_df['fga'].sum()
                   }
        # weights dictionary
        weights_dict = {'efg': 0.40, 'tov': 0.25, 'orb': 0.20, 'ftrate': 0.15}

        algo_dict = {}
        for s, w in weights_dict.iteritems():
            algo_dict[s] = (home_ff[s].item() - away_ff[s].item()) * w

        print home_team
        print round((sum(algo_dict.values()) * 2) + 2.47, 3)
        print ""


if __name__ == "__main__":
    Main('20191103')

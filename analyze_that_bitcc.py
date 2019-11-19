import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd
import mongo_df_builder

class Main:

    def __init__(self):
        self.stats = mongo_df_builder.Main('basic stats').df
        self.spreads = mongo_df_builder.Main('spreads').df

    def _clean_data(self):
        ff_cols = ['fg', 'fg3', 'fga', 'tov', 'ft', 'fta', 'orb', 'drb', 'trb']
        for col in ff_cols:
            self.stats[col] = self.stats[col].astype(float)

        df = pd.DataFrame()
        for id in self.stats['game_id'].unique():
            game_df = self.stats[self.stats['game_id'] == id][ff_cols]


if __name__ == "__main__":
    Main()

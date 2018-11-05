import pandas as pd
import numpy as np
import sys
import datetime as dt
sys.path.insert(0, "/Users/joe/projects/NBA_Jam/")
from utilities import db_connection_manager, config, assets


class convert_to_team_stats:

    def __init__(self, game_id = None, game_date = None, daily_slate = None):
        self.conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

        self.game_id = game_id
        self.game_date = game_date
        self.daily_slate = daily_slate

        self.main()

    def main(self):

        if self.game_id is not None:
            pass

        elif self.game_date is not None:
            ## get table of all games from the specified date
            games_df = assets.games_daily(self.game_date)
            ## build table of weighted running average team stats for each game
            for index, g in games_df.iterrows():
                self.fetch_player_stats(games_df[index:index+1])

        elif self.daily_slate is not None:
            ## build table of weighted running average team stats for each game
            for i, g in daily_slate.iterrows():
                self.fetch_player_stats(daily_slate[daily_slate[index:index+1]])

        return None


    def fetch_player_stats(self, game_info):

        home_sql = "SELECT * FROM player_four_factors WHERE team_id = '%s' and game_id LIKE '%s'"%(game_info['HOME_TEAM_ID'].item(), "002170%%")
        away_sql = "SELECT * FROM player_four_factors WHERE team_id = '%s' and game_id LIKE '%s'"%(game_info['VISITOR_TEAM_ID'].item(), "002170%%")

        matchup_dict = {'home_stats': pd.read_sql(home_sql, con = self.conn),
                        'away_stats': pd.read_sql(away_sql, con = self.conn)}

        for s, m in matchup_dict.iteritems():
            matchup_dict[s] = self.build_weighted_team_stats(m)



        return matchup_dict

    def build_weighted_team_stats(self, player_stats):

        player_df = player_stats[player_stats['MIN'].notna()]
        player_df['SEC'] = player_df['MIN'].apply(get_seconds)
        player_df = player_df.drop(columns = ['MIN', 'index'])

        ## need to determine number of games in which each player has played
        games_played = {}
        games_started = {}
        for p in player_df['PLAYER_NAME'].unique():
            games_played[p] = len(player_df[player_df['PLAYER_NAME'] == p])
            games_started[p] = len(player_df[(player_df['PLAYER_NAME'] == p) & (player_df['START_POSITION'] != "")])

        player_avg_df = player_df.groupby(by = ['PLAYER_NAME'], as_index = False).mean()

        print player_avg_df

        team_stats_cols = player_avg_df.columns.values[2:-1]
        weighted_team_stats = {}

        for i, stat in enumerate(team_stats_cols[:-1]):
            player_avg_df[stat] = player_avg_df[stat] * player_avg_df['SEC']
            weighted_team_stats[stat] = player_avg_df[stat].sum() / player_avg_df['SEC'].sum()

        print weighted_team_stats

        return None


def get_seconds(time_str):

    m, s = time_str.split(":")
    seconds = (int(m) * 60) + int(s)

    return seconds

def normalize_stats(stats, norm):

    return None


if __name__ == "__main__":
    convert_to_team_stats(game_date = '2018-10-26')

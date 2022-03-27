import pandas as pd
import requests


class FetchGameStats:

    def __init__(self):
        self.url = "https://www.balldontlie.io/api/v1"

    def _fetch_stats_by_team(self, team):
        ## first determine team id
        teams = requests.get(f"{self.url}/teams").json()
        teams = [ tm for tm in teams['data'] ]
        self.team = [ tm['id'] for tm in teams if tm['full_name'] == team ][0]

        ## now fetch game stats for the seleted team
        games = requests.get(f"{self.url}/games?dates[]=2021-02-02&team_ids[]={self.team}").json()
        games = [ gm for gm in games['data'] ]
        self.game = [ gm['id'] for gm in games ][0]
        ##
        stats = requests.get(f"{self.url}/stats?game_ids[]={self.game}").json()
        stats = stats['data']

    def _fetch_stats_by_date(self, dt):
        ## fetch all games for selected date
        games = requests.get(f"{self.url}/games?dates[]={dt}").json()
        games = games['data']
        games = [ game['id'] for game in games ]

    def _fetch_stats_by_player(self, players):
        stats_list = ['ast', 'blk', 'fg3m', 'pts', 'reb', 'stl', 'turnover']

        ## loop over player list and fetch season averages, last10 averages, last5 averages and last game stats
        dk_avgs = pd.DataFrame()

        # for playername in players[0:5]:
        for playername in players:
            print( playername )
            ## first get the player's ID
            player = requests.get(f"{self.url}/players?search={playername}").json()['data']
            player = player[0]['id']

            ## now get player's stats for the current season
            stats = requests.get(f"{self.url}/stats?player_ids[]={player}&seasons[]=2021&per_page=100").json()['data']

            stats_df = pd.DataFrame()
            for stat in stats:
                ## save the date object
                stat['date'] = stat['game']['date'].split('T')[0]
                stat.pop('player')
                stat.pop('team')
                stat.pop('game')

                stats_df = stats_df.append(stat, ignore_index=True)

            ## remove any preseason games
            stats_df = stats_df[stats_df['date'] >= '2021-10-19']
            stats_df['name'] = player

            stats_df = stats_df.sort_values('date', ascending=False)

            ## get season averages
            season_avg = stats_df.groupby('name', as_index=False).agg({stat:'mean' for stat in stats_list})
            season_avg['dk_pts'] = season_avg.apply(lambda row: dk_points_builder(row), axis=1)
            avg_dkpts = season_avg['dk_pts'].item()

            ## get last 10 game averages
            last10_avg = stats_df.head(10).groupby('name', as_index=False).agg({stat:'mean' for stat in stats_list})
            last10_avg['dk_pts'] = last10_avg.apply(lambda row: dk_points_builder(row), axis=1)

            ## get last 5 game averages
            last5_avg = stats_df.head(5).groupby('name', as_index=False).agg({stat:'mean' for stat in stats_list})
            last5_avg['dk_pts'] = last5_avg.apply(lambda row: dk_points_builder(row), axis=1)

            ## get last game averages
            last1_avg = stats_df.head(1).groupby('name', as_index=False).agg({stat:'mean' for stat in stats_list})
            last1_avg['dk_pts'] = last5_avg.apply(lambda row: dk_points_builder(row), axis=1)

            dk_avgs = dk_avgs.append({'name': playername, 'avg_pts': avg_dkpts}, ignore_index=True)

        print( season_avg )
        print()
        print( last10_avg )
        print()
        print( last5_avg )
        print()
        print( last1_avg )
        # print( dk_avgs )


def dk_points_builder(row):
    return (row['ast']*1.5) + (row['blk']*2) + (row['fg3m']*0.5) + (row['pts']*1) + (row['reb']*1.25) + (row['stl']*2) + (row['turnover']*-0.5)


def main():
    master = FetchGameStats()

    # master._fetch_stats_by_team(team='Boston Celtics')
    # master._fetch_stats_by_date(dt='2022-03-06')
    master._fetch_stats_by_player(['Jayson Tatum'])

if __name__ == "__main__":
    main()

import pandas as pd
from os.path import expanduser


class DataExplorer:

    def __init__(self, season='2019-2020'):
        ## Set some class variables ##
        self.workdir = f"{expanduser('~')}/Downloads"
        self.season = season

        ## Run through the functions ##
        self._fetch_raw_data()
        self._explore()

    def _fetch_raw_data(self):
        ## Import play-by-play dataset for the selected season ##
        file = f'{self.workdir}/NBA-PBP-{self.season}.csv'
        file = f'{self.workdir}/temp_pbp_data.csv'
        self.df = pd.read_csv(file, sep=',')

    def _explore(self):
        ## Select all of the plays from a game and explore
        # game_id = '201910220TOR'
        # df = self.df[self.df['URL'].str.contains(game_id)]
        # df.to_csv(f'{self.workdir}/temp_pbp_data.csv')
        df = self.df.fillna('')

        ## Which team made the play?
        df['Play'] = df.apply(lambda row: row['HomePlay'] if row['HomePlay'] != '' else row['AwayPlay'], axis=1)
        df['TeamPlay'] = df.apply(lambda row: 'Home' if row['HomePlay'] != '' else 'Away', axis=1)

        ## What type of play?
        df['PlayType'] = df.apply(lambda row: play_type(row['ShotOutcome'], row['ReboundType'], row['ViolationType'], row['TimeoutTeam'], row['FreeThrowOutcome'], row['EnterGame'], row['TurnoverType'], row['JumpballPoss']), axis=1)


def play_type(shot, rebound, violation, timeout, freethrow, ,turnover, jumpball):
    args = locals()
    for x in args:
        if x != '':
            return x



if __name__ == "__main__":
    DataExplorer()

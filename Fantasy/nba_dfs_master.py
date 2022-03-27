from draft_kings import Sport, Client
from datetime import datetime, date
import pandas as pd
import numpy as np
import pulp
import cplex
from os.path import expanduser

from pulls import balldontlie_master as bdl

class LinearOptimization:

    def __init__(self):
        self.dir = f"{expanduser('~')}/Downloads"
        self.today = datetime.now().date()
        self.salary_cap = 50000
        self.max_players = 8

    def _determine_player_pool(self):
        ## loop over currently available DFS contests, and determine event of choice
        contests = Client().contests(sport=Sport.NBA)

        for contest in contests.contests:
            if contest.payout == 100000.0:
                draft_group = contest.draft_group_id

        event_info = Client().draftables(draft_group_id=draft_group)

        ## loop over the available players and build a clean dataframe containing names and salaries
        player_pool = []
        for player in event_info.players:
            player_pool.append({'name': player.name_details.display, 'id': player.draftable_id, 'salary': player.salary})

        self.players = pd.DataFrame(player_pool)

        ## remove any weird duplicate values, and keep the max salary option
        self.players = self.players.groupby('name', as_index=False).max()

        ## remove any players that cost 3k (likely dont play)
        self.players = self.players[self.players['salary'] > 3000]

        ## import csv to get avg ppg
        ppg = pd.read_csv(f"{self.dir}/DKSalaries.csv", sep=',')
        ppg = ppg[['Name', 'AvgPointsPerGame', 'Position']]
        ppg['Position'] = ppg.apply(lambda row: row['Position'].split('/')[0] if '/' in row['Position'] else row['Position'], axis=1)

        self.players = self.players.merge(ppg, how='left', left_on='name', right_on='Name')

    def _determine_player_projections(self):
        df = pd.read_csv(f"{self.dir}/DFF_NBA_cheatsheet_{self.today.strftime('%Y-%m-%d')}.csv", sep=',')

        fields = ['first_name', 'last_name', 'position', 'position_alt', 'injury_status', 'ppg_projection']
        self.projections = df[fields]

        ## make full name field for merging
        self.projections['name'] = self.projections.apply(lambda row: f"{row['first_name']} {row['last_name']}", axis=1)

    def _fetch_player_stats(self):
        ## fetch player stats
        scraper = bdl.FetchGameStats()
        scraper._fetch_stats_by_player([ name for name in self.players['Name'].unique() ])

    def _merge_data(self):
        self.df = self.players.merge(self.projections, how='left', on='name')

        ## remove players that are OUT
        self.df = self.df[self.df['injury_status'] != 'O']

        ## remove players that are QUESTIONABLE
        self.df = self.df[self.df['injury_status'] != 'Q']

        ## fill in missing projections with avg ppg
        self.df['ppg_projection'] = np.where(self.df['ppg_projection'].isna(), self.df['AvgPointsPerGame'], self.df['ppg_projection'])
        # self.df = self.df[self.df['ppg_projection'].isna()]
        self.df['position'] = np.where(self.df['position'].isna(), self.df['Position'], self.df['position'])

        self.df = self.df[self.df['position'].notna()]

        ## reformat position field
        pos_map = {'PG':'G', 'SG':'G', 'SF':'F', 'PF':'F', 'C':'C'}
        self.df['position'] = self.df.apply(lambda row: pos_map[row['position']], axis=1)

        fields = ['name', 'position', 'salary', 'ppg_projection']
        fields = ['name', 'position', 'salary', 'AvgPointsPerGame']
        self.df = self.df[fields]

        self.df.reset_index(inplace=True)

    def _build_problem(self):
        self.tot_players = len(self.df)

        ## build positions mapping
        self.positions = {'G':[], 'F':[], 'C':[]}
        for pos in self.df['position']:
            for key in self.positions:
                self.positions[key].append(1 if key in pos else 0)

        ## defie the pulp object problem
        prob = pulp.LpProblem('NBA', pulp.LpMaximize)

        ## define the player variables
        self.lineup = [ pulp.LpVariable(f'player_{i+1}', cat="Binary") for i in range(self.tot_players) ]

        ## add the max player constraint
        prob += ( pulp.lpSum(self.lineup[i] for i in range(self.tot_players)) == self.max_players)

        #add the positional constraints
        # 3-4 guards
        prob += ( 3 <= pulp.lpSum(self.positions['G'][i]*self.lineup[i] for i in range(self.tot_players)) )
        prob += ( pulp.lpSum(self.positions['G'][i]*self.lineup[i] for i in range(self.tot_players)) <= 4 )

        # 3-4 forwards
        prob += ( 3 <= pulp.lpSum(self.positions['F'][i]*self.lineup[i] for i in range(self.tot_players)) )
        prob += ( pulp.lpSum(self.positions['F'][i]*self.lineup[i] for i in range(self.tot_players)) <= 4 )

        # 1-2 centers
        prob += ( 1 <= pulp.lpSum(self.positions['C'][i]*self.lineup[i] for i in range(self.tot_players)) )
        prob += ( pulp.lpSum(self.positions['C'][i]*self.lineup[i] for i in range(self.tot_players)) <= 2 )

        ## add the salary constraint
        prob += ( pulp.lpSum(self.df.loc[i, 'salary']*self.lineup[i] for i in range(self.tot_players)) <=  self.salary_cap )

        ## add the objective
        prob += ( pulp.lpSum(self.df.loc[i, 'AvgPointsPerGame']*self.lineup[i] for i in range(self.tot_players)) )

        ## solve the problem
        pulp.LpSolverDefault.msg = 1
        # prob.solve(pulp.CPLEX_PY(msg=0))
        prob.solve(pulp.PULP_CBC_CMD())
        status = pulp.LpStatus[prob.status]


        self.lineup_copy = []
        for i in range(self.tot_players):
            if self.lineup[i].varValue >= 0.9 and self.lineup[i].varValue <= 1.1:
                self.lineup_copy.append(1)
            else:
                self.lineup_copy.append(0)


    def _build_lineup(self):
        for num, player in enumerate(self.lineup_copy):
            if player > 0.9 and player < 1.1:
                print( self.df.loc[num, 'name'] )
                print( self.df.loc[num, 'AvgPointsPerGame'] )
                print( )

def main():
    algo = LinearOptimization()

    algo._determine_player_pool()
    algo._determine_player_projections()
    # algo._fetch_player_stats()
    algo._merge_data()
    algo._build_problem()
    algo._build_lineup()

if __name__ == "__main__":
    main()

from draft_kings import Sport, Client
from datetime import datetime, date
import pandas as pd
import pulp
import cplex
from os.path import expanduser

class LinearOptimization:

    def __init__(self):
        self.today = datetime.now().date()
        self.salary_cap = 50000

    def _determine_player_pool(self):
        ## loop over currently available DFS contests, and determine event of choice
        contests = Client().contests(sport=Sport.GOLF)

        for contest in contests.contests:
            if contest.payout >= 2500000.0:
                print( contest.payout )
                print()
                draft_group = contest.draft_group_id

        event_info = Client().draftables(draft_group_id=draft_group)

        ## loop over the available players and build a clean dataframe containing names and salaries
        player_pool = []
        for player in event_info.players:
            player_pool.append({'name': player.name_details.display, 'id': player.draftable_id, 'salary': player.salary})

        self.players = pd.DataFrame(player_pool)

        ## remove any weird duplicate values, and keep the max salary option
        self.players = self.players.groupby('name', as_index=False).max()

    def _determine_player_projections(self):
        ## scrape datagolf projections page
        self.projections = pd.read_csv(f"{expanduser('~')}/Downloads/draftkings_main_projections.csv", sep=',')

    def _merge_data(self):
        self.df = self.players.merge(self.projections, how='left', left_on='id', right_on='dk_id')
        self.df = self.df[(~self.df['salary'].isna()) & (~self.df['total_points'].isna())]

        self.df.reset_index(inplace=True)

    def _build_problem(self):
        self.tot_players = len(self.df)

        ## defie the pulp object problem
        prob = pulp.LpProblem('PGA', pulp.LpMaximize)

        ## define the player variables
        self.lineup = [ pulp.LpVariable(f'player_{i+1}', cat="Binary") for i in range(self.tot_players) ]

        ## add the max player constraint
        prob += ( pulp.lpSum(self.lineup[i] for i in range(self.tot_players)) == 6)

        ## add the salary constraint
        prob += ( pulp.lpSum(self.df.loc[i, 'salary']*self.lineup[i] for i in range(self.tot_players)) <=  50000 )

        ## add the objective
        prob += ( pulp.lpSum(self.df.loc[i, 'total_points']*self.lineup[i] for i in range(self.tot_players)) )

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
                print( self.df.loc[num, 'total_points'] )
                print( )


def main():
    algo = LinearOptimization()

    algo._determine_player_pool()
    algo._determine_player_projections()
    algo._merge_data()
    algo._build_problem()
    algo._build_lineup()

if __name__ == "__main__":
    main()

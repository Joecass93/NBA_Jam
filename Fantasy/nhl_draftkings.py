import pandas as pd
import pulp

class NHLMaster:

    def __init__(self):
        self.salary_cap = 50000
        self.header = ['C', 'C', 'W', 'W', 'W', 'D', 'D', 'G', 'UTIL']

    def _build_problem(self):
        #define the pulp object problem
        prob = pulp.LpProblem('NHL', pulp.LpMaximize)

        #define the player and goalie variables
        skaters_lineup = [pulp.LpVariable("player_{}".format(i+1), cat="Binary") for i in range(self.num_skaters)]
        goalies_lineup = [pulp.LpVariable("goalie_{}".format(i+1), cat="Binary") for i in range(self.num_goalies)]

        #add the max player constraints
        prob += (pulp.lpSum(skaters_lineup[i] for i in range(self.num_skaters)) == 8)
        prob += (pulp.lpSum(goalies_lineup[i] for i in range(self.num_goalies)) == 1)


if __name__ == "__main__":
    master = NHLMaster()
    master._build_problem()

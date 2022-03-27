import json
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import re
from itertools import permutations
from urllib.request import urlopen
import ssl

from pulp import *

url = "https://api.draftkings.com/draftgroups/v1/draftgroups/63726/draftables?format=json"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class BuildOptimalLineup():

    def __init__(self):
        self.today = datetime.now().date()

        print( f"Fetching and cleaning available players for {self.today.strftime('%B %d, %Y')}..." )
        self._fetch_players()
        self._build_pos_dicts()
        # self._build_flex_dicts()
        self._contest_rules()
        self._run_optimization()

    def _fetch_players(self):
        ## get raw json API response
        response = urlopen(url, context=ctx)
        data = json.loads(response.read())

        ## build dataframe from the raw json
        current = pd.DataFrame.from_dict(data["draftables"])
        self.players = current[current.status == "None"]

        self._clean_players()

    def _clean_players(self):
        ## extract points as float from each players attributes dictionary
        points = [ get_float(x, "value") for x in self.players.draftStatAttributes ]
        self.players['points'] = points

        ## clean up encoding issue with player names
        self.players['displayName'] = self.players['displayName'].apply(clean_encoding)

        ## remove duplicate players from the data, and keep only the key fields
        self.availables = self.players.groupby('displayName', as_index=False).agg({'position': 'max', 'salary': 'max', 'points': 'max'})

        ## rename some fields
        self.availables.rename(columns={'displayName': 'Name'}, inplace=True)

        ## add dummy vars for each position type
        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            self.availables[pos] = np.where(self.availables['position'].str.contains(pos), 1, 0)

    def _build_pos_dicts(self):
        ## build dictionaries of names & salaries, and names & points by position
        self.salaries = {}
        self.points = {}

        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            ## filter to just the selected position's players
            available_pos = self.availables[self.availables[pos] == 1].copy()
            salary = list(available_pos[["Name","salary"]].set_index("Name").to_dict().values())[0]
            point = list(available_pos[["Name","points"]].set_index("Name").to_dict().values())[0]

            ## append position dictionaries to master dictionaries
            self.salaries[pos] = salary
            self.points[pos] = point


    def _build_flex_dicts(self):
        ## build dictionaries for guard flex, forward flex and overall flex names and points
        g_flex_pts = {}
        f_flex_pts = {}
        flex_pts = {}
        ## build dictionaries for guard flex, forward flex and overall flex names and salaries
        g_flex_sal = {}
        f_flex_sal = {}
        flex_sal = {}

        for player, pts in self.points['PG'].items():
            g_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['SG'].items():
            g_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['SF'].items():
            f_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['PF'].items():
            f_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['C'].items():
            flex_pts[player] = pts

        for player, sal in self.salaries['PG'].items():
            g_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['SG'].items():
            g_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['SF'].items():
            f_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['PF'].items():
            f_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['C'].items():
            flex_sal[player] = sal

        ## update the master points dictionary with the flex info
        self.points['G_FLEX'] = g_flex_pts
        self.points['F_FLEX'] = f_flex_pts
        self.points['FLEX'] = flex_pts

        ## update the master salaries dictionary with the flex info
        self.salaries['G_FLEX'] = g_flex_sal
        self.salaries['F_FLEX'] = f_flex_sal
        self.salaries['FLEX'] = flex_sal


    def _contest_rules(self):
        ## establish the general contest rules (salary and position caps)
        self.salary_cap = 50000
        # self.positions = {'PG': 1, 'SG': 1, 'SF': 1, 'PF': 1,
        #                   'C': 1, 'G_FLEX': 1, 'F_FLEX': 1, 'FLEX': 1
        #                   }
        self.positions = {'PG': 2, 'SG': 2, 'SF': 2, 'PF': 1,
                          'C': 1
                          }

    def _run_optimization(self):
        _vars = {k: LpVariable.dict(k, v, cat="Binary") for k, v in self.points.items()}
        prob = LpProblem("Fantasy", LpMaximize)
        rewards = []
        costs = []
        position_constraints = []

        # Setting up the reward
        for k, v in _vars.items():
            costs += lpSum([self.salaries[k][i] * _vars[k][i] for i in v])
            rewards += lpSum([self.points[k][i] * _vars[k][i] for i in v])
            prob += lpSum([_vars[k][i] for i in v]) <= self.positions[k]

        prob += lpSum(rewards)
        prob += lpSum(costs) <= self.salary_cap
        prob.solve()

        summary(prob)

def get_float(l, key):
    """ Returns first float value from a list of dictionaries based on key. Defaults to 0.0 """
    for d in l:
        try:
            return float(d.get(key))
        except:
            pass
    return 0.0

def clean_encoding(raw):
    return raw.encode('utf-8').strip()

def summary(prob):
    div = '---------------------------------------\n'
    print("Variables:\n")
    score = str(prob.objective)
    constraints = [str(const) for const in prob.constraints.values()]
    for v in prob.variables():
        score = score.replace(v.name, str(v.varValue))
        constraints = [const.replace(v.name, str(v.varValue)) for const in constraints]
        if v.varValue != 0:
            print(v.name, "=", v.varValue)
    print(div)
    print("Constraints:")
    for constraint in constraints:
        constraint_pretty = " + ".join(re.findall("[0-9\.]*\*1.0", constraint))
        if constraint_pretty != "":
            print("{} = {}".format(constraint_pretty, eval(constraint_pretty)))
    print(div)
    print("Score:")
    score_pretty = " + ".join(re.findall("[0-9\.]+\*1.0", score))
    print("{} = {}".format(score_pretty, eval(score)))

if __name__ == "__main__":
    BuildOptimalLineup()

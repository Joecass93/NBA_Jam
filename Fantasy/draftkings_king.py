import urllib, json
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import re
from itertools import permutations
import ssl

from pulp import *

url = "https://api.draftkings.com/draftgroups/v1/draftgroups/24122/draftables?format=json"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class BuildOptimalLineup():

    def __init__(self):
        self.today = datetime.now().date()

        print "Fetching and cleaning available players for %s..."%self.today.strftime("%B %d, %Y")
        self._fetch_players()
        self._build_pos_dicts()
        self._build_flex_dicts()
        self._contest_rules()
        self._run_optimization()

    def _fetch_players(self):
        response = urllib.urlopen(url, context=ctx)
        data = json.loads(response.read())
        current = pd.DataFrame.from_dict(data["draftables"])
        self.players = current[current.status == "None"]
        self._clean_players()

    def _clean_players(self):
        points = [get_float(x, "value") for x in self.players.draftStatAttributes]
        self.players["points"] = points
        self.players['displayName'] = self.players['displayName'].apply(clean_encoding)
        availables = self.players[["position", "displayName", "salary", "points"]].groupby(["position", "displayName", "salary", "points"]).agg("count")
        self.availables = availables.reset_index()
        self.availables.rename(index=str, columns = {'displayName': 'Name'}, inplace = True)

        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            self.availables[pos] = np.where(self.availables['position'].str.contains(pos), 1, 0)

    def _build_pos_dicts(self):
        self.salaries = {}
        self.points = {}
        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            available_pos = self.availables[self.availables[pos] == 1].copy()
            salary = list(available_pos[["Name","salary"]].set_index("Name").to_dict().values())[0]
            point = list(available_pos[["Name","points"]].set_index("Name").to_dict().values())[0]
            self.salaries[pos] = salary
            self.points[pos] = point

    def _build_flex_dicts(self):
        g_flex_pts = {}
        f_flex_pts = {}
        flex_pts = {}
        g_flex_sal = {}
        f_flex_sal = {}
        flex_sal = {}

        for player, pts in self.points['PG'].iteritems():
            g_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['SG'].iteritems():
            g_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['SF'].iteritems():
            f_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['PF'].iteritems():
            f_flex_pts[player] = pts
            flex_pts[player] = pts
        for player, pts in self.points['C'].iteritems():
            flex_pts[player] = pts

        for player, sal in self.salaries['PG'].iteritems():
            g_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['SG'].iteritems():
            g_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['SF'].iteritems():
            f_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['PF'].iteritems():
            f_flex_sal[player] = sal
            flex_sal[player] = sal
        for player, sal in self.salaries['C'].iteritems():
            flex_sal[player] = sal

        self.points['G_FLEX'] = g_flex_pts
        self.points['F_FLEX'] = f_flex_pts
        self.points['FLEX'] = flex_pts

        self.salaries['G_FLEX'] = g_flex_sal
        self.salaries['F_FLEX'] = f_flex_sal
        self.salaries['FLEX'] = flex_sal

    def _contest_rules(self):
        self.salary_cap = 50000
        self.positions = {'PG': 1, 'SG': 1, 'SF': 1, 'PF': 1,
                          'C': 1, 'G_FLEX': 1, 'F_FLEX': 1, 'FLEX': 1
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
            print prob
            prob += lpSum([_vars[k][i] for i in v]) <= self.positions[k]

        prob += lpSum(rewards)
        prob += lpSum(costs) <= self.salary_cap
        prob.solve()

        # summary(prob)

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

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
        self._build_dicts()
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
        availables = self.players[["position", "displayName", "salary", "points"]].groupby(["position", "displayName", "salary", "points"]).agg("count")
        self.availables = availables.reset_index()
        self.availables.rename(index=str, columns = {'displayName': 'Name'}, inplace = True)

        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            self.availables[pos] = np.where(self.availables['position'].str.contains(pos), 1, 0)

    def _build_dicts(self):
        self.salaries = {}
        self.points = {}
        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            available_pos = self.availables[self.availables[pos] == 1].copy()
            salary = list(available_pos[["Name","salary"]].set_index("Name").to_dict().values())[0]
            point = list(available_pos[["Name","points"]].set_index("Name").to_dict().values())[0]
            self.salaries[pos] = salary
            self.points[pos] = point

    def _contest_rules(self):
        self.salary_cap = 50000
        self.positions = {'PG': 1, 'SG': 1, 'SF': 1, 'PF': 1,
                          'C': 1, 'G_flex': 1, 'F_flex': 1, 'Flex': 1
                          }
        self.g_flex = {'PG': 1, 'SG': 1, 'SF': 0, 'PF': 0, 'C': 0}
        self.f_flex = {'PG': 0, 'SG': 0, 'SF': 1, 'PF': 1, 'C': 0}
        self.flex = {'PG': 1, 'SG': 1, 'SF': 1, 'PF': 1, 'C': 1}

    def _run_optimization(self):
        _vars = {k: LpVariable.dict(k, v, cat="Binary") for k, v in self.points.items()}
        prob = LpProblem("Fantasy", LpMaximize)
        rewards = []
        costs = []
        position_constraints = []

        print _vars

        # # Setting up the reward
        # for k, v in _vars.items():
        #     costs += lpSum([salaries[k][i] * _vars[k][i] for i in v])
        #     rewards += lpSum([points[k][i] * _vars[k][i] for i in v])
        #     prob += lpSum([_vars[k][i] for i in v]) <= pos_num_available[k]
        #     prob += lpSum([pos_flex[k] * _vars[k][i] for i in v]) <= pos_flex_available
        #
        # prob += lpSum(rewards)
        # prob += lpSum(costs) <= SALARY_CAP

def get_float(l, key):
    """ Returns first float value from a list of dictionaries based on key. Defaults to 0.0 """
    for d in l:
        try:
            return float(d.get(key))
        except:
            pass
    return 0.0


if __name__ == "__main__":
    BuildOptimalLineup()

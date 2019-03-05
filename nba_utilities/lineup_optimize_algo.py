from ortools.linear_solver import pywraplp
import pandas as pd
from os.path import expanduser
import numpy as np
from pulp import *

home_dir = expanduser("~")

def main(proj_data, contest_params):

    players = proj_data

    contest_rules = contest_params['contest_rules']
    opt_rules = contest_params['opt_rules']

    ## organize rules, constraints etc...
    salary_cap = contest_rules['sal_cap']
    total_pos = sum(contest_rules['pos_counts'].values())


    ##### DFS optimization problem
    final_lineup_proj = 500

    pos_dict = contest_rules['pos_counts']
    del pos_dict['flex']

    max_repeats = opt_rules['num_lineups'] * opt_rules["player_freq"][2]
    print "players should not appear in more than %s lineups"%max_repeats

    players = proj_data.dropna()

    ## add lineup count column, full w/ 0s
    players['lineup_freq'] = 0

    for i in range(0,opt_rules['num_lineups']):

        lp = pulp.LpProblem("Lineup Builder", LpMaximize)
        # Create variables for lp
        lp_vars = [pulp.LpVariable('x_{0:04d}'.format(index), cat = 'Binary') for index in players.index]

        # Objective function, maximize points
        lp += pulp.LpAffineExpression(zip(lp_vars, players['Pts'])), 'Projected fantasy points'
        # Salary constraints
        lp += pulp.LpAffineExpression(zip(lp_vars, players['Sal'])) <= salary_cap, 'Salary constraint'

        # Multiple lineups constraint
        lp += pulp.LpAffineExpression(zip(lp_vars, players['lineup_freq'])) <= max_repeats, 'Frequency constraint'

        # Starter restrictions
        print "building lineup constraints...."
        for f in contest_rules['flex_alt']:
            reg = pos_dict.get(f)
            lp += pulp.LpAffineExpression(zip(lp_vars, 1 * (players['Pos'] == f))) <= (reg + 1), '%s upper constraint'%f
            lp += pulp.LpAffineExpression(zip(lp_vars, 1 * (players['Pos'] == f))) >= reg, '%s lower constraint'%f

        # add constraints for the remaining players
        for p, c in pos_dict.iteritems():
            if p in contest_rules['flex_alt']:
                pass
            else:
                lp += pulp.LpAffineExpression(zip(lp_vars, 1 * (players['Pos'] == p))) == c, '%s constraint'%p

        # total players
        lp += pulp.LpAffineExpression(zip(lp_vars, 1 * (players['Pos'] != ""))) == total_pos, 'total players constraint'

        # replicate constraint
        lp += pulp.LpAffineExpression(zip(lp_vars, players['Pts'])) <= float(value(final_lineup_proj)) - 0.001, 'replicate constraint'

        status = lp.solve()
        print LpStatus[status]

        print lp.objective.value()

        ## Who was selected

        include = [v.varValue for v in lp.variables()]
        players['include'] = include

        lineup = players[players['include'] == 1][['Name', 'Team', 'Pos', 'Pts', 'Sal']].sort_values(by = 'Pts', ascending = False)

        final_lineup_proj = lineup['Pts'].sum()

        print "Total salary: $%s"%str(lineup['Sal'].sum())
        print "Total projected points: %s"%final_lineup_proj

        ## Add to dataframe containing top 50 dataframes
        lineup['ranking'] = i + 1

        print "lineup #%s created!"%lineup['ranking'].max()

        if i == 0:
            lineups_master = lineup
        else:
            lineups_master = lineups_master.append(lineup)

        ## table for tracking number of lineups a player has appeared in
        curr_players_list = lineup['Name'].tolist()

        players['lineup_freq'] = np.where(players['Name'].isin(curr_players_list), players['lineup_freq'] + 1, players['lineup_freq'])

    print lineups_master
    #lineups_master.to_csv("%s/projects/NBA_Jam/Data/week_3_lineups.csv"%home_dir, sep = ",")

    return None

if __name__ == "__main__":
    main()

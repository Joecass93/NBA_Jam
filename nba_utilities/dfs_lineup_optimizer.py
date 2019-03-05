import pandas as pd
import numpy as np
from datetime import datetime
from os.path import expanduser
from random import shuffle
import itertools
import lineup_optimize_algo
import emoji


home_dir = expanduser("~")

def main(league, date, contest_type = None):

    if league == "NFL":
        money_team = nfl_solver(date)


    return money_team


def nfl_solver(date, contest_type = None):

    if contest_type:
        contest_type = "nfl_%s"%contest_type
    else:
        contest_type = "nfl_dk_standard"

    ## Get salary cap and other rules for the contest
    contest_params = get_dfs_rules(contest_type)


    #print "posisition counts: %s"%pos_counts
    #print "salary cap: %s"%sal_cap
    #print "flex options: %s"%flex_alt
    #print "average salary: %s"%avg_sal

    ## import csv's with point projections
    ## decision tree to determine import files based on contest type
    roto_grinders_df = pd.read_csv("%s/projects/NBA_Jam/data/pff_edge_proj.csv"%home_dir, sep = ",", header = 1)

    roto_grinders_df['Sal'] = pd.to_numeric(roto_grinders_df['Sal'].str[1:]) ## Reformat Salaries from string to integer

    lineup_optimize_algo.main(roto_grinders_df, contest_params)




############## V1 Attempt below
    #pff_edge_df = pd.read_csv(, sep = ",")

    # ## player_pool cleaning..
    # roto_grinders_df['Sal'] = pd.to_numeric(roto_grinders_df['Sal'].str[1:]) ## Reformat Salaries from string to integer
    #
    # pos_df = roto_grinders_df.groupby(['Pos']).size()
    #
    # ## Build dummy lineup
    # starting_point = roto_grinders_df[(roto_grinders_df['Sal'] > 5000) & (roto_grinders_df['Sal'] < 6000)]
    # print starting_point
    # #print starting_point.sort_values(by = ['Sal']) --- use this logic to build the dummy lineup automatically
    # dummy_list = ['107', '126', '124', '123', '132', '45', '15', '46', '474']
    # lineup_cols = ['Name', 'Team', 'Pos', 'Pts', 'Sal']
    # curr_lineup = roto_grinders_df[roto_grinders_df.Rnk.isin(dummy_list)][lineup_cols]
    #
    # ## remove and replace at random, dont allow a move if it breaks the rules
    # full_player_list = list(roto_grinders_df.Name)
    # # remove the players being used in the dummy lineup
    # dummy_players = list(curr_lineup.Name)
    # full_player_list = [x for x in full_player_list if x not in dummy_players]
    #
    # #shuffle(full_player_list)
    # # add column for $/pts to determine order to try to add new players
    # player_pool = roto_grinders_df[(roto_grinders_df.Name.isin(full_player_list)) & (roto_grinders_df['Pts'] != 0)]
    # player_pool = player_pool[lineup_cols]
    # player_pool['ROI'] = player_pool.apply(lambda row: row['Pts'] / row['Sal'], axis = 1)
    # curr_lineup['ROI'] = curr_lineup.apply(lambda row: row['Pts'] / row['Sal'], axis = 1)
    # player_pool = player_pool.sort_values(by = ['ROI'], ascending = False)
    # curr_lineup = curr_lineup.sort_values(by = ['ROI'], ascending = True)
    #
    # print "current lineup is: "
    # print curr_lineup
    #
    # # loop through available players and determine if we should swap them into lineup
    # lineup_count = 0
    # lineup_options = pd.DataFrame(columns = lineup_cols)

    # for p in player_pool.Name:
    #     i = 0
    #     if i < 500:
    #         print len(player_pool)
    #
    #         curr_sub = player_pool[player_pool['Name'] == p]
    #         ## get total salary of current lineup
    #         lineup_price = curr_lineup['Sal'].sum()
    #         ## get total projected points of current lineup
    #         lineup_proj = curr_lineup['Pts'].sum()
    #         ## find first occurence of this position in the current lineup (sorted by ROI ascending)
    #         curr_pos = curr_sub['Pos'].item()
    #         curr_sal = curr_sub['Sal'].item()
    #         curr_proj = curr_sub['Pts'].item()
    #         curr_name = curr_sub['Name'].item()
    #         # get index of that player
    #         replace_indx = curr_lineup.index[curr_lineup['Pos'] == curr_pos][0].item()
    #         replace_row = curr_lineup.loc[replace_indx]
    #         # determine new total lineup price when swapping these players
    #         replace_sal = replace_row['Sal'].item()
    #         replace_proj = replace_row['Pts'].item()
    #         replace_name = replace_row['Name']
    #         new_lineup_price = lineup_price - replace_sal + curr_sal
    #         new_lineup_proj = lineup_proj - replace_proj + curr_proj
    #         # determine if new total salary is below max
    #         if new_lineup_price > sal_cap:
    #             print "swapping %s in for %s would put lineup over salary cap, moving on to next player"%(curr_name, replace_name)
    #             pass
    #         elif new_lineup_proj < lineup_proj:
    #             print "swapping %s in for %s would lower projected points, moving on to next player"%(curr_name, replace_name)
    #         else:
    #             print "swapping %s in for %s is allowed!"%(curr_name, replace_name)
    #             ## swap the players
    #             curr_lineup = curr_lineup.drop(replace_indx)
    #             curr_lineup = curr_lineup.append(curr_sub)
    #             # add removed player back into eligible player pool
    #             print len(player_pool)
    #             player_pool = player_pool.append(replace_row[lineup_cols])
    #             print len(player_pool)
    #
    #             store_lineup = curr_lineup
    #             ## assign lineup number
    #             store_lineup['lineup_num'] = lineup_count
    #             store_lineup['total_proj'] = new_lineup_proj
    #
    #             lineup_options = lineup_options.append(store_lineup)
    #
    #
    #             lineup_count += 1
    #             i += 1
    #         else:
    #             pass
    #
    # print lineup_options
    #
    # best_lineup = lineup_options[lineup_options['lineup_num'] == lineup_count - 1]
    # print "total salary: %s"%best_lineup['Sal'].sum()
    # print "total projected points: %s"%best_lineup['Pts'].sum()


    return None

def get_dfs_rules(contest_type):

    nfl_dk_standard = {"contest_rules":{"pos_counts" :
                            {"qb" : 1,
                             "rb" : 2,
                             "wr" : 3,
                             "te" : 1,
                             "flex" : 1,
                             "dst" : 1
                             },
                       "sal_cap" : 50000,
                       "flex_alt" : ['rb', 'wr', 'te']
                        },
                        "opt_rules":
                            {"player_freq" : [0.05, 0.10, 0.25],
                             "lineup_overlap" : [2, 3, 4],
                             "num_lineups": 50}
                        }


    nfl_fd_standard = {}

    if contest_type == "nfl_dk_standard":
        dfs_params = nfl_dk_standard
    elif contest_type == "nfl_fd_standard":
        dfs_params = nfl_fd_standard

    return dfs_params

if __name__ == "__main__":
    main("NFL", '2018-09-20')

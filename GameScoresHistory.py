import nba_py
import pandas as pd
import numpy as np
import os
from flask import Flask
from flask import render_template
from datetime import datetime, date, timedelta

### Miscellaneous
###
cwd = os.getcwd() # Current working directory

### Create list of dates to pull game final results for
###
pulldates = []
d1 = date(2000, 10, 20) # Start Date
d2 = date(2010, 6, 30) # End Date

delta = d2 - d1 # timedelta

for i in range(delta.days + 1):
    #pulldates.append(datetime.timedelta(i))
    pulldates.append(d1 + timedelta(days=i))

### Create blank dataframe to append each days game data dataframe to
###
games_master = pd.DataFrame()

### Loop through the selected dates, get game final scores and append them to games_master
###
for date in pulldates:
    scoreboard = nba_py.Scoreboard(month=date.month, 
                            day=date.day, 
                            year=date.year)
    line_score = scoreboard.line_score()
    games_master = games_master.append(line_score)

d1 = d1.strftime('%m.%d.%Y') # transform d1 to string for file naming
d2 = d2.strftime('%m.%d.%Y') # transform d2 to string for file naming

### Print date to csv
###
games_master.to_csv(cwd + "/FinalScores" + d1 + "_" + d2 + ".csv", sep = ",") 








####Data cleaning nonsense
# List of games
#games = []
# Dictionary of the current game we're looking at
#current_game = {}

#current_game_sequence = 0
#game_sequence_counter = 0

# for team in line_score:
#     if (team["GAME_SEQUENCE"] != current_game_sequence):
#         current_game["TEAM_1_ABBREVIATION"] = team["TEAM_ABBREVIATION"]
#         current_game["TEAM_1_WINS_LOSSES"] = team["TEAM_WINS_LOSSES"]

#         current_game["TEAM_1_PTS"] = team["TEAM_PTS"]
#         current_game["TEAM_1_ID"] = team["TEAM_ID"]

#         current_game_sequence = team["GAME SEQUENCE"]
#         game_sequence_counter += 1
#     elif (game_sequence_counter == 1):
#         current_game["TEAM_2_ABBREVIATION"] = team["TEAM_ABBREVIATION"]
#         current_game["TEAM_2_WINS_LOSSES"] = team["TEAM_WINS_LOSSES"]
        
#         current_game["TEAM_2_PTS"] = team["TEAM_PTS"]
#         current_game["TEAM_2_ID"] = team["TEAM_ID"]           

#         current_game["GAME_ID"] = team["GAME_ID"]

#         games.append(current_game)

#         current_game = {}
#         game_sequence_counter = 0

# print(games)
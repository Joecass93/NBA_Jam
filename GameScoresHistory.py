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

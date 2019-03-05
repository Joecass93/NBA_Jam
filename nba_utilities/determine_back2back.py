import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from db_connection_manager import establish_db_connection

conn = establish_db_connection('sqlalchemy').connect()
scores = pd.read_sql('SELECT * FROM final_scores', con = conn)

new_scores = pd.DataFrame(columns = list(scores))
for d in scores['game_date'].unique():
    d_sub = scores[scores['game_date'] == d].copy()
    prev_d_sub = scores[scores['game_date'] == d - timedelta(1)].copy()

    prev_teams = [a for a in prev_d_sub['away_team']]
    for h in prev_d_sub['home_team']:
        prev_teams.append(h)

    d_sub['b2b_away'] = np.where(d_sub['away_team'].isin(prev_teams), "Yes", "No")
    d_sub['b2b_home'] = np.where(d_sub['home_team'].isin(prev_teams), "Yes", "No")

    new_scores = new_scores.append(d_sub)

reconn = establish_db_connection('sqlalchemy').connect()
new_scores.to_sql('new_final_scores', con = reconn, if_exists = 'append', index = False)

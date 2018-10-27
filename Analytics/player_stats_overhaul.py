import pandas as pd
import numpy as np
import sys
sys.path.insert(0, "/Users/joe/projects/NBA_Jam/")
from utilities import db_connection_manager, config

conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

celtics_sql = "SELECT * FROM player_four_factors WHERE team_id = '1610612738'"
celtics = pd.read_sql(celtics_sql, con = conn)

player_minutes = celtics[celtics['MIN'].notna()][['PLAYER_NAME', 'MIN']]

player_minutes['MIN'] = pd.to_datetime(player_minutes['MIN'], format = '%M:%S')

print player_minutes.head()

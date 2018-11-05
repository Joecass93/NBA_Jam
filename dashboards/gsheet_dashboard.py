
import pandas as pd
from datetime import datetime, date
import sys
from os.path import expanduser
sys.path.insert(0, "%s/projects/NBA_Jam"%expanduser("~"))
from utilities import gsheets_api_manager as gsheets
from utilities import db_connection_manager

def main():

    conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

    picks_df_sql = "SELECT * FROM historical_picks_table WHERE game_id LIKE '%s'"%'002180%%'
    picks_df = pd.read_sql(picks_df_sql, con = conn)

    ## trasnform dates to string
    print type(picks_df['game_date'].max())
    picks_df['game_date'] = pd.to_datetime(picks_df['game_date'], format = '%Y-%m-%d')
    picks_df['game_date'] = picks_df['game_date'].dt.strftime('%Y-%m-%d')

    dashboard_dict = {'workbook': '1kiajCiXZ0f1T_cAcZfYPxzumeIElehWuRhoHpu4GrW0',
                'data': picks_df,
                'worksheet': 'Full History!A1'}

    gsheets.df_to_gsheet(dashboard_dict['workbook'], dashboard_dict['worksheet'], dashboard_dict['data'])

    return None

if __name__ == "__main__":
    main()

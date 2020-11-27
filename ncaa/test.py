import json
import pandas as pd
from nba_utilities import mongo_connector as mc

def main():

    jamie = fetch_jamie_teams()
    joe = fetch_joe_teams()

    clean = merge_jamie_joe(jamie, joe)

def fetch_jamie_teams():
    with open('ncaa/jamie_teams.json') as f:
        return [ team['School'] for team in json.load(f) ]

def fetch_joe_teams():
    db = mc.main().warehouse
    return pd.DataFrame( [ team for team in db.kenpom_teams.find({}) ] )

def merge_jamie_joe(jamie, joe):
    jamie_df = pd.DataFrame({'team': jamie})
    jamie_df['mark'] = 'jamie_team'
    joe_df = pd.DataFrame(joe)

    joe_df['team'] = joe_df.apply(lambda row: row['team'].replace('+', ' ').replace('St.', 'State').replace('%27', "'").replace('%26', '&'), axis=1)
    joe_df['team'] = joe_df.apply(lambda row: row['team'].replace("State John's", "St. John's"), axis=1)

    df = joe_df.merge(jamie_df, how='left', on='team')
    # df['team'] = df.apply(lambda row: fix_name())
    # export = df[(df['mark'] == 'jamie_team') & (df['_id'].isna())].copy()
    df.to_csv('export_teams.csv', sep=',')

    return None

if __name__ == "__main__":
    main()

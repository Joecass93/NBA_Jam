import pandas as pd
import numpy as np
import difflib
from datetime import datetime, date, timedelta
import sys
sys.path.insert(0, "/Users/joe/projects/NBA_Jam/")
import json
import requests
from utilities import db_connection_manager, config
from bs4 import BeautifulSoup
import urllib2
from fuzzywuzzy import fuzz, process

difflib.get_close_matches

class get_todays_lineups():

    def __init__(self):
        self.conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()
        self.headers = config.request_header

        self.fetch_and_store_lineups()

    def fetch_and_store_lineups(self):

        lineups_df = self.go_get_the_lineups()

        clean_lineups = self.clean_the_lineups(lineups_df)

        print "Uploading today's stats to db..."
        upload_data_to_db(clean_lineups, "daily_lineups")

        return None

    def clean_the_lineups(self, lineups_df):

        ## import master table of players, ids and their teams
        players_master = pd.read_sql("SELECT * FROM players_master", con = self.conn)
        teams_master = pd.read_sql("SELECT * FROM teams_master", con = self.conn)

        pos_list = list(lineups_df)
        pos_list.remove('team')
        ## add columns to hold injury designation for ir slots
        ir_list = ['ir_1', 'ir_2', 'ir_3', 'ir_4', 'ir_5']
        for inj in ir_list:
            lineups_df['%s_type'%inj] = np.where(lineups_df[inj].str.contains("OUT"), "OUT",
                                                np.where(lineups_df[inj].str.contains("INACT"), "INACT",
                                                np.where(lineups_df[inj].str.contains("GTD"), "GTD", "MISSING")))


        ## remove GTD from players with the tag
        for p in pos_list:
            print "finding closest match from database for each %s..."%p
            lineups_df[p] = lineups_df[p].str.replace(" GTD", "")
            lineups_df[p] = lineups_df[p].str.replace(" INACT", "")
            lineups_df[p] = lineups_df[p].str.replace(" OUT", "")
            lineups_df[p] = lineups_df[p].str.replace(" IV", "")
            lineups_df[p] = lineups_df[p].str.replace("K. Towns", "Karl Anthony Towns")
            lineups_df[p] = lineups_df[p].replace(np.nan, 'MISSING', regex = True)

            lineups_df[p] = lineups_df[p].apply(lambda x: difflib.get_close_matches(x, players_master['PLAYER_NAME']))
            lineups_df[p] = lineups_df[p].map(lambda x: x.insert(0, 'MISSING') if len(x) == 0 else x)
            lineups_df[p] = lineups_df[p].replace(np.nan, "MISSING")

            lineups_df[p] = lineups_df[p].map(lambda x: x[0])

            ## create new column containing the player ids
            lineups_df = pd.merge(lineups_df, players_master[['PLAYER_NAME', 'PLAYER_ID']],
                                    how = 'left', left_on = p, right_on = 'PLAYER_NAME')

            lineups_df = lineups_df.drop(columns = ['PLAYER_NAME'], axis = 1)
            lineups_df = lineups_df.rename(index = str, columns = {'PLAYER_ID': '%s_ID'%p})

        ## get the team_ids
        # clean some names firsts
        lineups_df['team'] = lineups_df['team'].str.replace(r'\bNY\b', 'NYK', regex = True)
        lineups_df['team'] = lineups_df['team'].str.replace(r'\bSA\b', 'SAS', regex = True)
        lineups_df['team'] = lineups_df['team'].str.replace(r'\bPHO\b', 'PHX', regex = True)

        lineups_df = pd.merge(lineups_df, teams_master[['TEAM_ABBREVIATION', 'TEAM_ID']],
                            how = 'left', left_on = 'team', right_on = 'TEAM_ABBREVIATION')

        lineups_df = lineups_df.drop(columns = ['TEAM_ABBREVIATION'])

        print "lineup table for today is: "

        return lineups_df


    def go_get_the_lineups(self):

        lineups_url = "https://www.rotowire.com/basketball/nba-lineups.php"
        page = urllib2.urlopen(lineups_url)

        soup = BeautifulSoup(page, 'html.parser')

        ## initalize lineups dataframe
        injuries_cols = ['ir1', 'ir2', 'ir3', 'ir4', 'ir5']

        ## get each matchup first
        matchup_tags = soup.find_all('div', {'class':'lineup__box'})
        lineups_dict = {}
        n = 0
        for m in matchup_tags:

            ## initalize empty lists to hold team rosters for each matchup
            home_list = []
            away_list = []

            ## do some html parsing
            away_team = m.find_all('a', {'class':'lineup__team is-visit'})
            home_team = m.find_all('a', {'class':'lineup__team is-home'})
            away_lineup = m.find_all('ul', {'class': "lineup__list is-visit"})
            home_lineup = m.find_all('ul', {'class': "lineup__list is-home"})
            for at in away_team:
                away_list.append(str(at.text).strip())
            for ht in home_team:
                home_list.append(str(ht.text).strip())
            for al in away_lineup:
                away_list.append(str(al.text).strip())
            for hl in home_lineup:
                home_list.append(str(hl.text).strip())

            ## check that we are not pulling an empty html block
            if len(home_list) != 0:
                ## clean up strings
                home_list = [x.replace('\r', "") for x in home_list]
                home_list = [x.replace('\n', " ") for x in home_list]
                away_list = [x.replace('\r', "") for x in away_list]
                away_list = [x.replace('\n', " ") for x in away_list]

                ## split each player out by double spaces, and trim empty spaces from list
                home_list = home_list[1].split("  ")
                home_list = [x.strip() for x in home_list][7:]
                away_list = away_list[1].split("  ")
                away_list = [x.strip() for x in away_list][7:]

                ## insert team names back into the lists
                home_list.insert(0, str(ht.text).strip())
                away_list.insert(0, str(at.text).strip())

                ## initalize blank dictionaries to hold starters and their position
                home_start_dict = {}
                away_start_dict = {}
                end_h = home_list.index("INJURIES")
                end_a = away_list.index("INJURIES")
                for h in home_list[1:end_h]:
                    home_start_dict[h.split(" ", 1)[0]] = h.split(" ", 1)[1]
                for a in away_list[1:end_a]:
                    away_start_dict[a.split(" ", 1)[0]] = a.split(" ", 1)[1]

                if 'INJURIES' in home_list:
                    home_list.remove('INJURIES')
                if 'INJURIES' in away_list:
                    away_list.remove('INJURIES')

                home_start_dict['team'] = home_list[0]
                away_start_dict['team'] = away_list[0]

                ## reformat dicts as dataframes
                home_df = pd.DataFrame([home_start_dict.values()], columns = home_start_dict.keys())
                away_df = pd.DataFrame([away_start_dict.values()], columns = away_start_dict.keys())

                ## initalize blank dictionaries to hold injured players and their status
                home_injury_dict = {}
                away_injury_dict = {}
                for i, h in enumerate(home_list[6:]):
                    home_injury_dict['ir_%s'%str(i + 1)] = h.split(" ", 1)[1]
                for i, a in enumerate(away_list[6:]):
                    away_injury_dict['ir_%s'%str(i + 1)] = a.split(" ",1)[1]

                home_injury_dict['team'] = home_list[0]
                away_injury_dict['team'] = away_list[0]

                ## reformat dicts as dataframes
                away_injury_df = pd.DataFrame([away_injury_dict.values()], columns = away_injury_dict.keys())
                home_injury_df = pd.DataFrame([home_injury_dict.values()], columns = home_injury_dict.keys())
                matchup_df = home_df.append(away_df)
                injury_df = away_injury_df.append(home_injury_df)

                ## append to master dataframes for the day
                if n == 0:
                    lineups_df = matchup_df
                    injuries_df = injury_df
                else:
                    lineups_df = lineups_df.append(matchup_df)
                    injuries_df = injuries_df.append(injury_df)

                n = n + 1

        ## merge the starters table and injuries table by team name
        merged_lineups_table = lineups_df.merge(injuries_df, how = 'left', on = 'team')

        return merged_lineups_table


def find_matching_player_id(row):

    player = row['PG']

    print fuzz.token_sort_ratio(player,"test")

    return fuzz.token_sort_ratio(player, "test")

def upload_data_to_db(data, table):
    conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

    data.to_sql(table, con = conn, if_exists = 'replace')

    return None


if __name__ == "__main__":
    get_todays_lineups()

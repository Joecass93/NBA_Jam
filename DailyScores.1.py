import nba_py
from flask import Flask
from flask import render_template
from datetime import datetime

    
def get_games(date):
    datetime_today = datetime.today()
    datetime_today = datetime.strptime('Jan 15 2018', '%b %d %Y')

    scoreboard = nba_py.Scoreboard(month=date.month, 
                                day=date.day, 
                                year=date.year)
    line_score = scoreboard.line_score()
    # List of games
    games = []
    # Dictionary of the current game we're looking at
    current_game = {}

    current_game_sequence = 0
    game_sequence_counter = 0

    for team in line_score:
        if (team["GAME_SEQUENCE"] != current_game_sequence):
            current_game["TEAM_1_ABBREVIATION"] = team["TEAM_ABBREVIATION"]
            current_game["TEAM_1_WINS_LOSSES"] = team["TEAM_WINS_LOSSES"]

            current_game["TEAM_1_PTS"] = team["TEAM_PTS"]
            current_game["TEAM_1_ID"] = team["TEAM_ID"]

            current_game_sequence = team["GAME SEQUENCE"]
            game_sequence_counter += 1
        elif (game_sequence_counter == 1):
            current_game["TEAM_2_ABBREVIATION"] = team["TEAM_ABBREVIATION"]
            current_game["TEAM_2_WINS_LOSSES"] = team["TEAM_WINS_LOSSES"]
            
            current_game["TEAM_2_PTS"] = team["TEAM_PTS"]
            current_game["TEAM_2_ID"] = team["TEAM_ID"]           

            current_game["GAME_ID"] = team["GAME_ID"]

            games.append(current_game)

            current_game = {}
            game_sequence_counter = 0

    return games

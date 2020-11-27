import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import requests
import boto3
import os
from os.path import expanduser
from nba_utilities import mongo_connector as mc
import mongo_df_builder
import numpy as np
from datetime import datetime, date


def top_nav_bar():
    return html.Div([
        html.Nav(className='navbar navbar-dark fixed-top bg-dark flex-md-nowrap p-0', children=[
            html.Div(className='nav-sf-title', children=[
                html.Img(
                    src='https://3j9exr2e2kk1lvioh1y3bof1-wpengine.netdna-ssl.com/wp-content/uploads/2017/06/footer-logo.png',
                    className='sf-logo'),
                html.Div(className='sf-title', children=[
                    dcc.Link(className='nav-title', href='/', children=[
                        html.H1('NBA Jam', className="app-header--title")
                    ]),
                ]),
            ]),
        ]),
        html.Br()
    ])

class team_charts:

    def __init__(self):
        _mongo = mc.main()
        db = _mongo.warehouse

        self.df = mongo_df_builder.Main('basic stats').df
        self.rosters = mongo_df_builder.Main('rosters').df

        self._data_cleaner()
        self._team_looper()

    def _data_cleaner(self):
        # limit to just current season
        self.df = self.df[self.df['date'] >= datetime(2019, 10, 22)]

        # get list of teams
        self.teams = [ team for team in self.df['team'].unique() ]

        # reformat some fields as float
        self.df['pts'] = self.df['pts'].astype(float)

    def _team_looper(self):
        # for team in self.teams:
        self.charts = []
        for team in self.teams:
            roster = self.rosters[self.rosters['team'] == team]
            sub = self.df[self.df['team'] == team]

            # build mapping of each player to their total games played
            player_games = pd.DataFrame([ { 'player': player, 'games': len(sub[sub['player'] == player]['game_id'].unique()) } for player in sub['player'].unique() ])
            sub = sub.groupby(['player'], as_index=False).agg({'pts': 'sum'})

            sub = sub.merge(player_games, how='left', on='player')

            # now merge in roster info
            sub = sub.merge(roster, how='left', left_on='player', right_on='player_id')

            # create per-game columns
            sub['pts_pg'] = sub['pts'] / sub['games']

            # groupby position (optional)
            sub = sub.groupby(['position'], as_index=False).agg({'pts_pg': 'sum'})

            # now build chart for the current team
            self.charts.append(self._per_game_chart(sub.sort_values('pts_pg', ascending=False), team))


    def _per_game_chart(self, sub, team):
        if team == 'WAS':
            print sub
        fig = px.bar(sub, x='position', y='pts_pg')
        chart = dcc.Graph(
                    id='per-game-chart',
                    figure=fig
        )
        fig.update_layout(title_text=team)
        return chart


if __name__ == "__main__":
    team_charts()

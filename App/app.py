import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import flask
import os
from random import randint
import app_utilities as utils


server = flask.Flask(__name__)
server.secret_key = os.environ.get('secret_key', str(randint(0, 1000000)))
app = dash.Dash(__name__, server=server)

app.title = 'NBA Jam'
app.css.append_css({'external_url': "https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.css"})
# for loading screens
app.css.append_css({'external_url': "https://codepen.io/chriddyp/pen/brPBPO.css"})

# supress exceptions during debug
app.config.suppress_callback_exceptions = True
#
app.css.config.serve_locally=False

# serve layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# display page
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname is None:
        return main_layout
    elif pathname == '/':
        return main_layout

    return None

# home page layout (just contains top & side navbars for now)
main_layout = html.Div(children=[
    utils.top_nav_bar(),
    html.Div(children=[
        html.Br(),
        html.Br(),
        html.Div(id='per-game-charts')
    ])
], style={'background-color': '#3c414a'})

@app.callback(
    Output('per-game-charts', 'children'),
    [Input('url', 'pathname')]
)
def _build_pgame_charts(pathname):
    if pathname != '/':
        return None
    else:
        pass

    content = []
    for chart in utils.team_charts().charts:
        content.append(dbc.Col(chart, className='floating-chart'))

    return dbc.Row(content)

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)

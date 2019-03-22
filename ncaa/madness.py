import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, Event
import dash_table
import styling
import pandas as pd
import madness_helper as helper
from nba_utilities.db_connection_manager import establish_db_connection

app = dash.Dash()
app.title = "Madness"
app.css.append_css({'external_url':"https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css"})
conn = establish_db_connection('sqlalchemy').connect()

teams = pd.read_sql('SELECT DISTINCT team FROM kenpom_four_factors_data', con=conn)
teams = [ row['team'] for index, row in teams.iterrows() ]
teams = [ {'label': team, 'value': team} for team in sorted(teams) ]

def serve_layout():
    return html.Div(children = [
        html.Div(className="app-header", children = [
            html.H1('Alge-bracket', className="app-header--title", style=styling.portal_header_txt)], style = styling.portal_header_bgrd),
            dcc.Tabs(id="tabs", children=[

                #### Head 2 Head Predictor Tab ####
                dcc.Tab(label='H2H Predictor', children=[
                    html.H1(children='Matchup Predictor', style=styling.tab_header),
                    html.Div(style={'padding':10}),
                    html.Div(className='row', children=[
                            html.Div(html.H1(children='Select Team A: ', style=styling.filter_title), className='col-2'),
                            html.Div(dcc.Dropdown(id='team-a-dropdown', options=teams, value='Duke'), className='col-4'),
                            html.Div(html.H1(children='Select Team B: ', style=styling.filter_title), className='col-2'),
                            html.Div(dcc.Dropdown(id='team-b-dropdown', options=teams, value='Gonzaga'), className='col-4'),
                                ]),
                    html.Div(style={'padding':10}),
                    html.Div(className='row', children=[
                            html.Div(className='col-5'),
                            html.Div(id='spread', children=[], style={'box-shadow': '0 4px 8px 0 rgba(0,0,0,0.2)',
                                                                      'fontSize': 24}),
                            html.Div(className='col-5'),
                                ]),
                    ]),

                #### Bracket Tab ####
                dcc.Tab(label='Bracket', children=[
                    html.H1(children='Predicted Bracket', style=styling.tab_header),
                    ]),

                #### Rankings ####
                dcc.Tab(label='Rankings', children=[
                    html.H1(children='Current Week', style=styling.tab_header),
                    ]),

                #### Stats ####
                dcc.Tab(label='Stats', children=[
                    html.H1(children='Team Offense', style=styling.tab_header),
                    html.H1(style={'padding':10}),
                    html.H1(children='Team Defense', style=styling.tab_header),
                    ]),
                ])
                    ])

app.layout = serve_layout

@app.callback(
    Output('spread', 'children'),
    [Input('team-a-dropdown', 'value'),
     Input('team-b-dropdown', 'value')]
)
def update_value(team_a, team_b):
    spread = helper.four_factors_algo(team_a, team_b)
    if spread > 0:
        spread = '+%s'%spread
    return '{} {}'.format(team_b, spread)

if __name__ == "__main__":
    app.run_server(debug=True)

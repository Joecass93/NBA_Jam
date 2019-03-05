import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, Event
import dash_table
import styling

app = dash.Dash()
app.css.append_css({'external_url':"https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css"})

def serve_layout():
    return html.Div(children = [
        html.Div(className="app-header", children = [
            html.H1('Alge-bracket', className="app-header--title", style=styling.portal_header_txt)], style = styling.portal_header_bgrd),
            dcc.Tabs(id="tabs", children=[
                #### Daily Report Tab ####
                dcc.Tab(label='Bracket', children=[
                    html.H1(children='Predicted Bracket', style=styling.tab_header),
                    ]),
                dcc.Tab(label='H2H Predictor', children=[
                    html.H1(children='Predict H2H Matchup', style=styling.tab_header),
                    ]),
                dcc.Tab(label='Rankings', children=[
                    html.H1(children='Current Week', style=styling.tab_header),
                    ]),
                dcc.Tab(label='Stats', children=[
                    html.H1(children='Team Offense', style=styling.tab_header),
                    html.H1(style={'padding':10}),
                    html.H1(children='Team Defense', style=styling.tab_header),
                    ]),
                ])
                    ])

app.layout = serve_layout

if __name__ == "__main__":
    app.run_server(debug=True)

import os
import datetime
import dash
import dash_daq as daq
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from pathlib import Path
from collections import Counter, OrderedDict

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def serve_layout():
    fig = px.bar(stats(), barmode="group")
    return html.Div([
        html.H1(
            children='Total keystrokes',
            style={ 'textAlign': 'center'}
        ),
        daq.LEDDisplay(
            id='my-LED-display',
            label="",
            color="#103366",
            value=stats()['freq'].sum(),
            style={ 'textAlign': 'center'}
        ),
        html.Br(), html.Br(),
        html.Div(children=[
            html.H1(children='Keystroke graph', style={'textAlign': 'center'}),
            dcc.Graph(
                id='example-graph',
                figure=fig
            )
        ])
    ])


if __name__ == "__main__":
    app.layout = serve_layout
    app.run_server(host='0.0.0.0', port=8050)

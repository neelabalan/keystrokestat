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
from keymap import keymap

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

home = str(Path.home())
logname =  str(datetime.datetime.now().date()) + 'keystrokes.log'
logdir =  home + '/.keystrokestat/'
logpath =  logdir + logname

if not os.path.exists(logdir):
    os.makedirs(logdir)

def filter_key_release(lines):
    ''' filter key release string in lines '''
    for line in lines:
        return line.startswith('key press') 


def get_key_presses(contents):
    ''' returns keycodes as list '''
    lines = contents.splitlines()
    filteredLines = filter(
        lambda line: line.startswith('key press') is True, lines)
    keypresses = [
        keymap.get(
            int(
                list(filter(None, keycode.split(' ')))
            )[-1]
        )
        for keycode in filteredLines
    ]
    return keypresses


def get_contents():
    with open(logpath, 'r') as file:
        contents = file.read()
        return contents


def stats():
    '''get stats in df'''
    contents = get_contents()
    keypresses = get_key_presses(contents)
    freq_map = Counter(keypresses).most_common()
    df = pd.DataFrame.from_dict(freq_map)
    df.columns = ['keys', 'freq']
    df.set_index('keys', inplace=True)
    return df


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

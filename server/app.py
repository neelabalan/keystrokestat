import datetime
import sqlite3

import dash
import dash_daq as daq
from numpy import append
import plotly.graph_objs as go
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd


# testing
test_path = '/home/blue/.keystroke/keystrokes.db'
DB_PATH = '/root/.keystroke/keystorkes.db'
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, update_title=None)

data = {
    'time': [],
    'keystrokes': [],
    'last_updated': None
}


def data_for_the_day():
    """ total keystrokes for the day from db """
    with sqlite3.connect(test_path) as conn:
    # with sqlite3.connect(DB_PATH) as conn:
        query = "select * from keystroke where timestamp like '{}%'".format(
            str(datetime.datetime.now().date())
        )
        return pd.read_sql(query, con=conn)


def get_total_keystrokes():
    return data_for_the_day()["total"].sum()


def get_sum_of_all_keypress():
    return data_for_the_day() \
        .sum() \
        .to_frame() \
        .reset_index() \
        .drop([0, 102, 103]) \
        .rename(columns={'index': 'keystroke', 0: 'frequency'})


def serve_layout():
    bar_fig = px.bar(get_sum_of_all_keypress(), x='keystroke', y='frequency', barmode="group")
    return html.Div(
        [
            html.H1(children="Total keystrokes", style={"textAlign": "center"}),
            daq.LEDDisplay(
                id="live-count-update",
                label="",
                color="#103366",
                value='0',
                style={"textAlign": "center"},
            ),
            html.Br(),
            html.Br(),
            html.Div(
                children=[
                    html.H1(children="Keystroke graph", style={"textAlign": "center"}),
                    dcc.Graph(id="example-graph", figure=bar_fig),
                ]
            ),
            dcc.Graph(
                id='live-update-graph',
                # animate = True
            ),
            dcc.Interval(
                id='interval-component',
                interval=5*1000, # in milliseconds
                n_intervals=0
            )
        ]
    )

@app.callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph_live(n):
    

    # Collect some data
    db_data = data_for_the_day()
    last_val = db_data['total'].iloc[-1]

    last_timestamp = db_data['timestamp'].iloc[-1]
    if data['last_updated'] == last_timestamp:
        data['keystrokes'].append(0)
    else:
        data['keystrokes'].append(last_val)
        data['last_updated'] = last_timestamp

    data['time'].append(datetime.datetime.now().strftime('%X'))
    fig = go.Figure(data=[go.Scatter(x=data['time'], y=data['keystrokes'])])

    return fig

@app.callback(
    Output('live-count-update', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_total_count(n):
    return str(get_total_keystrokes())


if __name__ == "__main__":
    app.layout = serve_layout
    app.run_server(host="0.0.0.0", port=8050)

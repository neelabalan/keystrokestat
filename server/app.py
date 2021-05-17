import datetime

import sqlite3
import dash
import dash_daq as daq
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

# testing
# engine = create_engine('sqlite:////home/blue/.keystroke/keystrokes.db')
conn = sqlite3.connect("/root/.keystroke/keystrokes.db")
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def data_for_the_day():
    """ total keystrokes for the day from db """
    with conn: 
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
        .drop([0, 101, 102]) \
        .rename(columns={'index': 'keystroke', 0: 'frequency'})


def serve_layout():
    bar_fig = px.bar(get_sum_of_all_keypress(), x='keystroke', y='frequency', barmode="group")
    pie_fig = px.pie(get_sum_of_all_keypress().head(), values='frequency', names='keystroke', title='keypress pie distribution')
    return html.Div(
        [
            html.H1(children="Total keystrokes", style={"textAlign": "center"}),
            daq.LEDDisplay(
                id="my-LED-display",
                label="",
                color="#103366",
                value=get_total_keystrokes(),
                style={"textAlign": "center"},
            ),
            html.Br(),
            html.Br(),
            html.Div(
                children=[
                    html.H1(children="Keystroke graph", style={"textAlign": "center"}),
                    dcc.Graph(id="example-graph", figure=bar_fig),
                    dcc.Graph(id="pie-graph", figure=pie_fig)
                ]
            ),
        ]
    )


if __name__ == "__main__":
    app.layout = serve_layout
    app.run_server(host="0.0.0.0", port=8050)

import datetime
import dash
import dash_daq as daq
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from sqlalchemy import create_engine

# testing
# engine = create_engine('sqlite:////home/blue/.keystroke/keystrokes.db')
engine = create_engine('sqlite:////root/.keystroke/keystrokes.db')
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def data_for_the_day():
    ''' total keystrokes for the day from db '''
    with engine.connect() as conn:
        query = "select * from keystroke where timestamp like '{}%'".format(str(datetime.datetime.now().date()))
        return pd.read_sql(query, con=conn)

def get_total_keystrokes():
    return data_for_the_day()['total'].sum()

def get_sum_of_all_keypress():
    print(data_for_the_day().sum().drop(['total', 'timestamp']))
    return pd.DataFrame(data_for_the_day().sum().drop(['total', 'timestamp']))

def serve_layout():
    fig = px.bar(get_sum_of_all_keypress(), barmode="group")
    return html.Div([
        html.H1(
            children='Total keystrokes',
            style={ 'textAlign': 'center'}
        ),
        daq.LEDDisplay(
            id='my-LED-display',
            label="",
            color="#103366",
            value=get_total_keystrokes(),
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

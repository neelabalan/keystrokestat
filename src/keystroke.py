import subprocess
import argparse
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

def remove_empty_str_from_list(stringList):
    ''' removes empty strings from list '''
    return [string for string in stringList if string]


def getPIDs(output, targetProcess):
    ''' get pid for running target process '''
    filteredProcessList = [
        str(process) for process in output.splitlines() if targetProcess in str(process)]
    pids = list()
    for process in filteredProcessList:
        process = removeEmptyStringFromList(process.split(' '))
        pids.append(process[1])
    return pids


def kill(targetProcess):
    ''' kills the xinput test process '''
    if targetProcess:
        process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
        output, error = process.communicate()
        pids = getPIDs(output, targetProcess)
        for pid in pids:
            print('killing PID {}'.format(pid))
            os.kill(int(pid), 9)


def run():
    ''' run the app and log the keystrokes in keystroke.log '''
    logfile = open(logpath, 'w')
    try:
        xinput_ids = subprocess.Popen(
            "xinput list | grep -Po 'id=\K\d+(?=.*slave\s*keyboard)'",
            shell=True,
            stdout=subprocess.PIPE
        ).communicate()[0]

        command = "echo " + \
            xinput_ids.decode('utf-8').replace('\n', ' ') + \
            " | xargs -P0 -n1 xinput test"
        echos = subprocess.Popen(command, shell=True, stdout=logfile)
    except:
        print('EXCEPTION not valid device id')


def filter_key_release(lines):
    ''' filter key release string in lines '''
    for line in lines:
        return True if line.startswith('key press') else False


def get_key_presses(contents):
    ''' returns keycodes as list '''
    lines = contents.splitlines()
    filteredLines = filter(
        lambda line: line.startswith('key press') is True, lines)
    keypresses = [
        keymap.get(
            int(
                remove_empty_str_from_list(
                    keycode.split(' ')
                )[-1]
            )
        ) for keycode in filteredLines
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s',
        '--stats',
        action='store_true',
        help='show the stats'
    )
    parser.add_argument(
        '-r',
        '--run',
        action='store_true',
        help='spwans a thread to record the keystrokes'
    )
    parser.add_argument(
        '-k',
        '--kill',
        action='store_true',
        help='kills the xinput test process'
    )

    args = parser.parse_args()
    if args:
        if args.run:
            run()
        elif args.kill:
            kill('xinput test')
        elif args.stats:
            app.layout = serve_layout
            app.run_server(debug=True)

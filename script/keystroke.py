import subprocess
import argparse
import datetime
import pandas as pd
import datetime
import os
from pathlib import Path
from collections import Counter, OrderedDict
from sqlalchemy import create_engine
from apscheduler.schedulers.background import BackgroundScheduler
from keymap import keymap

SCHEDULER_INTERVAL= 5
scheduler = BackgroundScheduler(daemon=True)
engine = create_engine('sqlite:///{}/.keystroke/keystrokes.db'.format(str(Path.home())))
sqlite_connection = engine.connect()

def get_xinput_ids():
    try:
        xinput_ids = subprocess.Popen(
            "xinput list | grep -Po 'id=\K\d+(?=.*slave\s*keyboard)'",
            shell=True,
            stdout=subprocess.PIPE
        ).communicate()[0]
        return xinput_ids.decode('utf-8').replace('\n', ' ')
    except:
        print('EXCEPTION xinput ID not found')


def get_pids(output, target_process):
    ''' get PID for running target process '''
    filtered_process_list = [
        str(process) for process in output.splitlines() if target_process in str(process)
    ]
    pids = list()
    for process in filtered_process_list:
        process = list(filter(None, process.split(' ')))
        pids.append(process[1])
    return pids


def kill(target_process):
    ''' kills the xinput test process '''
    if target_process:
        process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
        output, error = process.communicate()
        pids = get_pids(output, target_process)
        for pid in pids:
            print('killing PID {}'.format(pid))
            os.kill(int(pid), 9)

def read_buffer(buffer):
    ''' read standard out buffer '''
    return buffer.stdout.read1().decode('utf-8')

def split_text(buffer_text: str):
    ''' split text on \n '''
    return buffer_text.split('\n')

def filter_text(lines):
    ''' filter empty strings and key releases '''
    filtered_lines = filter(
        lambda line: line.startswith('key press'), lines
    )
    return list(filter(None, filtered_lines))

def map_keycode_to_keys(filtered_lines):
    return [
        keymap.get(
            int(
                list(
                    filter(None, keycode.split(' '))
                )[-1]
            )
        ) for keycode in filtered_lines
    ] 

def workflow(buffer):
    ''' 
    -> read from buffer 
    -> transform text for easy filtering 
    -> filter key releases and empty string 
    -> map xinput code to char
    -> transform pd dataframe and store to sqlite
    '''
    keypress = map_keycode_to_keys(
            filter_text(
                split_text(
                    read_buffer(buffer)
                )
        )
    )
    df = pd.DataFrame.from_dict(
        [
            {
                **Counter(keypress), 
                **{
                    'timestamp': datetime.datetime.now(), 
                    'total': len(keypress)
                }
            }
        ]
    )
    # print(df.head())

    df.to_sql('keystroke', sqlite_connection, if_exists='append')

def run():
    ''' run the app and log the keystrokes BufferedReader '''
    echos = None
    try:
        command = "echo " + get_xinput_ids() + " | xargs -P0 -n1 xinput test"
        echos = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    except:
        print('EXCEPTION not valid device id')

    # workflow(echos)
    scheduler.add_job(workflow, trigger='interval', seconds=SCHEDULER_INTERVAL, args=(echos,))
    scheduler.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
        else:
            print('wrong arguments provided')
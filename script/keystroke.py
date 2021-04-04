import subprocess
import argparse
import datetime
import pandas as pd
import datetime
from pathlib import Path
from collections import Counter, OrderedDict
from sqlalchemy import create_engine
from apscheduler.schedulers.background import BackgroundScheduler


SCHEDULER_INTERVAL_MINS = 5
scheduler = BackgroundScheduler(daemon=True)
engine = create_engine('sqlite:///keystrokes.db')

# def remove_empty_str_from_list(string_list):
#     ''' removes empty strings from list '''
#     return [string for string in string_list if string]

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
        process = remove_empty_strings_from_list(process.split(' '))
        pids.append(process[1])
    return pids


def kill(target_process):
    ''' kills the xinput test process '''
    if targetProcess:
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
        lambda key_release_filter: line.startswith('key press'), lines
    )
    return list(filter(None, filtered_lines))

def map_keycode_to_keys(filtered_lines):
    keymap.get(
        int(
            list(
                filter(None, keycode.split(' '))
            )[-1]
        )
    ) for keycode in filtered_lines 

# TODO: pass args buffer
@sched.scheduled_job('interval', minutes=SCHEDULER_INTERVAL_MINS)
def workflow():
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
        {**Counter(keypress), **{'timestamp': datetime.datetime.now(), 'total': len(keypress)}}
    )

    engine.connect()
    df.to_sql('keystroke', sqlite_connection, if_exists='append')
    # engine.close()

def run():
    ''' run the app and log the keystrokes BufferedReader '''
    echos = None
    try:
        command = "echo " + get_xinput_ids() + " | xargs -P0 -n1 xinput test"
        echos = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    except:
        print('EXCEPTION not valid device id')

    scheduler.start()
    return echos

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
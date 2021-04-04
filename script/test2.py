import threading
import subprocess
import pandas as pd
import datetime
from queue import Queue
from apscheduler.schedulers.background import BackgroundScheduler

keypresses = Queue()
sched = BackgroundScheduler(daemon=True)
cmd = 'xinput --test 11'
a = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

def getkeypress():
    for line in a.stdout:
        keypress = get_key_presses(line.decode('utf-8'))
        if keypress:
            yield keypress
        # if line.decode('utf-8').startswith('key press'):
        #     yield line.decode('utf-8') 

def insert_to_queue():
    for keypress in getkeypress():
        keypresses.put((keypress, datetime.datetime.now()))

# pandas_storage
# for m in range(keypresses.qsize()):
@sched.scheduled_job('interval', seconds=5)
def print_key_presses():
    print('scheduler running')
    df = get_key_presses()
    if df.empty:
        print('nothing to show\n\n')
    else:
        print(df.head())

def get_key_presses():
    if keypresses.qsize():
        return pd.concat(
            [
                pd.DataFrame(
                    [keypresses.get()], columns=['keypress', 'datetime']
                )
                for i in range(keypresses.qsize())
            ], ignore_index=True
        )
    else:
        return pd.DataFrame()
    # print(q.get())

def remove_empty_str_from_list(stringList):
    ''' removes empty strings from list '''
    return [string for string in stringList if string]

def filter_key_release(line):
    ''' filter key release string in lines '''
    # for line in lines:
    return line.startswith('key press') 


def get_key_presses(line):
    ''' returns keycodes as list '''
    if line.startswith('key press'):
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

x = threading.Thread(target=insert_to_queue)
sched.start()
x.start()
x.join()

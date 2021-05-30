import subprocess
import datetime
import os
import sys
import time
import sqlite3
import operator
import itertools
import functools
from pathlib import Path
from collections import Counter
import logging


import pandas as pd
import click
from rich.live import Live
from rich.table import Table
from rich.align import Align
from rich.console import Console
from apscheduler.schedulers.background import BackgroundScheduler

from keymap import keymap

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.ERROR)

SCHEDULER_INTERVAL = 5
scheduler = BackgroundScheduler(daemon=True)
total_keystrokes = Counter({})
console = Console()


def get_xinput_ids():
    try:
        xinput_ids = subprocess.Popen(
            "xinput list | grep -Po 'id=\K\d+(?=.*slave\s*keyboard)'",
            shell=True,
            stdout=subprocess.PIPE,
        ).communicate()[0]
        return xinput_ids.decode('utf-8').replace('\n', ' ')
    except:
        print('EXCEPTION xinput ID not found')


def get_pids(output, target_process):
    '''get PID for running target process'''
    filtered_process_list = [
        str(process)
        for process in output.splitlines()
        if target_process in str(process)
    ]
    pids = list()
    for process in filtered_process_list:
        process = list(filter(None, process.split(' ')))
        pids.append(process[1])
    return pids


def kill(target_process):
    '''kills the xinput test process'''
    if target_process:
        process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
        output, error = process.communicate()
        pids = get_pids(output, target_process)
        for pid in pids:
            print('killing PID {}'.format(pid))
            os.kill(int(pid), 9)


def read_buffer(buffer):
    '''read standard out buffer'''
    return buffer.stdout.read1().decode('utf-8')


def split_text(buffer_text):
    '''split text on newline'''
    return buffer_text.split('\n')


def filter_text(lines):
    '''filter empty strings and key releases'''
    filtered_lines = filter(lambda line: line.startswith('key press'), lines)
    return list(filter(None, filtered_lines))


def map_keycode_to_keys(filtered_lines):
    '''mapping xinput keycodes to keyboard keys'''
    return [
        keymap.get(int(list(filter(None, keycode.split(' ')))[-1]))
        for keycode in filtered_lines
    ]


def workflow(buffer):
    '''
    -> read from buffer
    -> transform text for easy filtering
    -> filter key releases and empty string
    -> map xinput code to char
    -> transform to pandas dataframe and write to sqlite
    '''
    global total_keystrokes
    buffer_text = read_buffer(buffer)
    if buffer_text:
        keypress = map_keycode_to_keys(filter_text(split_text(buffer_text)))
        meta_dict = dict(timestamp=datetime.datetime.now(), total=len(keypress))
        keystrokes = Counter(keypress)
        total_keystrokes += keystrokes
        total_keystrokes = Counter(
            dict(
                sorted(
                    total_keystrokes.items(), key=operator.itemgetter(1), reverse=True
                )
            )
        )

    df = pd.DataFrame(
        [{**keystrokes, **meta_dict}],
        columns=list(keymap.values()) + list(meta_dict.keys()),
    )

    with sqlite3.connect(
        '/{}/.keystroke/keystrokes.db'.format(str(Path.home()))
    ) as conn:
        df.to_sql('keystroke', con=conn, if_exists='append')


def generate_table(count):
    '''make a new table'''
    table = Table(title="keypress frequency")
    table.add_column('Key')
    table.add_column('Frequency')
    temp_dict = dict(itertools.islice(total_keystrokes.items(), count))
    for key, val in temp_dict.items():
        table.add_row(key, str(val))
    return Align.center(table) 


def render_table(count):
    '''display table with top key counts'''
    generate_n_rows_table = functools.partial(generate_table, count)
    with Live(
        generate_n_rows_table(), 
        console=console.clear(), 
        refresh_per_second=SCHEDULER_INTERVAL
    ) as live:
        while True:
            time.sleep(SCHEDULER_INTERVAL)
            live.update(generate_n_rows_table())


@click.command()
@click.option(
    '--view',
    is_flag=False,
    default=False,
    flag_value=10,
    help='displays top frequently used keys',
)
@click.option('--pkill', is_flag=True, help='kill all instances of xinput')
def run(view , pkill):
    '''run workflow and log the keystrokes'''
    echos = None
    try:
        command = 'echo ' + get_xinput_ids() + ' | xargs -P0 -n1 xinput test'
        echos = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    except:
        print('EXCEPTION not valid device id')

    scheduler.add_job(
        workflow,
        trigger='interval',
        seconds=SCHEDULER_INTERVAL,
        coalesce=True,
        args=(echos,),
    )
    scheduler.start()

    try:
        if pkill:
            kill('xinput test')
        elif view:
            render_table(int(view))
        else:
            while True:
                time.sleep(2)

    except (KeyboardInterrupt, SystemExit):
        kill('xinput test')
        scheduler.shutdown()


if __name__ == '__main__':
    run()

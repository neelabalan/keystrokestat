import subprocess
import datetime
import pandas as pd
import datetime
import os
import sys
from pathlib import Path
from collections import Counter
from sqlalchemy import create_engine
from apscheduler.schedulers.background import BackgroundScheduler
from keymap import keymap

SCHEDULER_INTERVAL = 5
scheduler = BackgroundScheduler(daemon=True)
engine = create_engine("sqlite:///{}/.keystroke/keystrokes.db".format(str(Path.home())))


def get_xinput_ids()    :
    try:
        xinput_ids = subprocess.Popen(
            "xinput list | grep -Po 'id=\K\d+(?=.*slave\s*keyboard)'",
            shell=True,
            stdout=subprocess.PIPE,
        ).communicate()[0]
        return xinput_ids.decode("utf-8").replace("\n", " ")
    except:
        print("EXCEPTION xinput ID not found")


def get_pids(output, target_process):
    """ get PID for running target process """
    filtered_process_list = [
        str(process)
        for process in output.splitlines()
        if target_process in str(process)
    ]
    pids = list()
    for process in filtered_process_list:
        process = list(filter(None, process.split(" ")))
        pids.append(process[1])
    return pids


def kill(target_process):
    """ kills the xinput test process """
    if target_process:
        process = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
        output, error = process.communicate()
        pids = get_pids(output, target_process)
        for pid in pids:
            print("killing PID {}".format(pid))
            os.kill(int(pid), 9)


def read_buffer(buffer):
    """ read standard out buffer """
    return buffer.stdout.read1().decode("utf-8")


def split_text(buffer_text: str):
    """ split text on \n """
    return buffer_text.split("\n")


def filter_text(lines):
    """ filter empty strings and key releases """
    filtered_lines = filter(lambda line: line.startswith("key press"), lines)
    return list(filter(None, filtered_lines))


def map_keycode_to_keys(filtered_lines):
    """ mapping xinput keycodes to keyboard keys """
    return [
        keymap.get(int(list(filter(None, keycode.split(" ")))[-1]))
        for keycode in filtered_lines
    ]


def workflow(buffer):
    """
    -> read from buffer
    -> transform text for easy filtering
    -> filter key releases and empty string
    -> map xinput code to char
    -> transform to pandas dataframe and write to sqlite
    """
    sqlite_connection = engine.connect()
    keypress = map_keycode_to_keys(filter_text(split_text(read_buffer(buffer))))
    meta_dict = {
        "timestamp": datetime.datetime.now(),
        "total": len(keypress),
    }
    df = pd.DataFrame(
        [{**Counter(keypress), **meta_dict}],
        columns=list(keymap.values()) + list(meta_dict.keys()),
    )
    print(df.head())

    if keypress:
        df.to_sql("keystroke", sqlite_connection, if_exists="append")
    sqlite_connection.close()


def run():
    """ run the app and log the keystrokes BufferedReader """
    echos = None
    try:
        command = "echo " + get_xinput_ids() + " | xargs -P0 -n1 xinput test"
        echos = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    except:
        print("EXCEPTION not valid device id")

    # testing
    # workflow(echos)
    scheduler.add_job(
        workflow, trigger="interval", seconds=SCHEDULER_INTERVAL, args=(echos,)
    )
    scheduler.start()
    import time

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        kill('xinput test')
        scheduler.shutdown()


if __name__ == "__main__":
    arg = sys.argv[1]
    if arg == "-r":
        run()
    elif arg == "-k":
        kill("xinput test")
    else:
        print("wrong arguments provided")

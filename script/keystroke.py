import subprocess
import argparse
import os
import datetime
from pathlib import Path
from collections import Counter, OrderedDict

home = str(Path.home())
logname =  str(datetime.datetime.now().date()) + 'keystrokes.log'
logdir =  home + '/.keystrokestat/'
logpath =  logdir + logname

if not os.path.exists(logdir):
    os.makedirs(logdir)

def remove_empty_str_from_list(str_list):
    ''' removes empty strings from list '''
    return [string for string in str_list if string]


def get_pids(output, target_process):
    ''' get pid for running target process '''
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
    if targetProcess:
        process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
        output, error = process.communicate()
        pids = get_pids(output, target_process)
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
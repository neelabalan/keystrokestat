'''
works on xinput test
'''
import subprocess
import argparse
import os
from keymap import keymap
from collections import Counter, OrderedDict
from pytablewriter import MarkdownTableWriter

filepath = os.path.join(
        os.path.expanduser('~'), 
        'keystrokes.log'
    )

def removeEmptyStringFromList(stringList):
    ''' removes empty strings from list '''
    return [string for string in stringList if string]

def getPIDs(output, targetProcess):
    ''' get pid for running target process '''
    filteredProcessList  = [str(process) for process in output.splitlines() if targetProcess in str(process)]
    pids = list()
    for process in filteredProcessList:
        process = removeEmptyStringFromList(process.split(' '))
        pids.append(process[1])
    return pids


def run(deviceid):
    ''' run the app and log the keystrokes in keystroke.log '''
    logfile = open(filepath, 'w')
    try:
        process = subprocess.Popen(['xinput', 'test', '{}'.format(deviceid)], stdout=logfile)
    except:
        print('EXCEPTION not valid device id')


def kill(targetProcess):
    ''' kills the xinput test process '''
    if targetProcess:
        process         = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
        output, error   = process.communicate()
        pids            = getPIDs(output, targetProcess)
        for pid in pids:
            print('killing PID {}'.format(pid))
            os.kill(int(pid), 9)

def filterKeyRelease(lines):
    ''' filter key release string in lines '''
    for line in lines:
        return True if line.startswith('key press') else False

def getKeyPresses(contents):
    ''' returns keycodes as list '''
    lines         = contents.splitlines()
    filteredLines = filter(lambda line: line.startswith('key press') is True, lines)
    keypresses    = [
        keymap.get(
            int(
                removeEmptyStringFromList(
                    keycode.split(' ')
                )[-1]
            ) 
        ) for keycode in filteredLines
    ]
    return keypresses


def stats():
    ''' 
    show stats in table form 
    can be exported to markdown
    '''
    with open(filepath, 'r') as file:
        # taking only key press
        contents     = file.read()
        keypresses   = getKeyPresses(contents)
        frequencyMap = Counter(keypresses)
        print(frequencyMap)
        total        = sum(frequencyMap.values())

        writer              = MarkdownTableWriter(
            headers      = ['keys', 'frequency', 'percentage'],
            value_matrix = [
                [char, frequency, (frequency/total)*100] 
                for char, frequency in 
                sorted(
                    frequencyMap.items(), 
                    key = lambda item: item[1], 
                    reverse=True
                )
            ]
        )
        writer.write_table()


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
            run(args.run)
        elif args.kill:
            kill('xinput test')
        elif args.stats:
            stats()   

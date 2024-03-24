import os
import sys


filename = 'pylot.log'

events = {
    'traffic light': -1,
    'lane-invasion': 0,
    'collision': 0
}

with open(filename, 'r') as f:
    for line in f:
        if 'event from the simulator' in line:
            for event in events:
                if event in line:
                    events[event] += 1

with open(sys.argv[1], 'a') as f:
    output_str = ' '.join([f"{k}:{v}" for k, v in events.items()])+'\n'
    f.writelines(output_str)

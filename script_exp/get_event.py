import os
import sys
import re
import pickle
import os

filename = 'pylot.log'


save_dir = './'

events = {
    'traffic light': 0,
    'lane-invasion': 0,
    'collision': []
}

x, y = [], []

with open(filename, 'r') as f:
    for line in f:
        if 'event from the simulator' in line:
            for event in events:
                if event in line:
                    if event == 'collision':
                        events[event].append(
                            re.findall(r'@\[(\d+)\]', line)[0])
                    else:
                        events[event] += 1
        # if 'RRT* Path' in line:
        #     log = ' '.join(line.split(' ')[1:])
        #     num = re.findall(r'-?\d+\.\d+', log)[0]
        #     if 'RRT* Path X' in log:
        #         x.append(float(num))
        #     else:
        #         y.append(-float(num))

with open(os.path.join(save_dir, sys.argv[1]), 'a') as f:
    output_str = ' '.join([f"{k}:{v}" for k, v in events.items()])+'\n'
    f.writelines(output_str)

# with open(os.path.join(save_dir, sys.argv[2]+'.pkl'), 'wb') as f:
#     pickle.dump((x, y), f)

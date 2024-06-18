import gym
import pathlib
from util.fileutils import load_json
from util.obstacle import get_init_obstacle
from Handler import PylotAfterPerecptionHandler
import glob
import random


class OfflinePerturbDetectionENV(gym.Env):
    def __init__(self):
        super(OfflinePerturbDetectionENV, self).__init__()
        self.base_dir = pathlib.Path('/home/erdos/workspace/pylot/data_RL/scc4/RL_profile1')
        self.profile_timestamps = sorted([int(pathlib.Path(x).stem.split('-')[1]) for x in glob.glob(str(self.base_dir.joinpath('bboxes').joinpath('*.json')))])
        self.state = self._init_state()

        
        

    def reset(self):
        pass
        

    def step(self, action):
        pass

    def render(self):
        pass

    def _init_state(self):
        self.timestamp = random.choice(self.profile_timestamps)
        self.handler = PylotAfterPerecptionHandler(self.base_dir, self.timestamp)
        state = self.handler.get_bbox_state()
        return state

import gym
import pathlib
from util.fileutils import load_json
from modules.obstacle import get_init_obstacle
from Handler import PylotAfterPerecptionHandler
import glob
import random
from util.bbox_handler import BboxHandler


class OfflinePerturbDetectionENV(gym.Env):
    def __init__(self):
        super(OfflinePerturbDetectionENV, self).__init__()
        self.base_dir = pathlib.Path('/home/erdos/workspace/pylot/data_RL/scc4/RL_profile1')
        self.profile_timestamps = sorted([int(pathlib.Path(x).stem.split('-')[1]) for x in glob.glob(str(self.base_dir.joinpath('bboxes').joinpath('*.json')))])
        self.obstacles, self.dists = self._init_state()
        self.bboxes = [ob.bounding_box for ob in self.obstacles]
        self.closest_ob_idx = self.dists.index(min(self.dists))
        self.bbox_handler = BboxHandler(self.bboxes[self.closest_ob_idx], 0.4, 0.4)

    def reset(self):
        pass
        
    def step(self, action):
        new_bbox = self.bbox_handler.step(action)
        self.bboxes[self.closest_ob_idx] = new_bbox
        self.handler.step(self.bboxes)


    def render(self):
        pass

    def _init_state(self):
        self.timestamp = random.choice(self.profile_timestamps)
        self.handler = PylotAfterPerecptionHandler(self.base_dir, self.timestamp)
        state, dists = self.handler.get_bbox_state()
        return state, dists

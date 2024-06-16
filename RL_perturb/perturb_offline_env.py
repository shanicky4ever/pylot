import gym
import pathlib
from util.fileutils import load_json
from util.obstacle import get_init_obstacle


class OfflinePerturbDetectionENV(gym.Env):
    def __init__(self):
        super(OfflinePerturbDetectionENV, self).__init__()

    def reset(self):
        pass

    def step(self, action):
        pass

    def render(self):
        pass

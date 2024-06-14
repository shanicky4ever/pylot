from perturb_offline_env import OfflinePerturbDetectionENV
from Handler import PylotAfterPerecptionHandler
import pathlib
from util.fileutils import load_pickle, load_json
from util.obstacle import build_obstacle_from_bbox_info

folder = '/home/erdos/workspace/pylot/data_RL/sc4/RL_profile'
timesatamp = 13587

folder = pathlib.Path(folder)

# env = OfflinePerturbDetectionENV()
#print(obs)
handler = PylotAfterPerecptionHandler(folder, timesatamp)
# handler.step(handler.ini)

next_bbox = load_json(folder.joinpath('bboxes').joinpath(f"bboxes-{timesatamp+500}.json"))
for nb in next_bbox:
    nb['id'] -=40

handler.step(next_bbox)

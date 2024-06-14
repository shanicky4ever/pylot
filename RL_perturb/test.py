from perturb_offline_env import OfflinePerturbDetectionENV
from Handler import PylotAfterPerecptionHandler
import pathlib

folder = '/home/erdos/workspace/pylot/data_RL/scenario4_try/RL_profile'
timesatamp = 13587

folder = pathlib.Path(folder)

# env = OfflinePerturbDetectionENV()
#print(obs)
handler = PylotAfterPerecptionHandler(folder, timesatamp)
# handler.step(handler.ini)

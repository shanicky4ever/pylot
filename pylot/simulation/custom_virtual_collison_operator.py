import erdos
from collections import deque
import os
import shutil
import json

class CustomVirtualCollisionOperator(erdos.Operator):
    def __init__(self, pose_stream: erdos.ReadStream,
                 prediction_stream: erdos.ReadStream, 
                 finished_indicator_stream: erdos.WriteStream,
                 flags):
        self._flags = flags
        self.pose_msg = deque()
        self.prediction_msg = deque()
        pose_stream.add_callback(self.on_pose_update)
        prediction_stream.add_callback(self.on_prediction_update)
        erdos.add_watermark_callback(
            [pose_stream, prediction_stream], [finished_indicator_stream],
            self.on_watermark)
        self._frame_cnt = 0
        self._data_path = os.path.join(self._flags.data_path, 'custom_virtual_collision')
        if os.path.exists(self._data_path):
            shutil.rmtree(self._data_path)
        os.makedirs(self._data_path)


    @staticmethod
    def connect(pose_stream: erdos.ReadStream,
                 prediction_stream: erdos.ReadStream):
        finished_indicator_stream = erdos.WriteStream()
        return [finished_indicator_stream]
    
    def on_watermark(self, timestamp, finished_indicator_stream):
        if timestamp.is_top:
            return
        pose = self.pose_msg.popleft()
        predictions = self.prediction_msg.popleft()
        with open(os.path.join(self._data_path,'actors.json'), 'r') as f:
            actors = json.load(f)

    
    def on_pose_update(self, msg: erdos.Message):
        game_time = msg.timestamp.coordinates[0]
        self.pose_msg.append((game_time, msg.data))

    def on_prediction_update(self, msg: erdos.Message):
        game_time = msg.timestamp.coordinates[0]
        self.prediction_msg.append((game_time, msg.predictions))
    
def collision_detection(pose, predictions, actors):
    hero_extent_x, hero_extent_y = actors['hero']['extent']['x'], actors['hero']['extent']['y']
    pose_x, pose_y = pose.transform.location.x, pose.transform.location.y


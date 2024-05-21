import erdos
from collections import deque

from pylot.perception.detection.utils import BoundingBox2D
from pylot.perception.messages import ObstaclesMessage
from pylot.perception.detection.obstacle import Obstacle

import time

class DetectionPertrubOperator(erdos.Opertor):
    def __init__(self, obstacles_stream, pertrub_stream,
                 obstacles_pertrub_stream, flags):
        obstacles_stream.add_callback(self.on_obstacles_msg)
        pertrub_stream.add_callback(self.on_pertrub_msg)
        self._obstacles_pertrub_stream = obstacles_pertrub_stream
        self._flags = flags
        self.obs_msg = deque()
        self.perturb_msg = deque()

    @staticmethod
    def connect(obstacles_stream, pertrub_stream):
        obstacles_pertrub_stream = erdos.WriteStream()
        return [obstacles_pertrub_stream]
    
    def destroy(self):
        self._obstacles_pertrub_stream.send(erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))

    def on_obstacles_msg(self, msg):
        self.obs_msg.append(msg)

    def on_pertrub_msg(self, msg):
        self.perturb_msg.append(msg)

    @erdos.profile_method()
    def on_watermark(self, timestamp, obstacles_pertrub_stream):
        st_time = time.time()
        if len(self.obs_msg) == 0 or len(self.perturb_msg) == 0:
            return
        obs_msg = self.obs_msg.popleft()
        perturb_msg = self.perturb_msg.popleft()
        assert obs_msg.timestamp == perturb_msg.timestamp
        pertrub_mode = perturb_msg.mode
        pertrub_ratio = perturb_msg.ratio
        bboxes_pertrub = [Obstacle(
                pertrub_bbox(obs.bounding_box, 
                             pertrub_mode, pertrub_ratio),
                obs.confidence, obs.label, obs.id
            ) for obs in obs_msg.obstacles]
        total_time = (time.time() - st_time) * 1000 + obs_msg.runtime
        obstacles_pertrub_stream.send(ObstaclesMessage(obs_msg.timestamp, bboxes_pertrub, total_time))
        obstacles_pertrub_stream.send(erdos.WatermarkMessage(obs_msg.timestamp))



def pertrub_bbox(bbox, perturb_mode, perturb_ratio) -> BoundingBox2D:
    '''
    pertrub_mode:
        1: increase x range
        2: decrease x range
        3: increase y range
        4: decrease y range
        5: zoom in
        6: zoom out
        7: move left
        8: move right
        9: move up
        10: move down
    '''
    x_min, x_max, y_min, y_max = bbox.x_min, bbox.x_max, bbox.y_min, bbox.y_max
    mid_x = (x_min + x_max) / 2
    mid_y = (y_min + y_max) / 2
    range_x, range_y = x_max - x_min, y_max - y_min
    if perturb_mode == 1:
        range_x *= perturb_ratio
    elif perturb_mode == 2:
        range_x /= perturb_ratio
    elif perturb_mode == 3:
        range_y *= perturb_ratio
    elif perturb_mode == 4:
        range_y /= perturb_ratio
    elif perturb_mode == 5:
        range_x *= perturb_ratio
        range_y *= perturb_ratio
    elif perturb_mode == 6:
        range_x /= perturb_ratio
        range_y /= perturb_ratio
    elif perturb_mode == 7:
        mid_x -= range_x * perturb_ratio
    elif perturb_mode == 8:
        mid_x += range_x * perturb_ratio
    elif perturb_mode == 9:
        mid_y += range_y * perturb_ratio
    elif perturb_mode == 10:
        mid_y -= range_y * perturb_ratio
    else:
        raise ValueError("Invalid perturb mode")
    return BoundingBox2D(mid_x - range_x / 2, mid_x + range_x / 2, mid_y - range_y / 2, mid_y + range_y / 2)
import erdos

from pylot.perception.detection.utils import BoundingBox2D
from pylot.perception.detection.obstacle import Obstacle
from pylot.perception.messages import ObstaclesMessage
import os

import time

class DdetectionFakeOperator(erdos.Operator):
    def __init__(self, obstacle_stream, obstacles_fake_stream, flags):
        obstacle_stream.add_callback(self.on_obstacles_msg, [obstacles_fake_stream])
        self._obstacles_fake_stream = obstacles_fake_stream
        self._flags = flags

    @staticmethod
    def connect(obstacle_stream):
        obstacles_fake_stream = erdos.WriteStream()
        return [obstacles_fake_stream]
    
    def destroy(self):
        self._obstacles_fake_stream.send(
            erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))
        
    def on_obstacles_msg(self, msg: erdos.Message, obstacles_fake_stream: erdos.WriteStream):
        for obs in msg.obstacles:
            
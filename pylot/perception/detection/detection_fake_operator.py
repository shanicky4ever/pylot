import erdos

from pylot.perception.detection.utils import BoundingBox2D
from pylot.perception.detection.obstacle import Obstacle
from pylot.perception.messages import ObstaclesMessage
import os

import time
import copy


class DetectionFakeOperator(erdos.Operator):
    def __init__(self, obstacls_stream, obstacles_fake_stream, flags):
        obstacls_stream.add_callback(self.on_obstacles_msg, [obstacles_fake_stream])
        self._obstacles_fake_stream = obstacles_fake_stream
        self._flags = flags
        # self._msg_cnt = 0
        # self._data_path = os.path.join(self._flags.data_path, 'detector-fake')
        # os.makedirs(self._data_path, exist_ok=True)

    @staticmethod
    def connect(obstacles_stream):
        obstacles_fake_stream = erdos.WriteStream()
        return [obstacles_fake_stream]
    
    def destroy(self):
        self._obstacles_fake_stream.send(
            erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))

    def on_obstacles_msg(self, msg: erdos.Message, obstacles_fake_stream: erdos.WriteStream):
        # assert len(msg.timestamp.coordinates) == 1
        # game_time = msg.timestamp.coordinates[0]
        bboxes_fake = []

        start_time = time.time()

        for obs in msg.obstacles:
            bbox = obs.bounding_box
            x_min, x_max, y_min, y_max = bbox.x_min, bbox.x_max, bbox.y_min, bbox.y_max
            mid_x = (x_min + x_max) / 2
            mid_y = (y_min + y_max) / 2
            range_x, range_y = x_max - x_min, y_max - y_min
            mid_y -= range_y * self._flags.obstacle_error
            new_box = [ int(mid_y - range_y / 2), int(mid_x - range_x / 2),
                        int(mid_y + range_y / 2), int(mid_x + range_x / 2)]
            bboxes_fake.append(Obstacle(
                BoundingBox2D(new_box[1], new_box[3], new_box[0], new_box[2]),
                obs.confidence, obs.label, obs.id
            ))

        runtime = (time.time() - start_time) * 1000
        obstacles_fake_stream.send(
            ObstaclesMessage(msg.timestamp, bboxes_fake, runtime))
        obstacles_fake_stream.send(
            erdos.WatermarkMessage(msg.timestamp))
        
        # if self._flags.log_detector_output_fake:
        #     self._msg_cnt += 1
        #     if self._msg_cnt % self._flags.log_every_nth_message == 0:
        #         msg.frame.annotate_with_bounding_boxes(msg.timestamp, bboxes_fake,
        #                                                None, self._bbox_colors)
        #         msg.frame.save(msg.timestamp.coordinates[0],
        #                        # self._flags.data_path,
        #                        self._data_path,
        #                        'fake-detector-{}'.format(self.config.name))


import json
import os

import erdos

class ObstacleLocationLoggerOperator(erdos.Operator):
    def __init__(self, obstacle_with_location_stream:erdos.ReadStream,
                 finished_indicator_stream: erdos.WriteStream,
                 flags, file_base_name):
        obstacle_with_location_stream.add_callback(self.on_obstacle_with_location_update)
        self._flags = flags
        self._file_base_name = file_base_name
        self._msg_cnt = 0
        self._data_path = os.path.join(self._flags.data_path, file_base_name)
        os.makedirs(self._data_path, exist_ok=True)

    @staticmethod
    def connect(obstacle_with_location_stream:erdos.ReadStream):
        finished_indicator_stream = erdos.WriteStream()
        return [finished_indicator_stream]

    def on_obstacle_with_location_update(self, msg:erdos.Message):
        self._msg_cnt += 1
        if self._msg_cnt % self._flags.log_every_nth_message != 0:
            return
        obstacles_with_location = [obs for obs in msg.obstacles]
        assert len(msg.timestamp.coordinates) == 1
        timestamp = msg.timestamp.coordinates[0]
        file_name = os.path.join(self._data_path,
                                 'obstacle_with_location-{}.json'.format(timestamp))
        with open(file_name, 'w') as outfile:
            json.dump(self._get_log_format(obstacles_with_location), outfile)

    def _get_log_format(self, obstacles_with_location):
        return [{
            'x': obs.transform.location.x,
            'y': obs.transform.location.y,
            'z': obs.transform.location.z,
            'id': obs.id,
            'label': obs.label,
            'confidence': obs.confidence,
        } for obs in obstacles_with_location]
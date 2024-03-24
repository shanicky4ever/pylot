import json
import os

import erdos

class WaypointsLoggerOperator(erdos.Operator):
    def __init__(self, waypoints_stream: erdos.ReadStream, flags, file_base_name):
        waypoints_stream.add_callback(self.on_waypoints_update)
        self._flags = flags
        self._file_base_name = file_base_name
        self._msg_cnt = 0
        self._data_path = os.path.join(self._flags.data_path, file_base_name)
        os.makedirs(self._data_path, exist_ok=True)

    @staticmethod
    def connect(waypoints_stream: erdos.ReadStream):
        finished_indicator_stream = erdos.WriteStream()
        return [finished_indicator_stream]

    def on_waypoints_update(self, msg: erdos.Message):
        self._msg_cnt += 1
        if self._msg_cnt % self._flags.log_every_nth_message != 0:
            return
        assert len(msg.timestamp.coordinates) == 1
        timestamp = msg.timestamp.coordinates[0]
        file_name = os.path.join(self._data_path,
                                 'waypoints-{}.json'.format(timestamp))
        with open(file_name, 'w') as outfile:
            json.dump(self._get_log_format(msg.waypoints), 
                      outfile, indent=4, separators=(',', ': '))
    
    def _get_log_format(self, waypoints):
        return [{
            'x': wp.location.x,
            'y': wp.location.y,
        } for wp in waypoints]
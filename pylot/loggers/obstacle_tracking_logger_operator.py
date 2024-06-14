import pickle
import os
import erdos


class ObstacleTrackingOperator(erdos.Operator):
    def __init__(self, obstacles_tracking_stream: erdos.ReadStream,
                 finished_indicator_stream: erdos.WriteStream, flags,
                 file_base_name):
        obstacles_tracking_stream.add_callback(self.on_obstacles_tracking_update)
        self._flags = flags
        self._file_base_name = file_base_name
        self._msg_cnt = 0
        self._data_path = os.path.join(self._flags.data_path, file_base_name)
        os.makedirs(self._data_path, exist_ok=True)

    @staticmethod
    def connect(obstacles_tracking_stream: erdos.ReadStream):
        finished_indicator_stream = erdos.WriteStream()
        return [finished_indicator_stream]

    def on_obstacles_tracking_update(self, msg: erdos.Message):
        self._msg_cnt += 1
        if self._msg_cnt % self._flags.log_every_nth_message != 0:
            return
        obstacle_trajectories = msg.obstacle_trajectories
        file_name = os.path.join(self._data_path, 'tracking-{}.pb'.format(msg.timestamp))
        with open(file_name, 'wb') as outfile:
            outfile.dump(obstacle_trajectories)

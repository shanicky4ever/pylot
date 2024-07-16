import erdos
from collections import deque

import pylot
from pylot.perception.detection.utils import get_obstacle_locations
from pylot.perception.messages import ObstacleTrajectoriesMessage
import os
import json
from carla import Vehicle

class ObstacleLocationWGThistoryOperator(erdos.Operator):
    def __init__(self, obstacles_stream, depth_stream, pose_stream,
                 GT_history_stream,
                 tracked_obstacles_stream, flags, camera_setup):
        obstacles_stream.add_callback(self.on_obstacles_update)
        depth_stream.add_callback(self.on_depth_update)
        pose_stream.add_callback(self.on_pose_update)
        GT_history_stream.add_callback(self.on_GT_history_update)
        erdos.add_watermark_callback(
            [obstacles_stream, depth_stream, pose_stream, GT_history_stream],
            [tracked_obstacles_stream],
            self.on_watermark
        )
        self._obstacles_msgs = deque()
        self._depth_msgs = deque()
        self._pose_msgs = deque()
        self._GT_history_msgs = deque()
        self._flags = flags
        self._camera_setup = camera_setup
        self._logger = erdos.utils.setup_logging(self.config.name,
                                                 self.config.log_file_name)
        self._csv_logger = erdos.utils.setup_csv_logging(
            self.config.name + '-csv', self.config.csv_log_file_name)
        self.detectID_convert_gtID = {}
        
    @staticmethod
    def connect(obstacles_stream, depth_stream, pose_stream, GT_history_stream):
        tracked_obstacles_stream = erdos.WriteStream()
        return [tracked_obstacles_stream]

    @erdos.profile_method()
    def on_watermark(self, timestamp, tracked_obstacles_stream):
        obstacles_msg = self._obstacles_msgs.popleft()
        depth_msg = self._depth_msgs.popleft()
        vehicle_transform = self._pose_msgs.popleft().data.transform
        GT_history_msg = self._GT_history_msgs.popleft()
        history_traj = GT_history_msg.obstacle_trajectories
        """covert history traj from center to nail"""
        with open(os.path.join(self._flags.data_path, 'actors', f'actors-{timestamp.coordinates[0]}.json'), 'r') as f:
            actor_gt = json.load(f)
        for i, ht in enumerate(history_traj):
            ob_id = str(ht.obstacle.id)
            if ob_id not in actor_gt:
                continue
            for j, traj in enumerate(ht.trajectory):
                history_traj[i].trajectory[j].location.x -= actor_gt[ob_id]['extent']['x']
        """TODO: here we only concern same direct with x extent, may determine the y extent when need"""

        obstacles_with_location = get_obstacle_locations(
            obstacles_msg.obstacles, depth_msg, vehicle_transform,
            self._camera_setup, self._logger)
        for obstacle in obstacles_with_location:
            if (vehicle_transform.location.distance(
                    obstacle.transform.location) > self._flags.dynamic_obstacle_distance_threshold):
                continue
            new_location = \
                vehicle_transform.inverse_transform_locations(
                    [obstacle.transform.location])[0]
            if obstacle.id not in self.detectID_convert_gtID:
                exsit_gtID = [v for k, v in self.detectID_convert_gtID.items()]
                min_dist = 2 * self._flags.dynamic_obstacle_distance_threshold
                for traj in history_traj:
                    if traj.obstacle.id in exsit_gtID:
                        continue
                    ob_dist = new_location.distance(traj.trajectory[-1].location)
                    if ob_dist < min_dist:
                        min_dist = ob_dist
                        self.detectID_convert_gtID[obstacle.id] = traj.obstacle.id
                '''TODO: unable to deal with multiple new obs right now, consider more func'''
            if obstacle.id not in self.detectID_convert_gtID:
                continue

            for i, traj in enumerate(history_traj):
                if self.detectID_convert_gtID[obstacle.id] == traj.obstacle.id:
                    # print(timestamp)
                    # print(traj.trajectory[-1].location)
                    # print(new_location)
                    history_traj[i].trajectory[-1] = pylot.utils.Transform(
                        new_location,
                        obstacle.transform.rotation
                    )

        tracked_obstacles_stream.send(
            ObstacleTrajectoriesMessage(timestamp, history_traj))
        tracked_obstacles_stream.send(erdos.WatermarkMessage(timestamp))

    
    def destroy(self):
        self._logger.warn('destroying {}'.format(self.config.name))

    def on_obstacles_update(self, msg):
        self._logger.debug('@{}: obstacles update'.format(msg.timestamp))
        self._obstacles_msgs.append(msg)

    def on_depth_update(self, msg):
        self._logger.debug('@{}: depth update'.format(msg.timestamp))
        self._depth_msgs.append(msg)

    def on_pose_update(self, msg):
        self._logger.debug('@{}: pose update'.format(msg.timestamp))
        self._pose_msgs.append(msg)

    def on_GT_history_update(self, msg):
        self._logger.debug('@{}: GT_history update'.format(msg.timestamp))
        self._GT_history_msgs.append(msg)
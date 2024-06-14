from json import load
import pathlib
from util.fileutils import load_pickle, load_json
from util.obstacle import abstact_tracking_info, get_init_obstacle, build_obstacle_from_bbox_info, find_obs_in_trajectory, replace_latest_trajectories
from pylot.utils import Transform, Location, Rotation
from pylot.perception.depth_frame import DepthFrame
from pylot.drivers.sensor_setup import DepthCameraSetup, RGBCameraSetup


class PylotAfterPerecptionHandler:
    def __init__(self, profile_data_folder, timestamp):
        self.profile_data_folder = pathlib.Path(profile_data_folder)
        self.timestamp = timestamp
        self._input_frame_data()

    def _input_frame_data(self):
        self.pose = load_json(self.profile_data_folder.joinpath(
            'pose').joinpath(f"pose-{self.timestamp}.json"))
        self.pose = {k: float(v) for k, v in self.pose.items()}
        self.ego_location = Location(self.pose['x'], self.pose['y'], self.pose['z'])
        self.ego_rotation = Rotation(self.pose['roll'], self.pose['pitch'], self.pose['yaw'])
        self.ego_transform = Transform(self.ego_location, self.ego_rotation)

        depth_frame_data = load_pickle(self.profile_data_folder.joinpath("depth").joinpath(f"depth-{self.timestamp}.pkl"))
        depth_camera_setup = DepthCameraSetup('depth_center_camera',
                                              depth_frame_data.shape[1],
                                              depth_frame_data.shape[0],
                                              self.ego_transform)
        self.depth_frame = DepthFrame(depth_frame_data, depth_camera_setup)

        self.camera_setup = RGBCameraSetup('rgb_camera',  depth_frame_data.shape[1], depth_frame_data.shape[0],
                                           self.ego_transform)

        self.trajectories_data = load_json(self.profile_data_folder.joinpath(
            'trajectories').joinpath(f"trajectories-{self.timestamp}.json"))
        self.trajectories = abstact_tracking_info(self.trajectories_data)

        init_obs = get_init_obstacle(self.profile_data_folder, self.timestamp)
        self.obs_in_traj_info = find_obs_in_trajectory(self.trajectories, init_obs,
            depth_frame=self.depth_frame, ego_transform=self.ego_transform)
        # new_trajectories = replace_latest_trajectories(self.trajectories, init_obs,
        #     depth_frame=self.depth_frame, ego_transform=self.ego_transform, obs_in_traj_info=self.obs_in_traj_info)

    def step(self, bbox):
        new_obs = build_obstacle_from_bbox_info(bbox)
        new_trajectories = replace_latest_trajectories(self.trajectories, new_obs,
            depth_frame=self.depth_frame, ego_transform=self.ego_transform, obs_in_traj_info=self.obs_in_traj_info)


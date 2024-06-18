from json import load
import pathlib
from util.fileutils import load_pickle, load_json
from util.obstacle import abstact_tracking_info, get_init_obstacle, build_obstacle_from_bbox_info, find_obs_in_trajectory, replace_latest_trajectories, get_obstacle_location
from util.load_config import load_config
from pylot.utils import Transform, Location, Rotation
from pylot.perception.depth_frame import DepthFrame
from pylot.drivers.sensor_setup import DepthCameraSetup, RGBCameraSetup
from modules.prediction_linear import generate_linear_predicted_trajectories
from pylot.simulation.utils import map_from_opendrive
from modules.planning import planning_generate
from pylot.utils import Pose, Vector3D

class PylotAfterPerecptionHandler:
    def __init__(self, profile_data_folder, timestamp):
        self.profile_data_folder = pathlib.Path(profile_data_folder)
        self.timestamp = timestamp
        self.configs = load_config('config/config.json')
        self._input_frame_data()

    def _input_frame_data(self):
        self.metadata = load_json(self.profile_data_folder.joinpath('meta_data.json'))

        pose_data = load_json(self.profile_data_folder.joinpath('pose').joinpath(f"pose-{self.timestamp}.json"))
        pose_data = {k: float(v) for k, v in pose_data.items()}
        ego_location = Location(pose_data['x'], pose_data['y'], pose_data['z'])
        ego_rotation = Rotation(pose_data['roll'], pose_data['pitch'], pose_data['yaw'])
        velocity = Vector3D(pose_data['velocity_x'], pose_data['velocity_y'], pose_data['velocity_z'])
        self.ego_transform = Transform(ego_location, ego_rotation)
        self.pose = Pose(self.ego_transform, pose_data['forward_speed'], velocity)

        depth_frame_data = load_pickle(self.profile_data_folder.joinpath("depth").joinpath(f"depth-{self.timestamp}.pkl"))
        depth_camera_setup = DepthCameraSetup('depth_center_camera',
                                              depth_frame_data.shape[1],
                                              depth_frame_data.shape[0],
                                              self.ego_transform)
        self.depth_frame = DepthFrame(depth_frame_data, depth_camera_setup)

        self.camera_setup = RGBCameraSetup('rgb_camera', depth_frame_data.shape[1], depth_frame_data.shape[0],
                                           self.ego_transform)

        self.trajectories_data = load_json(self.profile_data_folder.joinpath(
            'trajectories').joinpath(f"trajectories-{self.timestamp}.json"))
        self.trajectories = abstact_tracking_info(self.trajectories_data)

        self.init_obs = get_init_obstacle(self.profile_data_folder, self.timestamp)
        self.obs_in_traj_info = find_obs_in_trajectory(self.trajectories, self.init_obs,
            depth_frame=self.depth_frame, ego_transform=self.ego_transform)
        
        with open(self.profile_data_folder.joinpath('map.xodr')) as f:
            map_data = ''.join(f.readlines())
            self.map = map_from_opendrive(map_data)

        self.goal_location = Location(self.metadata['goal_location']['x'], self.metadata['goal_location']['y'], self.metadata['goal_location']['z'])
        
    def step(self, bbox):
        new_obs = build_obstacle_from_bbox_info(bbox)
        new_trajectories = replace_latest_trajectories(self.trajectories, new_obs,
            depth_frame=self.depth_frame, ego_transform=self.ego_transform, obs_in_traj_info=self.obs_in_traj_info)
        predicted_trajectories = generate_linear_predicted_trajectories(new_trajectories)
        planning_waypoints = planning_generate(self.ego_transform, self.pose, predicted_trajectories, self.map, self.goal_location, self.configs, self.timestamp)
        
    def get_bbox_state(self):
        obs_locations = [get_obstacle_location(ob, self.depth_frame, self.ego_transform.location) for ob in self.init_obs]
        dists = [ob.transform.location.distance(self.ego_transform.location) for ob in obs_locations]
        return obs_locations
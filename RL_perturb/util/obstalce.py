from collections import namedtuple
from typing import Deque, Dict, List
from pylot.perception.detection.utils import BoundingBox2D, get_obstacle_locations
from pylot.perception.detection.obstacle import Obstacle
from .fileutils import load_json
from pylot.utils import Vector2D, Transform, Rotation, Location
import numpy as np
import re


def get_init_obstacle(base_dir, timestamp):
    bboxes = load_json(base_dir.joinpath("bboxes").joinpath(f"bboxes-{timestamp}.json"))
    return build_obstacle_from_bbox_info(bboxes)


def build_obstacle_from_bbox_info(bboxes: List):
    obs = []
    for bbox in bboxes:
        bb = bbox['bounding_box']
        x_min, y_min, x_max, y_max = bb[0][0], bb[0][1], bb[1][0], bb[1][1]
        ob_bb = BoundingBox2D(x_min, x_max, y_min, y_max)
        ob = Obstacle(bounding_box=ob_bb, confidence=1.0, id=bbox['id'], label=bbox['label'])
        obs.append(ob)
    return obs


def replace_latest_trajectories(trajectories, obstacles: List, depth_frame, ego_transform: Transform, obs_in_traj_info):
    for ob in obstacles:
        if ob.id not in obs_in_traj_info:
            continue
        ob_with_transform = get_obstacle_location(ob, depth_frame, ego_transform.location)
        new_location = ego_transform.inverse_transform_locations(
            [ob_with_transform.transform.location])[0]
        new_location.x += obs_in_traj_info[ob.id]['x']
        new_location.y += obs_in_traj_info[ob.id]['y']
        new_location.z += obs_in_traj_info[ob.id]['z']
        trajectories[obs_in_traj_info[ob.id]['traj']][-1].location =\
            Location(new_location.x, new_location.y, new_location.z)
    return trajectories




    obstacle_ids = [o.id for o in obstacles]
    for h in history:
        if h.obstacle.id == obstacle_ids:
            obs_with_transform = get_obstacle_location(h.obstacle, depth_frame, ego_transform.location)
            new_location = ego_transform.inverse_transform_locations(
                [obs_with_transform.trasnform.location])[0]
            print(new_location)
            # h.cur_obstacle_trajectory[-1] = Transform(new_location, Rotation())
    return history

def find_obs_in_trajectory(trajectories: Dict, obstacles: List, depth_frame, ego_transform: Transform):
    obs_in_traj_info = {}
    for ob in obstacles:
        obs_with_transform = get_obstacle_location(ob, depth_frame, ego_transform.location)
        new_location = ego_transform.inverse_transform_locations(
                [obs_with_transform.transform.location])[0]
        closest_trans_id, closest_dist = _find_closest_trans(trajectories, new_location)
        if closest_trans_id is not None:
            obs_in_traj_info[ob.id] = {
                'traj': closest_trans_id,
                'x': closest_dist[0],
                'y': closest_dist[1],
                'z': closest_dist[2]
            }
    return obs_in_traj_info


def _find_closest_trans(trajectories: Dict, location):
    min_dist = np.infty
    closest_id = -1
    dist_x, dist_y = 0, 0
    for traj_id, traj_value in trajectories.items():
        last_traj = traj_value[-1].location
        dist = ((location.x - last_traj.x)**2 + (location.y - last_traj.y)**2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            closest_id = traj_id
            dist_x = last_traj.x - location.x
            dist_y = last_traj.y - location.y
            dist_z = last_traj.z - location.z
    if min_dist < 2.0:
        return closest_id, (dist_x, dist_y, dist_z)
    else:
        return None, None

def get_obstacle_location(obstacle, depth_frame, ego_location):
    center_point = obstacle.bounding_box_2D.get_center_point()
    sample_points = []
    for delta_x in range(-30, 30, 5):
        for delta_y in range(-30, 30, 5):
            sample_point = center_point + Vector2D(
                delta_x, delta_y)
            if obstacle.bounding_box.is_within(sample_point):
                sample_points.append(sample_point)
    locations = depth_frame.get_pixel_locations(sample_points)
    # Choose the closest from the locations of the sampled points.
    min_distance = np.infty
    closest_location = None
    for location in locations:
        dist = location.distance(ego_location)
        if dist < min_distance:
            min_distance = dist
            closest_location = location
    obstacle.transform = Transform(closest_location, Rotation())
    return obstacle


def abstact_tracking_info(track_data):
    info = {}
    for ob_track_data in track_data:
        ob_id = int(re.search(r'id:\s*(\d+)', ob_track_data).group(1))
        trajectory_pattern = re.findall(
            r'Transform\(location:\s*Location\(x=([-\d.]+),\s*y=([-\d.]+),\s*z=([-\d.]+)\),\s*rotation:\s*Rotation\(pitch=([-\d.]+),\s*yaw=([-\d.]+),\s*roll=([-\d.]+)\)\)', ob_track_data)
        trajectory = [Transform(Location(float(x), float(y), float(z)), Rotation(
            float(p), float(yaw), float(r))) for x, y, z, p, yaw, r in trajectory_pattern]
        info[ob_id] = trajectory
    return info

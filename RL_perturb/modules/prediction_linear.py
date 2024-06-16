from pylot.utils import Location, Rotation, Transform
import numpy as np
from pylot.prediction.obstacle_prediction import ObstaclePrediction

def generate_linear_predicted_trajectories(history_tracking, prediction_num_past_steps=10, prediction_num_future_steps=10):
    obstacle_predictions_list = []
    nearby_obstacle_trajectories, nearby_obstacles_ego_transforms = \
        get_nearby_obstacles_info(history_tracking, radius=50)
    num_predictions = len(nearby_obstacle_trajectories)
    for idx in range(len(nearby_obstacle_trajectories)):
        obstacle_trajectory = nearby_obstacle_trajectories[idx]
        # Time step matrices used in regression.
        num_steps = min(prediction_num_past_steps,
                        len(obstacle_trajectory.trajectory))
        ts = np.zeros((num_steps, 2))
        future_ts = np.zeros((prediction_num_future_steps, 2))
        for t in range(num_steps):
            ts[t][0] = -t
            ts[t][1] = 1
        for i in range(prediction_num_future_steps):
            future_ts[i][0] = i + 1
            future_ts[i][1] = 1

        xy = np.zeros((num_steps, 2))
        for t in range(num_steps):
            # t-th most recent step
            transform = obstacle_trajectory.trajectory[-(t + 1)]
            xy[t][0] = transform.location.x
            xy[t][1] = transform.location.y
        linear_model_params = np.linalg.lstsq(ts, xy, rcond=None)[0]
        # Predict future steps and convert to list of locations.
        predict_array = np.matmul(future_ts, linear_model_params)
        predictions = []
        for t in range(prediction_num_future_steps):
            # Linear prediction does not predict vehicle orientation, so we
            # use our estimated orientation of the vehicle at its latest
            # location.
            predictions.append(
                Transform(location=Location(x=predict_array[t][0],
                                            y=predict_array[t][1]),rotation=nearby_obstacles_ego_transforms[idx].rotation))
        obstacle_predictions_list.append(
            ObstaclePrediction(obstacle_trajectory,
                obstacle_trajectory.obstacle.transform, 1.0,
                predictions))
    return obstacle_predictions_list

def get_nearby_obstacles_info(obstacle_trajectories, radius=50, filter_fn=None):
    if filter_fn:
        filtered_trajectories = list(
            filter(filter_fn, obstacle_trajectories))
    else:
        filtered_trajectories = obstacle_trajectories
    distances = [
        v.trajectory[-1].get_angle_and_magnitude(Location())[1]
        for k, v in filtered_trajectories.items()
    ]
    sorted_trajectories = [
        filtered_trajectories[v] for v, d in sorted(zip(filtered_trajectories, distances),
                                key=lambda pair: pair[1]) if d <= radius
    ]
    if not sorted_trajectories:
        return sorted_trajectories, []
    nearby_obstacles_ego_locations = np.stack([t.trajectory[-1] for t in sorted_trajectories])
    nearby_obstacles_ego_transforms = []
    for i in range(len(sorted_trajectories)):
        cur_obstacle_angle = sorted_trajectories[
            i].estimate_obstacle_orientation()
        nearby_obstacles_ego_transforms.append(
            Transform(location=nearby_obstacles_ego_locations[i].location, rotation=Rotation(yaw=cur_obstacle_angle)))
    return sorted_trajectories, nearby_obstacles_ego_transforms



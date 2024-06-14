

def generate_linear_predicted_trajectories(history_tracking):
    obstacle_predictions_list = []
    nearby_obstacle_trajectories, nearby_obstacles_ego_transforms = \
        history_tracking.get_nearby_obstacles_info(10)

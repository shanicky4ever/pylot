from pylot.planning.utils import BehaviorPlannerState
from collections import deque
from pylot.utils import RoadOption
from pylot.planning.waypoints import Waypoints
from pylot.planning.rrt_star.rrt_star_planner import RRTStarPlanner
from pylot.planning.world import World
import erdos


def planning_generate(ego_transform, pose, prediction, map, goal_location, configs, timestamp):
    plan_logger = erdos.utils.setup_logging('planning', 'RLlog.log')
    world = World(flags=configs, logger=plan_logger)
    world.update(timestamp=timestamp,
                 pose=pose,
                 obstacle_predictions=prediction,
                 static_obstacles=[],
                 hd_map=map)
    planner = RRTStarPlanner(world, configs, plan_logger)
    route_after_behaviour_plan = behaviour_generate(ego_transform, pose, map, goal_location, timestamp)
    world.update_waypoints(route_after_behaviour_plan.waypoints[-1].location, route_after_behaviour_plan)
    (speed_factor, _, _, speed_factor_tl, speed_factor_stop) = world.stop_for_agents(timestamp)
    output_wps = planner.run(timestamp, None)
    speed_factor = min(speed_factor_stop, speed_factor_tl)
    output_wps.apply_speed_factor(speed_factor)
    return output_wps


'''
Use Follow Way points to all scen, since no record on previous behavior. TO BE UPDATED later.
'''

def behaviour_generate(ego_transform, pose, map, goal_location, timestamp):
    ego_info = EgoInfo()
    ego_info.update(pose, timestamp)
    state = BehaviorPlannerState.FOLLOW_WAYPOINTS
    # TODO here if we have previous behavior record, we can use it to generate the behavior
    waypoints = map.compute_waypoints(ego_transform.location, goal_location)
    road_options = deque([
        RoadOption.LANE_FOLLOW
        for _ in range(len(waypoints))
    ])
    ego_traj = Waypoints(waypoints, road_options=road_options)
    return ego_traj


class EgoInfo(object):
    def __init__(self):
        self.last_time_moving = 0
        self.last_time_stopped = 0
        self.current_time = 0

    def update(self, pose, timestamp):
        self.current_time = timestamp
        if pose.forward_speed >= 0.7:
            self.last_time_moving = self.current_time
        else:
            self.last_time_stopped = self.current_time

import signal

from absl import app, flags

import erdos

import pylot.flags
import pylot.component_creator  # noqa: I100
import pylot.operator_creator
import pylot.utils
from pylot.drivers.sensor_setup import DepthCameraSetup, RGBCameraSetup, \
    SegmentedCameraSetup
from pylot.simulation.utils import get_world, set_asynchronous_mode

from datetime import datetime
import os
import shutil

#flags.DEFINE_list('goal_location', '234, 59, 39', 'Ego-vehicle goal location')
flags.DEFINE_bool('log_rgb_camera', False,
                  'True to enable center camera RGB logging')
flags.DEFINE_bool('log_segmented_camera', False,
                  'True to enable center segmented camera logging')
flags.DEFINE_bool('log_left_right_cameras', False,
                  'Control whether we log left and right cameras.')
flags.DEFINE_bool('log_depth_camera', False,
                  'True to enable depth camera logging')
flags.DEFINE_bool('log_gnss', False, 'Enable logging of GNSS measurements.')
flags.DEFINE_bool('log_pose', False, 'Enable logging of pose measurements.')
flags.DEFINE_bool('log_imu', False, 'Enable logging of IMU measurements.')
flags.DEFINE_bool('log_lidar', False, 'True to enable lidar logging')
flags.DEFINE_bool('log_obstacles', False,
                  'True to enable obstacle bounding box logging')
flags.DEFINE_bool(
    'log_traffic_lights', False,
    'True to enable traffic lights bounding box and camera logging')
flags.DEFINE_bool('log_multiple_object_tracker', False,
                  'True to enable logging in the MOT format')
flags.DEFINE_bool('log_trajectories', False,
                  'True to enable trajectory logging')
flags.DEFINE_bool('log_chauffeur', False,
                  'True to log data in ChauffeurNet style.')
flags.DEFINE_bool('log_top_down_segmentation', False,
                  'True to enable logging of top down segmentation')

flags.DEFINE_bool('log_obstacles_fake', False,
                  'True to enable obstacle bounding box logging')
flags.DEFINE_bool('log_predictions', False,
                  'True to enable prediction logging')
flags.DEFINE_bool('log_predictions_fake', False,
                  'True to enable prediction logging')
flags.DEFINE_bool('log_waypoints', False,
                  'True to enable waypoints logging')
flags.DEFINE_bool('log_waypoints_fake', False,
                  'True to enable waypoints logging')
flags.DEFINE_bool('log_obstacle_with_location', False,
                  'True to enable obstacle with location logging')
flags.DEFINE_bool('log_obstacle_history', False,
                  'True to enable obstacle history logging')


FLAGS = flags.FLAGS

# The location of the center camera relative to the ego-vehicle.
CENTER_CAMERA_LOCATION = pylot.utils.Location(1.3, 0.0, 1.8)




def driver():
    transform = pylot.utils.Transform(CENTER_CAMERA_LOCATION,
                                      pylot.utils.Rotation(pitch=-15))
    streams_to_send_top_on = []
    control_loop_stream = erdos.LoopStream()
    time_to_decision_loop_stream = erdos.LoopStream()
    if FLAGS.simulator_mode == 'pseudo-asynchronous':
        release_sensor_stream = erdos.LoopStream()
        pipeline_finish_notify_stream = erdos.LoopStream()
    else:
        release_sensor_stream = erdos.IngestStream()
        pipeline_finish_notify_stream = erdos.IngestStream()
    notify_streams = []

    # Create operator that bridges between pipeline and the simulator.
    (
        pose_stream,
        pose_stream_for_control,
        ground_traffic_lights_stream,
        ground_obstacles_stream,
        ground_speed_limit_signs_stream,
        ground_stop_signs_stream,
        vehicle_id_stream,
        open_drive_stream,
        global_trajectory_stream,
    ) = pylot.operator_creator.add_simulator_bridge(
        control_loop_stream,
        release_sensor_stream,
        pipeline_finish_notify_stream,
    )

    # Add sensors.
    center_camera_setup = RGBCameraSetup('center_camera',
                                         FLAGS.camera_image_width,
                                         FLAGS.camera_image_height, transform,
                                         FLAGS.camera_fov)
    (center_camera_stream, notify_rgb_stream) = \
        pylot.operator_creator.add_camera_driver(
            center_camera_setup, vehicle_id_stream, release_sensor_stream)
    notify_streams.append(notify_rgb_stream)
    if pylot.flags.must_add_depth_camera_sensor():
        depth_camera_setup = DepthCameraSetup('depth_center_camera',
                                              FLAGS.camera_image_width,
                                              FLAGS.camera_image_height,
                                              transform, FLAGS.camera_fov)
        (depth_camera_stream, notify_depth_stream) = \
            pylot.operator_creator.add_camera_driver(
                depth_camera_setup, vehicle_id_stream, release_sensor_stream)
    else:
        depth_camera_stream = None
    if pylot.flags.must_add_segmented_camera_sensor():
        segmented_camera_setup = SegmentedCameraSetup(
            'segmented_center_camera', FLAGS.camera_image_width,
            FLAGS.camera_image_height, transform, FLAGS.camera_fov)
        (ground_segmented_stream, notify_segmented_stream) = \
            pylot.operator_creator.add_camera_driver(
                segmented_camera_setup, vehicle_id_stream,
                release_sensor_stream)
    else:
        ground_segmented_stream = None

    if pylot.flags.must_add_lidar_sensor():
        # Place LiDAR sensor in the same location as the center camera.
        (point_cloud_stream, notify_lidar_stream,
         lidar_setup) = pylot.operator_creator.add_lidar(
             transform, vehicle_id_stream, release_sensor_stream)
        if FLAGS.log_lidar:
            pylot.operator_creator.add_lidar_logging(point_cloud_stream)
    else:
        point_cloud_stream = None
        lidar_setup = None

    if FLAGS.obstacle_location_finder_sensor == 'lidar':
        depth_stream = point_cloud_stream
        # Camera sensors are slower than the lidar sensor.
        notify_streams.append(notify_lidar_stream)
    elif FLAGS.obstacle_location_finder_sensor == 'depth_camera':
        depth_stream = depth_camera_stream
        notify_streams.append(notify_depth_stream)
    elif FLAGS.obstacle_location_finder_sensor == 'depth_stereo':
        (depth_stream, notify_left_camera_stream,
         notify_right_camera_stream) = pylot.component_creator.add_depth(
             transform, vehicle_id_stream, center_camera_setup,
             depth_camera_stream, release_sensor_stream)
        notify_streams.append(notify_left_camera_stream)
        notify_streams.append(notify_right_camera_stream)
    else:
        raise ValueError(
            'Unknown --obstacle_location_finder_sensor value {}'.format(
                FLAGS.obstacle_location_finder_sensor))
    
    if FLAGS.log_rgb_camera:
        pylot.operator_creator.add_camera_logging(
            center_camera_stream, 'center_camera_logger_operator', 'center')

    if FLAGS.log_segmented_camera:
        pylot.operator_creator.add_camera_logging(
            segmented_stream, 'center_segmented_camera_logger_operator',
            'segmented')

    if FLAGS.log_depth_camera:
        pylot.operator_creator.add_camera_logging(
            depth_camera_stream, 'depth_camera_logger_operator', 'depth')

    imu_stream = None
    if pylot.flags.must_add_imu_sensor():
        (imu_stream, _) = pylot.operator_creator.add_imu(
            pylot.utils.Transform(location=pylot.utils.Location(),
                                  rotation=pylot.utils.Rotation()),
            vehicle_id_stream)
        if FLAGS.log_imu:
            pylot.operator_creator.add_imu_logging(imu_stream)

    gnss_stream = None
    if pylot.flags.must_add_gnss_sensor():
        (gnss_stream, _) = pylot.operator_creator.add_gnss(
            pylot.utils.Transform(location=pylot.utils.Location(),
                                  rotation=pylot.utils.Rotation()),
            vehicle_id_stream)
        if FLAGS.log_gnss:
             pylot.operator_creator.add_gnss_logging(gnss_stream)

    if FLAGS.localization:
        pose_stream = pylot.operator_creator.add_localization(
            imu_stream, gnss_stream, pose_stream)
        if FLAGS.log_pose:
            pylot.operator_creator.add_pose_logging(pose_stream)

    obstacles_stream, perfect_obstacles_stream = \
        pylot.component_creator.add_obstacle_detection(
            center_camera_stream, center_camera_setup, pose_stream,
            depth_stream, depth_camera_stream, ground_segmented_stream,
            ground_obstacles_stream, ground_speed_limit_signs_stream,
            ground_stop_signs_stream, time_to_decision_loop_stream)
    if FLAGS.log_obstacles:
        pylot.operator_creator.add_bounding_box_logging(
            obstacles_stream, 'bboxes')
    if FLAGS.log_multiple_object_tracker:
        pylot.operator_creator.add_multiple_object_tracker_logging(
            obstacles_stream)
        
    if FLAGS.custom_obstacle_detection_eval:
        pylot.operator_creator.add_custom_obstacle_detection_eval(obstacles_stream, perfect_obstacles_stream)

    tl_transform = pylot.utils.Transform(CENTER_CAMERA_LOCATION,
                                         pylot.utils.Rotation())
    traffic_lights_stream, tl_camera_stream = \
        pylot.component_creator.add_traffic_light_detection(
            tl_transform, vehicle_id_stream, release_sensor_stream,
            pose_stream, depth_stream, ground_traffic_lights_stream,
            time_to_decision_loop_stream)
    if FLAGS.log_traffic_lights:
        pylot.operator_creator.add_bounding_box_logging(
            traffic_lights_stream, 'tl-bboxes')

    lane_detection_stream = pylot.component_creator.add_lane_detection(
        center_camera_stream, pose_stream, open_drive_stream)
    if lane_detection_stream is None:
        lane_detection_stream = erdos.IngestStream()
        streams_to_send_top_on.append(lane_detection_stream)

    obstacles_tracking_stream = pylot.component_creator.add_obstacle_tracking(
        center_camera_stream, center_camera_setup, obstacles_stream,
        depth_stream, vehicle_id_stream, pose_stream, ground_obstacles_stream,
        time_to_decision_loop_stream)
    
    if FLAGS.log_obstacle_with_location:
        obs_with_loc_stream = pylot.component_creator.add_obstacle_with_location(
            obstacles_stream, depth_stream, pose_stream, center_camera_setup)
        pylot.operator_creator.add_obstacle_with_location_logging(
            obs_with_loc_stream, 'obstacles_with_location')
    
    if FLAGS.log_trajectories:
        pylot.operator_creator.add_trajectory_logging(
            obstacles_tracking_stream)

    segmented_stream = pylot.component_creator.add_segmentation(
        center_camera_stream, ground_segmented_stream)

    if FLAGS.fusion:
        pylot.operator_creator.add_fusion(pose_stream, obstacles_stream,
                                          depth_stream,
                                          ground_obstacles_stream)

    prediction_stream, prediction_camera_stream, notify_prediction_stream = \
        pylot.component_creator.add_prediction(
            obstacles_tracking_stream, vehicle_id_stream,
            time_to_decision_loop_stream, transform, release_sensor_stream,
            pose_stream, point_cloud_stream, lidar_setup)
    if prediction_stream is None:
        prediction_stream = obstacles_stream
    if notify_prediction_stream:
        notify_streams.append(notify_prediction_stream)
    
    if FLAGS.log_predictions:
        pylot.operator_creator.add_prediction_logging(prediction_stream,
                                                      'predictions')

    goal_location = pylot.utils.Location(float(FLAGS.goal_location[0]),
                                         float(FLAGS.goal_location[1]),
                                         float(FLAGS.goal_location[2]))
    waypoints_stream = pylot.component_creator.add_planning(
        goal_location, pose_stream, prediction_stream, traffic_lights_stream,
        lane_detection_stream, open_drive_stream, global_trajectory_stream,
        time_to_decision_loop_stream)
    if FLAGS.log_waypoints:
        pylot.operator_creator.add_waypoints_logging(waypoints_stream,
                                                     'waypoint')

    if FLAGS.simulator_mode == "pseudo-asynchronous":
        # Add a synchronizer in the pseudo-asynchronous mode.
        (
            waypoints_stream_for_control,
            pose_stream_for_control,
            sensor_ready_stream,
            _pipeline_finish_notify_stream,
        ) = pylot.operator_creator.add_planning_pose_synchronizer(
            waypoints_stream, pose_stream_for_control, pose_stream,
            *notify_streams)
        release_sensor_stream.set(sensor_ready_stream)
        pipeline_finish_notify_stream.set(_pipeline_finish_notify_stream)
    else:
        waypoints_stream_for_control = waypoints_stream
        pose_stream_for_control = pose_stream

    control_stream = pylot.component_creator.add_control(
        pose_stream_for_control, waypoints_stream_for_control,
        vehicle_id_stream, perfect_obstacles_stream)
    control_loop_stream.set(control_stream)

    pylot.component_creator.add_evaluation(vehicle_id_stream, pose_stream,
                                           imu_stream)

    time_to_decision_stream = pylot.operator_creator.add_time_to_decision(
        pose_stream, obstacles_stream)
    time_to_decision_loop_stream.set(time_to_decision_stream)

    control_display_stream = None
    if pylot.flags.must_visualize():
        control_display_stream, ingest_streams = \
            pylot.operator_creator.add_visualizer(
                pose_stream, center_camera_stream, tl_camera_stream,
                prediction_camera_stream, depth_camera_stream,
                point_cloud_stream, segmented_stream, imu_stream,
                obstacles_stream, traffic_lights_stream,
                obstacles_tracking_stream, lane_detection_stream,
                prediction_stream, waypoints_stream, control_stream)
        streams_to_send_top_on += ingest_streams

    node_handle = erdos.run_async('pylot.dot')

    for stream in streams_to_send_top_on:
        stream.send(erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))
    # If we did not use the pseudo-asynchronous mode, ask the sensors to
    # release their readings whenever.
    if FLAGS.simulator_mode != "pseudo-asynchronous":
        release_sensor_stream.send(
            erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))
        pipeline_finish_notify_stream.send(
            erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))

    return node_handle, control_display_stream


def shutdown_pylot(node_handle, client, world):
    if node_handle:
        node_handle.shutdown()
    else:
        print('WARNING: The Pylot dataflow failed to initialize.')
    if FLAGS.simulation_recording_file is not None:
        client.stop_recorder()
    set_asynchronous_mode(world)
    if pylot.flags.must_visualize():
        import pygame
        pygame.quit()


def shutdown(sig, frame):
    raise KeyboardInterrupt


def main(args):
    # current_time = datetime.now().strftime("%m-%d-%H-%M-%S")
    # FLAGS.data_path = os.path.join(FLAGS.data_path,current_time)
    if os.path.exists(FLAGS.data_path):
        shutil.rmtree(FLAGS.data_path)
    os.makedirs(FLAGS.data_path)
    # Connect an instance to the simulator to make sure that we can turn the
    # synchronous mode off after the script finishes running.
    client, world = get_world(FLAGS.simulator_host, FLAGS.simulator_port,
                              FLAGS.simulator_timeout)
    try:
        if FLAGS.simulation_recording_file is not None:
            client.start_recorder(FLAGS.simulation_recording_file)
        node_handle, control_display_stream = driver()
        signal.signal(signal.SIGINT, shutdown)
        if pylot.flags.must_visualize():
            pylot.utils.run_visualizer_control_loop(control_display_stream)
        node_handle.wait()
    except KeyboardInterrupt:
        shutdown_pylot(node_handle, client, world)
    except Exception:
        shutdown_pylot(node_handle, client, world)
        raise


if __name__ == '__main__':
    app.run(main)

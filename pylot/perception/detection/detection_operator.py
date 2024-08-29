"""Implements an operator that detects obstacles."""
import time

import erdos

import numpy as np

from pylot.perception.detection.obstacle import Obstacle
from pylot.perception.detection.utils import BoundingBox2D, \
    OBSTACLE_LABELS, load_coco_bbox_colors, load_coco_labels
from pylot.perception.messages import ObstaclesMessage

import tensorflow as tf
import os


class DetectionOperator(erdos.Operator):
    """Detects obstacles using a TensorFlow model.

    The operator receives frames on a camera stream, and runs a model for each
    frame.

    Args:
        camera_stream (:py:class:`erdos.ReadStream`): The stream on which
            camera frames are received.
        obstacles_stream (:py:class:`erdos.WriteStream`): Stream on which the
            operator sends
            :py:class:`~pylot.perception.messages.ObstaclesMessage` messages.
        model_path(:obj:`str`): Path to the model pb file.
        flags (absl.flags): Object to be used to access absl flags.
    """

    def __init__(self, camera_stream: erdos.ReadStream,
                 time_to_decision_stream: erdos.ReadStream,
                 obstacles_stream: erdos.WriteStream, model_path: str, flags):
        camera_stream.add_callback(self.on_msg_camera_stream,
                                   [obstacles_stream])
        time_to_decision_stream.add_callback(self.on_time_to_decision_update)
        self._flags = flags
        self._logger = erdos.utils.setup_logging(self.config.name,
                                                 self.config.log_file_name)
        self._obstacles_stream = obstacles_stream

        # pylot.utils.set_tf_loglevel(logging.ERROR)
        # Only sets memory growth for flagged GPU
        self._logger.info(f"GPU is {self._flags.obstacle_detection_gpu_index}")
        physical_devices = tf.config.experimental.list_physical_devices('GPU')
        # tf.config.experimental.set_visible_devices(
        #     [physical_devices[self._flags.obstacle_detection_gpu_index]],
        #     'GPU')
        self._logger.info(f"gpu device{physical_devices[self._flags.obstacle_detection_gpu_index]}")
        logical_devices = tf.config.list_logical_devices()
        for device in logical_devices:
            self._logger.info(f'Logical device {device.name} is on physical device {device.device_type}')
        # tf.config.experimental.set_memory_growth(
        #     physical_devices[self._flags.obstacle_detection_gpu_index], True)
        # tf.config.threading.set_intra_op_parallelism_threads(8)
        # Load the model from the saved_model format file.
        self._model = tf.saved_model.load(model_path)
        self._logger.info(f'{physical_devices[self._flags.obstacle_detection_gpu_index]}')
        logical_devices = tf.config.list_logical_devices()
        for device in logical_devices:
            self._logger.info(f'Logical device {device.name} is on physical device {device.device_type}')

        self._coco_labels = load_coco_labels(self._flags.path_coco_labels)
        self._bbox_colors = load_coco_bbox_colors(self._coco_labels)
        # Unique bounding box id. Incremented for each bounding box.
        self._unique_id = 0
        if self._flags.log_detector_output:
            self._msg_cnt = 0
            self._data_path = os.path.join(self._flags.data_path, 'detector')
            os.makedirs(self._data_path, exist_ok=True)
        # Serve some junk image to load up the model.
        self.__run_model(np.zeros((108, 192, 3), dtype='uint8'))


    @staticmethod
    def connect(camera_stream: erdos.ReadStream,
                time_to_decision_stream: erdos.ReadStream):
        """Connects the operator to other streams.

        Args:
            camera_stream (:py:class:`erdos.ReadStream`): The stream on which
                camera frames are received.

        Returns:
            :py:class:`erdos.WriteStream`: Stream on which the operator sends
            :py:class:`~pylot.perception.messages.ObstaclesMessage` messages.
        """
        obstacles_stream = erdos.WriteStream()
        return [obstacles_stream]

    def destroy(self):
        self._logger.warn('destroying {}'.format(self.config.name))
        # Sending top watermark because the operator is not flowing
        # watermarks.
        self._obstacles_stream.send(
            erdos.WatermarkMessage(erdos.Timestamp(is_top=True)))

    def on_time_to_decision_update(self, msg: erdos.Message):
        self._logger.debug('@{}: {} received ttd update {}'.format(
            msg.timestamp, self.config.name, msg))

    @erdos.profile_method()
    def on_msg_camera_stream(self, msg: erdos.Message,
                             obstacles_stream: erdos.WriteStream):
        """Invoked whenever a frame message is received on the stream.

        Args:
            msg (:py:class:`~pylot.perception.messages.FrameMessage`): Message
                received.
            obstacles_stream (:py:class:`erdos.WriteStream`): Stream on which
                the operator sends
                :py:class:`~pylot.perception.messages.ObstaclesMessage`
                messages.
        """
        self._logger.debug('@{}: {} received message'.format(
            msg.timestamp, self.config.name))
        start_time = time.time()
        # The models expect BGR images.
        assert msg.frame.encoding == 'BGR', 'Expects BGR frames'
        num_detections, res_boxes, res_scores, res_classes = self.__run_model(
            msg.frame.frame)
        obstacles = []
        for i in range(0, num_detections):
            if res_classes[i] in self._coco_labels:
                if (res_scores[i] >=
                        self._flags.obstacle_detection_min_score_threshold):
                    if (self._coco_labels[res_classes[i]] in OBSTACLE_LABELS):
                        obstacles.append(
                            Obstacle(BoundingBox2D(
                                int(res_boxes[i][1] *
                                    msg.frame.camera_setup.width),
                                int(res_boxes[i][3] *
                                    msg.frame.camera_setup.width),
                                int(res_boxes[i][0] *
                                    msg.frame.camera_setup.height),
                                int(res_boxes[i][2] *
                                    msg.frame.camera_setup.height)),
                                res_scores[i],
                                self._coco_labels[res_classes[i]],
                                id=self._unique_id))
                        self._unique_id += 1
                    else:
                        self._logger.warning(
                            'Ignoring non essential detection {}'.format(
                                self._coco_labels[res_classes[i]]))
            else:
                self._logger.warning('Filtering unknown class: {}'.format(
                    res_classes[i]))

        self._logger.debug('@{}: {} obstacles: {}'.format(
            msg.timestamp, self.config.name, obstacles))

        # Get runtime in ms.
        runtime = (time.time() - start_time) * 1000
        # Send out obstacles.
        obstacles_stream.send(
            ObstaclesMessage(msg.timestamp, obstacles, runtime))
        obstacles_stream.send(erdos.WatermarkMessage(msg.timestamp))

        if self._flags.log_detector_output:
            self._msg_cnt += 1
            if self._msg_cnt % self._flags.log_every_nth_message == 0:
                msg.frame.annotate_with_bounding_boxes(msg.timestamp, obstacles,
                                                       None, self._bbox_colors)
                msg.frame.save(msg.timestamp.coordinates[0], self._data_path,
                               'detector-{}'.format(self.config.name))

    def __run_model(self, image_np):
        # Expand dimensions since the model expects images to have
        # shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image_np, axis=0)

        infer = self._model.signatures['serving_default']
        result = infer(tf.convert_to_tensor(value=image_np_expanded))

        for key, value in result.items():
            self._logger.info(f'{key} is on device: {value.device}')

        boxes = result['boxes']
        scores = result['scores']
        classes = result['classes']
        num_detections = result['detections']

        num_detections = int(num_detections[0])
        res_classes = [int(cls) for cls in classes[0][:num_detections]]
        res_boxes = boxes[0][:num_detections]
        res_scores = scores[0][:num_detections]
        return num_detections, res_boxes, res_scores, res_classes

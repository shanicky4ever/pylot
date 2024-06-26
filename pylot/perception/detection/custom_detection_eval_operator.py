import erdos
from pycocotools.cocoeval import COCOeval
from pycocotools.coco import COCO
from collections import deque
import json
import os

class CustomDetectionEvalOperator(erdos.Operator):
    def __init__(self, obstacles_stream: erdos.ReadStream, 
                 perfect_obstacles_stream: erdos.ReadStream,
                 finished_indicator_stream: erdos.WriteStream,
                 flags):
        self._flags = flags
        self.obstacle_perception = deque()
        self.obstacle_perfect = deque()
        obstacles_stream.add_callback(self.on_perception)
        perfect_obstacles_stream.add_callback(self.on_perfect)
        erdos.add_watermark_callback([obstacles_stream, perfect_obstacles_stream], 
        [finished_indicator_stream],
        self.on_watermark)
        self._frame_cnt = 0
        # self.labels = {}
        self._data_path = os.path.join(self._flags.data_path, 'detect_eval')
        os.makedirs(self._data_path, exist_ok=True)
        self.keys=['AP','AP50','AP75','AP_small','AP_medium','AP_large','AR1','AR10','AR100','AR_small','AR_medium','AR_large']

    @staticmethod
    def connect(obstacles_stream: erdos.ReadStream,
                perfect_obstacles_stream: erdos.ReadStream):
        finished_indicator_stream = erdos.WriteStream()
        return [finished_indicator_stream]

    def on_perception(self, msg: erdos.Message):
        game_time = msg.timestamp.coordinates[0]
        self.obstacle_perception.append((game_time, msg.obstacles))

    def on_perfect(self, msg: erdos.Message):
        game_time = msg.timestamp.coordinates[0]
        self.obstacle_perfect.append((game_time, msg.obstacles))

    @erdos.profile_method()
    def on_watermark(self, timestamp: erdos.Timestamp,
                     finished_indicator_stream: erdos.WriteStream):
        percpt = self.obstacle_perception.popleft()
        perf = self.obstacle_perfect.popleft()
        assert percpt[0] == perf[0]
        self._frame_cnt += 1
        if self._frame_cnt % self._flags.detection_eval_freq != 0:
            return
        self.labels = {}
        truth_data = self._build_truth_data(perf[1])
        percpt_data = self._build_perception_data(percpt[1])
        if len(truth_data) and len(percpt_data):
            coco_gt = COCO()
            coco_gt.dataset = truth_data
            coco_gt.createIndex()
            coco_dt = coco_gt.loadRes(percpt_data)
            coco_eval = COCOeval(coco_gt, coco_dt, "bbox")
            coco_eval.evaluate()
            coco_eval.accumulate()
            coco_eval.summarize()
            res = {k: v for k, v in zip(self.keys, coco_eval.stats)}
            res['iou'] = coco_eval.ious[(1,1)].tolist()
        else:
            res = {}
        with open(os.path.join(self._data_path,f'detection_eval-{percpt[0]}.json'), 'w') as f:
            json.dump(res, f)
        

    def _build_truth_data(self, obstacles):
        truth_data = {"images":[{"id":1, 
                                 "width":int(self._flags.camera_image_width), 
                                 "height":int(self._flags.camera_image_height),
                                 "file_name":"frame.jpg"}],
                        "annotations":[],
                        "categories":[]}
        for obs in obstacles:
            if obs.is_person() or obs.is_vehicle():
                label = 'vehicle' if obs.is_vehicle() else 'person'
                if label not in self.labels:
                    self.labels[label] = len(self.labels) + 1
                    truth_data["categories"].append({"id":self.labels[label], "name":label, "supercategory": label})
                x, y, h, w = self._corner2center(obs.bounding_box_2D)
                truth_data["annotations"].append({
                    "id": len(truth_data['annotations'])+1,
                    "image_id":1,
                    "category_id":self.labels[obs.label],
                    "bbox": [x, y, h, w],
                    "area": h*w,
                    "iscrowd":0})
            else:
                continue
        return truth_data
    
    def _build_perception_data(self, obstacles):
        detect_results = []
        for obs in obstacles:
            if obs.is_person() or obs.is_vehicle():
                label = 'vehicle' if obs.is_vehicle() else 'person'
                if label not in self.labels:
                    continue
                x, y, h, w = self._corner2center(obs.bounding_box)
                detect_results.append({ #"id": len(detect_results)+1,
                                        "image_id":1,
                                        "category_id":self.labels[label],
                                        "bbox":[x, y, h, w],
                                        "score":obs.confidence.numpy().item()})
            else:
                continue
        return detect_results

    def _corner2center(self, bbox):
        center = bbox.get_center_point()
        x, y = center.x, center.y
        h = bbox.get_height()
        w = bbox.get_width()
        return x, y, w, h

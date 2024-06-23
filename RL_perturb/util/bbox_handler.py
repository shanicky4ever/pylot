from pylot.perception.detection.utils import BoundingBox2D
import random

class BboxHandler:
    def __init__(self, init_bbox, max_offset_ratio, max_zoom_ratio,frame_width=1920, frame_height=1080):
        self.frame_height = frame_height
        self.frame_width = frame_width
        bbox_list = convert_bbox_list(init_bbox)
        self.bbox = self.corner2center(bbox_list)
        self.max_offset_ratio = max_offset_ratio
        self.max_zoom_ratio = max_zoom_ratio
        print(self.bbox)

    def step(self, action):
        dx, dy, dw, dh = action
        self.bbox[0][0] += dx
        self.bbox[0][1] += dy
        self.bbox[1] += dh
        self.bbox[2] += dw
        self.bbox[0][0] = max(0, min(self.frame_width, self.bbox[0][0]))
        self.bbox[0][1] = max(0, min(self.frame_height, self.bbox[0][1]))
        self.bbox[1] = max(0, min(self.frame_height, self.bbox[1]))
        self.bbox[2] = max(0, min(self.frame_width, self.bbox[2]))
        return self.center2corner(self.bbox)

    def corner2center(self, corner_bbox):
        x_min, y_min, x_max, y_max = corner_bbox[0], corner_bbox[1], corner_bbox[2], corner_bbox[3]
        mid = [(x_min + x_max) // 2, (y_min + y_max) // 2]
        bbox_height = y_max - y_min
        bbox_width = x_max - x_min
        return mid, bbox_height, bbox_width
    
    def center2corner(self, center_bbox):
        mid, bbox_height, bbox_width = center_bbox
        x_min = max(mid[0] - bbox_width // 2, 0)
        y_min = max(mid[1] - bbox_height // 2, 0)
        x_max = min(mid[0] + bbox_width // 2, self.frame_width)
        y_max = min(mid[1] + bbox_height // 2, self.frame_height)
        return [x_min, y_min, x_max, y_max]

def convert_bbox_list(bbox):
    return [bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max]

def convert_list_bbox(bbox_list):
    return BoundingBox2D(bbox_list[0], bbox_list[1], bbox_list[2], bbox_list[3])

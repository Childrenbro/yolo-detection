import cv2
import os
from PyQt6.QtCore import QThread, pyqtSignal
from ultralytics import YOLO
from collections import defaultdict

class YoloDetector(QThread):
    update_image_signal = pyqtSignal(object)
    update_results_signal = pyqtSignal(str)
    detection_finished_signal = pyqtSignal(str)

    def __init__(self, model_path, source_type, source_path, conf_threshold, iou_threshold):
        super().__init__()
        self.model_path = model_path
        self.source_type = source_type
        self.source_path = source_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.model = None
        self.is_running = True

    def run(self):
        try:
            self.model = YOLO(self.model_path)
            print("YOLO model loaded successfully.")
        except Exception as e:
            print(f"Error: Unable to load model {self.model_path}. Error: {e}")
            self.update_results_signal.emit(f"Model loading failed: {e}")
            return

        if self.source_type == 'image':
            self.process_image()
        elif self.source_type == 'video':
            self.process_video()
        elif self.source_type == 'camera':
            self.process_camera()

    def get_image_id(self):
        """提取图片ID（文件名去除路径和后缀）"""
        filename = os.path.basename(self.source_path)
        image_id, _ = os.path.splitext(filename)
        return image_id

    def filter_top4_boxes(self, result):
        """筛选置信度前四的检测框"""
        if result.boxes is None or len(result.boxes) == 0:
            return
        boxes = result.boxes
        box_info = []
        for i in range(len(boxes)):
            conf = boxes.conf[i].item()
            box_info.append( (conf, i) )
        # 按置信度降序排序
        box_info.sort(key=lambda x: x[0], reverse=True)
        # 取前四个的索引
        top4_indices = [idx for conf, idx in box_info[:4]]
        # 筛选出前四个box
        result.boxes = boxes[top4_indices]

    def process_image(self):
        results = self.model(self.source_path, conf=self.conf_threshold, iou=self.iou_threshold)
        self.filter_top4_boxes(results[0])
        annotated_frame = results[0].plot()
        self.update_image_signal.emit(annotated_frame)
        result_text = self.format_results(results[0], self.get_image_id())
        self.update_results_signal.emit(result_text)
        self.detection_finished_signal.emit(result_text)

    def process_video(self):
        cap = cv2.VideoCapture(self.source_path)
        if not cap.isOpened():
            self.update_results_signal.emit("Error: Unable to open video file.")
            return
            
        last_result_text = "Video processing in progress..."
        while self.is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            results = self.model(frame, conf=self.conf_threshold, iou=self.iou_threshold)
            self.filter_top4_boxes(results[0])
            annotated_frame = results[0].plot()
            self.update_image_signal.emit(annotated_frame)
            
            last_result_text = self.format_results(results[0], "video_frame")
            self.update_results_signal.emit(last_result_text)
            self.msleep(30)

        cap.release()
        
        if self.is_running:
            final_summary = "Video processing completed.\n" + last_result_text
            self.update_results_signal.emit("Video processing completed.")
            self.detection_finished_signal.emit(final_summary)

    def process_camera(self):
        try:
            camera_index = int(self.source_path)
        except ValueError:
            camera_index = self.source_path

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            self.update_results_signal.emit("Error: Unable to open camera.")
            return

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                self.update_results_signal.emit("Error: Unable to read frame from camera.")
                break
            
            results = self.model(frame, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
            self.filter_top4_boxes(results[0])
            annotated_frame = results[0].plot()
            self.update_image_signal.emit(annotated_frame)
            
            result_text = self.format_results(results[0], "camera_frame")
            self.update_results_signal.emit(result_text)
        
        cap.release()
        print("Camera released.")

    def format_results(self, result, image_id):
        """生成markdown格式的检测结果表格（包含归一化坐标，取置信度前四的结果）"""
        if result.boxes is None or len(result.boxes) == 0:
            return "No target detected in the current frame."

        class_names = result.names
# -----------------------------------------------需修改：定义类别与ID的映射关系--------------------------------------------------
        class_id_map = {"hole": 0, "broken": 1, "rusty": 2, "scratch": 3, "sd": 4, "hd": 5, "vd": 6}
# ---------------------------------------------------------------------------------------------------------------------------
        # 获取图像原始尺寸（高度、宽度）用于归一化
        orig_height, orig_width = result.orig_shape  # YOLO的orig_shape返回(高, 宽)
        # markdown表格表头
        text_lines = [
            "| image_id | class_id | x_center | y_center | width | height |",
            "|----------|----------|----------|----------|-------|--------|"
        ]

        # 收集所有box信息并按置信度降序排序，取前4个
        box_info_list = []
        for box in result.boxes:
            conf = box.conf.cpu().numpy()[0]
            cls = int(box.cls)
            xywh = box.xywh.cpu().numpy()[0]
            box_info_list.append( (conf, cls, xywh) )
        
        # 按置信度降序排序（此处因filter_top4_boxes已处理，排序可省略但保留逻辑一致性）
        box_info_list.sort(key=lambda x: x[0], reverse=True)
        # 取前4个结果
        box_info_list = box_info_list[:4]

        for conf, cls, xywh in box_info_list:
            class_name = class_names[cls]
            # 根据映射关系生成class_id
            class_id = f"{class_id_map[class_name]}-{class_name}"

            x_center_pix, y_center_pix, width_pix, height_pix = xywh
            
            # 归一化计算（保留4位小数）
            x_center = f"{x_center_pix / orig_width:.4f}"  # x中心坐标 / 图像宽度
            y_center = f"{y_center_pix / orig_height:.4f}"  # y中心坐标 / 图像高度
            width = f"{width_pix / orig_width:.4f}"  # 宽度 / 图像宽度
            height = f"{height_pix / orig_height:.4f}"  # 高度 / 图像高度
            
            # 拼接markdown表格行
            text_lines.append(
                f"| {image_id} | {class_id} | {x_center} | {y_center} | {width} | {height} |"
            )
        
        return "\n".join(text_lines)

    def stop(self):
        self.is_running = False
        print("Requesting to stop the detection thread...")
        self.wait()
        print("Detection thread has stopped.")
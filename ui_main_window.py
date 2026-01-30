import cv2
import sys
import os
from database import add_history_record, get_all_history, update_history_summary, add_feedback
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QStackedWidget, QListWidget, QLabel, QFileDialog, QFrame,
                             QTextEdit, QLineEdit, QFormLayout, QDoubleSpinBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QApplication)
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt
from yolo_detector import YoloDetector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Container Damage Detection System")
        self.setGeometry(100, 100, 1200, 800)
        self.detector_thread = None
        self.current_history_id = None
        # 新增：批量图片检测的图片列表和当前索引
        self.image_paths = []
        self.current_image_index = -1

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_widget.setFixedWidth(200)

        self.nav_list = QListWidget()
        self.nav_items = ["Main Dashboard", "Image Detection", "Video Detection", "Real-time Detection", "System Settings", "History", "Help", "Feedback", "User Manual", "Exit"]
        self.nav_list.addItems(self.nav_items)
        nav_layout.addWidget(self.nav_list)
        
        self.stacked_widget = QStackedWidget()
        self.settings_page = self.create_settings_page()
        self.dashboard_page = self.create_dashboard_page()
        self.image_page = self.create_detection_page("image")
        self.video_page = self.create_detection_page("video")
        self.camera_page = self.create_detection_page("camera")
        self.history_page = self.create_history_page()
        self.help_page = self.create_help_page()
        self.feedback_page = self.create_feedback_page()
        self.instructions_page = self.create_instructions_page()

        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.image_page)
        self.stacked_widget.addWidget(self.video_page)
        self.stacked_widget.addWidget(self.camera_page)
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.history_page)
        self.stacked_widget.addWidget(self.help_page)
        self.stacked_widget.addWidget(self.feedback_page)
        self.stacked_widget.addWidget(self.instructions_page)
        
        main_layout.addWidget(nav_widget)
        main_layout.addWidget(self.stacked_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-image: url("port_bg.jpg");
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }

            QWidget[objectName="nav_widget"] {
                background-color: #333644;
                border-right: 1px solid #222;
            }

            QListWidget {
                background-color: transparent;
                color: white;
                font-size: 14px;
                border: none;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-left: 3px solid transparent;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 122, 0, 0.2);
                border-left: 3px solid #FF7A00;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(255, 255, 255, 0.1);
            }

            QPushButton {
                background-color: #333644;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FF7A00;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #ccc;
            }

            QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border-color: #FF7A00;
                outline: none;
            }
            QTextEdit[readOnly="true"] {
                background-color: #f5f5f5;
            }

            QWidget[objectName="control_panel"] {
                background-color: rgba(245, 247, 250, 0.9);
                border-right: 1px solid #ddd;
                padding: 10px;
            }

            QLabel[objectName="image_display_label"] {
                background-color: #1a1a1a;
                border: 1px solid #FF7A00;
                color: white;
                font-size: 14px;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #333644;
                color: white;
                padding: 8px;
                border: 1px solid #222;
                font-size: 13px;
                text-align: center;
            }
            QTableWidget::item {
                padding: 6px;
                font-size: 12px;
                text-align: center;
            }
            QTableWidget::item:alternate {
                background-color: #f5f5f5;
            }
            QTableWidget::item:hover {
                background-color: #fff3e6;
            }

            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLabel[text^="<h1>"], QLabel[text^="<h2>"], QLabel[text^="<h3>"] {
                color: #2c3e50;
                margin-bottom: 10px;
            }
            QLabel[objectName="dashboard_info_label"] b {
                color: #FF7A00;
            }

            QFrame[frameShape="HLine"] {
                color: #ccc;
                margin: 10px 0;
            }

            QMessageBox {
                background-color: white;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """)

        nav_widget.setObjectName("nav_widget")
        self.dashboard_info_label.setObjectName("dashboard_info_label")

        self.nav_list.currentRowChanged.connect(self.handle_nav_selection)
        self.nav_list.setCurrentRow(0)
        self.model_path_input.textChanged.connect(self.update_dashboard_info)
        self.update_dashboard_info()

    def handle_nav_selection(self, index):
        item_text = self.nav_list.item(index).text()
        if item_text == "Exit":
            self.close()
        else:
            if item_text == "History":
                self.refresh_history_table()
            self.stacked_widget.setCurrentIndex(index)

    def update_history_with_final_summary(self, final_summary):
        if self.current_history_id is not None:
            update_history_summary(self.current_history_id, final_summary)
            print(f"History record ID: {self.current_history_id} has been updated with the final result.")

    def start_detection(self, source_type, source_path, image_label, results_table):
        if not source_path or source_path == "No file selected":
            QMessageBox.warning(self, "Warning", "Please select a valid source first!")
            return
        self.stop_detection()
        model_path = self.model_path_input.text()
        conf = self.conf_spinbox.value()
        iou = self.iou_spinbox.value()
        self.detector_thread = YoloDetector(model_path, source_type, source_path, conf, iou)
        
        self.detector_thread.detection_finished_signal.connect(self.update_history_with_final_summary)
        
        self.detector_thread.update_image_signal.connect(lambda img: self.update_image(img, image_label))
        self.detector_thread.update_results_signal.connect(
            lambda markdown_text: self.update_results_table(markdown_text, results_table)
        )
        self.detector_thread.start()
        
        model_filename = os.path.basename(model_path)
        summary = f"Using model {model_filename} for detection..."
        self.current_history_id = add_history_record(source_type, source_path, summary)
        print(f"Created new history record, ID: {self.current_history_id}")

        results_table.setRowCount(1)
        tips_item = QTableWidgetItem(f"Using model {model_filename} for detection...")
        tips_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        results_table.setItem(0, 0, tips_item)
        results_table.setSpan(0, 0, 1, 6)

    def update_results_table(self, markdown_text, results_table):
        results_table.setRowCount(0)
        
        if markdown_text == "No targets detected in current frame.":
            results_table.setRowCount(1)
            empty_item = QTableWidgetItem(markdown_text)
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            results_table.setItem(0, 0, empty_item)
            results_table.setSpan(0, 0, 1, 6)
            return
        
        markdown_lines = markdown_text.strip().split("\n")
        if len(markdown_lines) < 3:
            return
        
        data_lines = markdown_lines[2:]
        for row_idx, line in enumerate(data_lines):
            line_parts = [part.strip() for part in line.strip("|").split("|")]
            if len(line_parts) != 6:
                continue
            
            results_table.insertRow(row_idx)
            for col_idx, part in enumerate(line_parts):
                cell_item = QTableWidgetItem(part)
                cell_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                results_table.setItem(row_idx, col_idx, cell_item)

    def create_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("<h2>Detection History</h2>")
        layout.addWidget(title)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["ID", "Detection Type", "Source File/Camera", "Detection Time", "Result Summary"])
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self.history_table)
        return page

    def refresh_history_table(self):
        history_data = get_all_history()
        self.history_table.setRowCount(0)
        self.history_table.setRowCount(len(history_data))
        for row_index, row_data in enumerate(history_data):
            self.history_table.setItem(row_index, 0, QTableWidgetItem(str(row_data['id'])))
            self.history_table.setItem(row_index, 1, QTableWidgetItem(row_data['detection_type']))
            self.history_table.setItem(row_index, 2, QTableWidgetItem(row_data['source_path']))
            self.history_table.setItem(row_index, 3, QTableWidgetItem(row_data['detection_time']))
            self.history_table.setItem(row_index, 4, QTableWidgetItem(row_data['result_summary']))

    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("<h1>Welcome to the Intelligent Container Damage Detection System</h1>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dashboard_info_label = QLabel()
        self.dashboard_info_label.setTextFormat(Qt.TextFormat.RichText)
        self.dashboard_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(self.dashboard_info_label)
        return page

    def update_dashboard_info(self):
        model_path = self.model_path_input.text()
        model_filename = os.path.basename(model_path)
        info_text = (f"Please select a function from the left navigation bar to start using.<br><br>"
                     f"Current model: <b style='color:blue;'>{model_filename}</b><br>"
                     f"System status: <b style='color:green;'>Normal</b>")
        self.dashboard_info_label.setText(info_text)

    def create_detection_page(self, page_type):
        page = QWidget()
        layout = QHBoxLayout(page)
        
        control_panel = QWidget()
        control_panel.setObjectName("control_panel")
        control_panel.setFixedWidth(350)
        control_layout = QVBoxLayout(control_panel)
        
        source_label = QLabel(f"<h3>Please select {'image' if page_type == 'image' else 'video'} file</h3>")
        source_path_label = QLabel("No file selected")
        source_path_label.setWordWrap(True)
        select_button = QPushButton(f"Select {'image' if page_type == 'image' else 'video'}")
        camera_input = None
        if page_type == 'camera':
             source_label.setText("<h3>Camera Detection</h3>")
             source_path_label.setText("Default using camera 0, can be manually changed")
             camera_input = QLineEdit("0")
             control_layout.addWidget(camera_input)
        start_button = QPushButton("Start Detection")
        stop_button = QPushButton("Stop Detection")
        control_layout.addWidget(source_label)
        if page_type != 'camera':
            control_layout.addWidget(source_path_label)
            control_layout.addWidget(select_button)
        control_layout.addWidget(start_button)
        control_layout.addWidget(stop_button)

        # 新增：批量图片检测功能（仅在图片检测页面生效）
        if page_type == "image":
            # 选择图片文件夹按钮
            select_folder_button = QPushButton("Select Image Folder")
            control_layout.addWidget(select_folder_button)
            select_folder_button.clicked.connect(lambda: self.select_image_folder(source_path_label))

            # 翻页按钮布局
            page_layout = QHBoxLayout()
            self.prev_btn = QPushButton("Previous Image")
            self.next_btn = QPushButton("Next Image")
            self.prev_btn.setDisabled(True)
            self.next_btn.setDisabled(True)
            page_layout.addWidget(self.prev_btn)
            page_layout.addWidget(self.next_btn)
            control_layout.addLayout(page_layout)

            # 翻页按钮点击事件
            self.prev_btn.clicked.connect(lambda: self.switch_image(-1, source_path_label, image_display_label, results_table))
            self.next_btn.clicked.connect(lambda: self.switch_image(1, source_path_label, image_display_label, results_table))

        control_layout.addStretch()
        
        display_area = QWidget()
        display_layout = QVBoxLayout(display_area)
        
        image_display_label = QLabel("Detection display area")
        image_display_label.setObjectName("image_display_label")
        image_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_display_label.setFrameShape(QFrame.Shape.Box)
        image_display_label.setMinimumSize(600, 400)
        image_display_label.setStyleSheet("background-color: #333; color: white;")
        
        results_table = QTableWidget()
        results_table.setColumnCount(6)
        results_table.setHorizontalHeaderLabels(["image_id", "class_id", "x_center", "y_center", "width", "height"])
        results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_table.setFixedHeight(250)
        
        detection_title_label = QLabel("Detection Results:")
        detection_title_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        
        display_layout.addWidget(image_display_label)
        display_layout.addWidget(detection_title_label)
        display_layout.addWidget(results_table)
        
        layout.addWidget(control_panel)
        layout.addWidget(display_area)
        
        if page_type == "image":
            select_button.clicked.connect(lambda: self.select_file('image', source_path_label))
            start_button.clicked.connect(lambda: self.start_detection('image', source_path_label.text(), image_display_label, results_table))
        elif page_type == "video":
            select_button.clicked.connect(lambda: self.select_file('video', source_path_label))
            start_button.clicked.connect(lambda: self.start_detection('video', source_path_label.text(), image_display_label, results_table))
        elif page_type == "camera":
            start_button.clicked.connect(lambda: self.start_detection('camera', camera_input.text(), image_display_label, results_table))
        stop_button.clicked.connect(self.stop_detection)
        return page
        
    def select_image_folder(self, source_path_label):
        """选择包含多张图片的文件夹，初始化图片列表和索引"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder_path:
            return
        
        # 过滤出文件夹内的图片文件（支持jpg、png、bmp等格式）
        img_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        self.image_paths = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path) 
            if os.path.splitext(f.lower())[1] in img_extensions
        ]
        
        if not self.image_paths:
            QMessageBox.warning(self, "Prompt", "No valid image files found in the folder!")
            return
        
        # 初始化当前索引为0，更新UI
        self.current_image_index = 0
        source_path_label.setText(self.image_paths[self.current_image_index])
        # 激活翻页按钮
        self.prev_btn.setDisabled(False)
        self.next_btn.setDisabled(len(self.image_paths) == 1)

    def switch_image(self, step, source_path_label, image_label, results_table):
        """切换图片并触发检测"""
        self.current_image_index += step
        # 更新按钮状态
        self.prev_btn.setDisabled(self.current_image_index == 0)
        self.next_btn.setDisabled(self.current_image_index == len(self.image_paths) - 1)
        # 更新当前图片路径并开始检测
        source_path_label.setText(self.image_paths[self.current_image_index])
        self.start_detection('image', self.image_paths[self.current_image_index], image_label, results_table)

    def create_settings_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        page.setContentsMargins(20, 20, 20, 20)

# ------------------------------------------需修改：修改成自己的训练模型------------------------------------------------------
        self.model_path_input = QLineEdit(r"D:\竞赛\2025妈妈杯-大数据挑战赛\MCB2501644\支撑材料\code\Q2\ultralytics-main\ultralytics\runs\yolo11n\weights\best.pt")
# --------------------------------------------------------------------------------------------------------------------------

        select_model_button = QPushButton("Select Model File")
        select_model_button.clicked.connect(self.select_model_file)
        self.conf_spinbox = QDoubleSpinBox()
        self.conf_spinbox.setRange(0.0, 1.0)
        self.conf_spinbox.setSingleStep(0.05)
        self.conf_spinbox.setValue(0.25)
        self.iou_spinbox = QDoubleSpinBox()
        self.iou_spinbox.setRange(0.0, 1.0)
        self.iou_spinbox.setSingleStep(0.05)
        self.iou_spinbox.setValue(0.45)
        layout.addRow(QLabel("<h2>Parameter Settings</h2>"), None)
        layout.addRow("Model Path:", self.model_path_input)
        layout.addRow("", select_model_button)
        layout.addRow("Confidence Threshold (conf):", self.conf_spinbox)
        layout.addRow("IOU Threshold (iou):", self.iou_spinbox)
        return page

    def create_help_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        html_content = """
        <style>
            body {
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 14pt;
                line-height: 1.6;
                color: #333;
            }
            h1, h2 {
                color: #2c3e50;
                border-bottom: 1px solid #ddd;
                padding-bottom: 8px;
                margin-top: 20px;
            }
            b {
                color: #0056b3;
            }
        </style>
        <body>
            <h1>Help Documentation</h1>
            <h2>Frequently Asked Questions (FAQ)</h2>
            <p><b>Q: How to select your own model?</b></p>
            <p>A: Please click on "System Settings" in the left navigation bar, then click the "Select Model File" button and find your .pt model file in your computer.</p>
            <p><b>Q: Why is real-time detection very laggy?</b></p>
            <p>A: Real-time detection consumes a lot of computing resources. Please ensure your computer configuration is sufficient, or appropriately lower the confidence threshold in "System Settings" to reduce computational load.</p>

            <h2>Contact Us</h2>
            <p>If you encounter any issues that cannot be resolved, please contact us through the "Feedback" page, or send an email to 1828147300@qq.com.</p>
        </body>
        """
        
        text_edit.setHtml(html_content)
        
        layout.addWidget(text_edit)
        return page
        
    def create_feedback_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        page.setContentsMargins(20, 20, 20, 20)
        title = QLabel("<h2>Problem and Suggestion Feedback</h2>")
        self.feedback_type_combo = QComboBox()
        self.feedback_type_combo.addItems(["Bug Feedback", "Feature Suggestions", "Interface Issues", "Other"])
        self.feedback_text_edit = QTextEdit()
        self.feedback_text_edit.setPlaceholderText("Please describe the problem or suggestion in detail...")
        self.feedback_text_edit.setMinimumHeight(200)
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Optional, your email or phone number for contact")
        submit_button = QPushButton("Submit Feedback")
        submit_button.clicked.connect(self.submit_feedback)
        layout.addRow(title)
        layout.addRow("Feedback Type:", self.feedback_type_combo)
        layout.addRow("Detailed Description:", self.feedback_text_edit)
        layout.addRow("Contact Information:", self.contact_input)
        layout.addRow(submit_button)
        return page
    
    def create_instructions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        html_content = """
        <style>
            body {
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 14pt;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 1px solid #ddd;
                padding-bottom: 8px;
            }
            ol {
                padding-left: 30px;
            }
            li {
                margin-bottom: 12px;
            }
            b {
                color: #0056b3;
            }
            p {
                margin-top: 25px;
            }
        </style>
        <body>
            <h1>使用说明</h1>
            <ol>
                <li><b>System Settings:</b> For first-time use, please configure your YOLO model path in the "System Settings" page.</li>
                <li><b>Image Detection:</b> Click "Image Detection", select an image or an image folder, then click "Start Detection". You can use the "Previous/Next" buttons to batch detect images in a folder.</li>
                <li><b>Video Detection:</b> Click "Video Detection", select a video file, then click "Start Detection". The system will process and display each frame.</li>
                <li><b>Real-time Detection:</b> Click "Real-time Detection", and the system will automatically call the default camera. You can change the camera ID (e.g., 0, 1, 2...) in the input box.</li>
            </ol>
            <p>Enjoy your experience!</p>
        </body>
        """
        
        text_edit.setHtml(html_content)
        
        layout.addWidget(text_edit)
        return page

    def submit_feedback(self):
        feedback_type = self.feedback_type_combo.currentText()
        feedback_content = self.feedback_text_edit.toPlainText()
        contact_info = self.contact_input.text()

        if not feedback_content.strip():
            QMessageBox.warning(self, "Submission failed, feedback cannot be empty!", "Please enter your feedback content before submitting.")
            return

        success = add_feedback(feedback_type, feedback_content, contact_info)

        if success:
            QMessageBox.information(self, "Submission successful", f"Your [{feedback_type}] feedback has been submitted successfully, thank you for your support!")
            self.feedback_text_edit.clear()
            self.contact_input.clear()
        else:
            QMessageBox.critical(self, "Submission failed", "Failed to write your feedback to the database. Please check the backend logs.")
    def select_model_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select model file", "", "PyTorch Models (*.pt)")
        if file_path:
            self.model_path_input.setText(file_path)

    def select_file(self, file_type, label_to_update):
        dialog_title = "Select image" if file_type == 'image' else "Select video"
        file_filter = "Images (*.png *.xpm *.jpg *.bmp);;All Files (*)" if file_type == 'image' else "Videos (*.mp4 *.avi *.mov);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, dialog_title, "", file_filter)
        if file_path:
            label_to_update.setText(file_path)
            # 重置批量图片列表（避免与单张选择冲突）
            self.image_paths = []
            self.current_image_index = -1
            self.prev_btn.setDisabled(True)
            self.next_btn.setDisabled(True)

    def stop_detection(self):
        if self.detector_thread and self.detector_thread.isRunning():
            self.detector_thread.stop()
            self.detector_thread = None

    def update_image(self, frame, image_label):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit Program', 'Are you sure you want to exit this system?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.stop_detection()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
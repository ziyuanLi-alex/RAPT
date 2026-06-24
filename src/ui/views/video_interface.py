# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import ( QMediaDevices
)
from PyQt6.QtGui import QPixmap, QImage
from qfluentwidgets import (
    SubtitleLabel, CardWidget, LineEdit, 
    SpinBox, PrimaryPushButton, BodyLabel, 
    StrongBodyLabel, InfoBar, InfoBarPosition,
    SegmentedWidget, ComboBox
)
import cv2
import threading 

from core.settings import ConfigManager
from core.DataCollector import DataCollector
from ui.i18n import t
from ..threads import VideoThread, ContinuousCollectThread
import time

class VideoInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("videoInterface")
        
        self.config = ConfigManager()
        self.dataCollector = DataCollector(self.config)
        
        self.videoThread = None
        self.rfidThread = None
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # Header
        self.titleLabel = SubtitleLabel(t("video.title", self.config), self)
        self.vBoxLayout.addWidget(self.titleLabel)

        # Content Layout: Left (Video), Right (Stats)
        self.contentLayout = QHBoxLayout()
        
        # Video Card
        self.videoCard = CardWidget(self)
        self.videoLayout = QVBoxLayout(self.videoCard)
        self.videoLabel = QLabel("等待摄像头...", self.videoCard)
        self.videoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.videoLabel.setMinimumSize(640, 480)
        self.videoLabel.setStyleSheet("background-color: #202020; color: #808080;")
        self.videoLayout.addWidget(self.videoLabel)
        
        self.contentLayout.addWidget(self.videoCard, 2)
        
        # Stats/Log Panel
        self.statsLayout = QVBoxLayout()
        self.statsLabel = StrongBodyLabel("采集状态: 就绪", self)
        self.logDisplay = QPlainTextEdit(self)
        self.logDisplay.setReadOnly(True)
        self.logDisplay.setPlaceholderText("日志信息...")
        font = self.logDisplay.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.logDisplay.setFont(font)
        
        self.statsLayout.addWidget(self.statsLabel)
        self.statsLayout.addWidget(self.logDisplay)
        
        self.contentLayout.addLayout(self.statsLayout, 1)
        self.vBoxLayout.addLayout(self.contentLayout)

        # Control Card
        self.controlCard = CardWidget(self)
        self.controlCard.setFixedHeight(80)
        self.controlLayout = QHBoxLayout(self.controlCard)
        self.controlLayout.setContentsMargins(10, 10, 10, 10)
        
        self.camLabel = BodyLabel(t("video.camera", self.config), self.controlCard)
        self.camCombo = ComboBox(self.controlCard)
        self.camCombo.setFixedWidth(140)
        self.populate_cameras()
        
        self.nameLabel = BodyLabel("任务名称:", self.controlCard)
        self.nameEdit = LineEdit(self.controlCard)
        self.nameEdit.setPlaceholderText("video_test_01")
        self.nameEdit.setFixedWidth(150)
        
        self.startBtn = PrimaryPushButton(t("video.start_capture", self.config), self.controlCard)
        self.startBtn.clicked.connect(self.toggleCapture)
        
        self.controlLayout.addWidget(self.camLabel)
        self.controlLayout.addWidget(self.camCombo)
        
        self.testBtn = PrimaryPushButton("测试/预览", self.controlCard)
        self.testBtn.clicked.connect(self.toggleTest)
        self.controlLayout.addWidget(self.testBtn)
        
        self.controlLayout.addSpacing(20)
        self.controlLayout.addWidget(self.nameLabel)
        self.controlLayout.addWidget(self.nameEdit)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.startBtn)
        
        self.vBoxLayout.addWidget(self.controlCard)

        # Mode Selector
        self.modePivot = SegmentedWidget(self)
        self.modePivot.addItem("Joint", t("video.joint", self.config))
        self.modePivot.addItem("Video", t("video.video_only", self.config))
        self.modePivot.addItem("RFID", t("video.rfid_only", self.config))
        self.modePivot.setCurrentItem("Joint")
        self.modePivot.currentItemChanged.connect(self.onModeChanged)
        self.currentMode = "Joint"
        
        # Insert Pivot into header or top of content? 
        # Let's put it in the control layout for now, or maybe above the control card.
        # Ideally, it fits nicely in the control card or as a separate row.
        # Let's add it to the control layout before the start button.
        self.controlLayout.insertWidget(6, self.modePivot)
        self.controlLayout.insertSpacing(7, 20)

    def onModeChanged(self, key):
        self.currentMode = key

    def populate_cameras(self):
        self.camCombo.clear()
        # 获取系统中所有可用的视频输入设备
        cameras = QMediaDevices.videoInputs()
        
        if not cameras:
            self.camCombo.addItem("未检测到摄像头", userData=-1)
            return

        for i, camera in enumerate(cameras):
            # 获取设备描述名称
            name = camera.description()
            # 获取唯一 ID
            device_id = camera.id()
            self.camCombo.addItem(f"{name}", userData=i)
            
        self.camCombo.setCurrentIndex(0)

    # def populate_cameras(self):
    #     self.camCombo.clear()
    #     found = False
        
    #     # Determine backend
    #     import os
    #     backends = []
    #     if os.name == 'nt':
    #         backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    #     else:
    #         backends = [cv2.CAP_ANY]
        
    #     # Check first 3 indices
    #     for i in range(3):
    #         is_opened = False
    #         for backend in backends:
    #             try:
    #                 cap = cv2.VideoCapture(i, backend)
    #                 if cap.isOpened():
    #                     self.camCombo.addItem(f"Camera {i}", userData=i)
    #                     found = True
    #                     is_opened = True
    #                     cap.release()
    #                     break # Found a working backend for this index
    #                 else:
    #                     cap.release()
    #             except:
    #                 pass
            
    #         # If we want to be less strict, we can just add indices that we think *might* exist
    #         # But scanning is better.
            
    #     if not found:
    #         self.camCombo.addItem("Camera 0", userData=0)
            
    #     self.camCombo.setCurrentIndex(0)

    def toggleTest(self):
        # Prevent test if capture is running
        if self.startBtn.text() == "停止采集":
            return
            
        if self.videoThread and self.videoThread.isRunning():
            # Stop Test
            self.videoThread.stop()
            self.testBtn.setText("测试/预览")
            self.startBtn.setEnabled(True)
            self.nameEdit.setEnabled(True)
            self.camCombo.setEnabled(True)
            self.modePivot.setEnabled(True)
            self.statsLabel.setText("采集状态: 就绪")
            self.videoThread = None # Reset
        else:
            # Start Test
            camera_id = self.camCombo.currentData()
            # Fallback if currentData is None (issue with qfluentwidgets or binding)
            if camera_id is None:
                text = self.camCombo.currentText()
                if "Camera" in text:
                    try:
                        camera_id = int(text.split(" ")[-1])
                    except:
                        camera_id = 0
                else:
                    camera_id = 0
                    
            self.logDisplay.clear()
            self.logDisplay.appendPlainText(f"启动预览... (Camera: {camera_id})")
            
            self.videoThread = VideoThread(
                camera_id=camera_id,
                action_name="test_preview",
                output_dir=self.config.output_dir,
                parent=self,
                preview_only=True
            )
            self.videoThread.frame_captured.connect(self.onFrameCaptured)
            self.videoThread.error.connect(self.onVideoError)
            self.videoThread.start()
            
            self.testBtn.setText("停止测试")
            self.startBtn.setEnabled(False)
            self.nameEdit.setEnabled(False)
            self.camCombo.setEnabled(False)
            self.modePivot.setEnabled(False)
            self.statsLabel.setText("采集状态: 摄像头测试中...")

    def toggleCapture(self):
        # Prevent capture if test is running
        if self.testBtn.text() == "停止测试":
            return
        if self.videoThread and self.videoThread.isRunning():
            # Stop
            self.stopCapture()
        else:
            # Start
            self.startCapture()

    def startCapture(self):
        action_name = self.nameEdit.text().strip()
        if not action_name:
            action_name = "video_session"
            
        camera_id = self.camCombo.currentData()
        if camera_id is None:
             # Fallback
             text = self.camCombo.currentText()
             try:
                 camera_id = int(text.split(" ")[-1])
             except:
                 camera_id = 0
                 
        mode = self.currentMode
        
        self.logDisplay.clear()
        self.logDisplay.appendPlainText(f"正在初始化... (Mode: {mode}, Camera: {camera_id})")
        
        # Setup Barrier for Joint Mode
        sync_barrier = None
        if mode == "Joint":
            sync_barrier = threading.Barrier(2)
            self.logDisplay.appendPlainText("等待线程同步启动...")
        
        # 1. Initialize Video Thread (if needed)
        if mode in ["Joint", "Video"]:
            self.videoThread = VideoThread(
                camera_id=camera_id,
                action_name=action_name,
                output_dir=self.config.output_dir,
                parent=self,
                sync_barrier=sync_barrier
            )
            self.videoThread.frame_captured.connect(self.onFrameCaptured)
            self.videoThread.saved.connect(self.onVideoSaved)
            self.videoThread.error.connect(self.onVideoError)
        
        # 2. Initialize RFID Thread (Raw Mode) (if needed)
        if mode in ["Joint", "RFID"]:
            self.rfidThread = ContinuousCollectThread(
                data_collector=self.dataCollector,
                action_name=action_name,
                duration=0, # Infinite until stop
                parent=self,
                mode="raw",
                sync_barrier=sync_barrier
            )
            self.rfidThread.progress_update.connect(self.onRfidProgress)
            self.rfidThread.saved.connect(self.onRfidSaved)
            self.rfidThread.error.connect(self.onRfidError)
        
        # Start Threads
        if self.videoThread:
            self.videoThread.start()
        if self.rfidThread:
            self.rfidThread.start()
        
        self.startBtn.setText("停止采集")
        self.nameEdit.setEnabled(False)
        self.camCombo.setEnabled(False)
        self.modePivot.setEnabled(False)
        self.statsLabel.setText(f"采集状态: 进行中 ({mode})")

    def stopCapture(self):
        self.startBtn.setEnabled(False)
        self.startBtn.setText("正在停止...")
        
        if self.rfidThread and self.rfidThread.isRunning():
            self.rfidThread.stop()
        
        if self.videoThread and self.videoThread.isRunning():
            self.videoThread.stop()
            
        # Manually trigger check if threads are already dead (edge case)
        if not (self.rfidThread and self.rfidThread.isRunning()) and \
           not (self.videoThread and self.videoThread.isRunning()):
               self.checkFinished()

    def onFrameCaptured(self, image: QImage, timestamp: float):
        # Scale image to fit label while keeping aspect ratio
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.videoLabel.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.videoLabel.setPixmap(scaled)

    def onRfidProgress(self, data):
        # Update RFID stats
        fc = data["frame_count"]
        epc = data["last_epc"]
        self.logDisplay.appendPlainText(f"RFID: Count={fc}, Last={epc}")
        # Scroll to bottom
        sb = self.logDisplay.verticalScrollBar()
        sb.setValue(sb.maximum())

    def onVideoSaved(self, video_path, meta_path):
        self.logDisplay.appendPlainText(f"[Video Saved] {video_path}")
        self.checkFinished()

    def onRfidSaved(self, csv_path):
        self.logDisplay.appendPlainText(f"[RFID Saved] {csv_path}")
        self.checkFinished()

    def onVideoError(self, msg):
        self.logDisplay.appendPlainText(f"[Video Error] {msg}")
        self.checkFinished()

    def onRfidError(self, msg):
        self.logDisplay.appendPlainText(f"[RFID Error] {msg}")
        self.checkFinished()
        
    def checkFinished(self):
        # Check if both threads are finished/stopped
        v_running = self.videoThread and self.videoThread.isRunning()
        r_running = self.rfidThread and self.rfidThread.isRunning()
        
        if not v_running and not r_running:
            self.startBtn.setText(t("video.start_capture", self.config))
            self.startBtn.setEnabled(True)
            self.nameEdit.setEnabled(True)
            self.camCombo.setEnabled(True)
            self.modePivot.setEnabled(True)
            self.statsLabel.setText("采集状态: 完成")
            
            # Reset threads to allow proper re-initialization next time
            self.videoThread = None
            self.rfidThread = None
            
            InfoBar.success(
                title='采集结束',
                content="数据保存完成",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT
            )

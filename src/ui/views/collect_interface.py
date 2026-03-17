# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    SubtitleLabel, SegmentedWidget, CardWidget, LineEdit, 
    SpinBox, PrimaryPushButton, BodyLabel, StrongBodyLabel,
    InfoBar, InfoBarPosition, StateToolTip
)

from core.settings import ConfigManager
from core.DataCollector import DataCollector
from core.binding import BindingManager
from ..threads import ContinuousCollectThread, SingleShotCollectThread

import csv
import time
from pathlib import Path
from datetime import datetime

class CollectInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("collectInterface")
        
        self.config = ConfigManager()
        self.dataCollector = DataCollector(self.config)
        self.bindingManager = BindingManager(self.config) # 需确保 BindingManager 支持无参或 Config 初始化
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # 1. Header & Navigation
        self.headerLayout = QHBoxLayout()
        self.titleLabel = SubtitleLabel("采集监控", self)
        
        self.pivot = SegmentedWidget(self)
        self.pivot.addItem("Continuous", "持续采集")
        self.pivot.addItem("SingleShot", "单次采集")
        self.pivot.setCurrentItem("Continuous")
        self.pivot.currentItemChanged.connect(self.onPivotChanged)
        
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.pivot)
        
        self.vBoxLayout.addLayout(self.headerLayout)

        # 2. Stacked Content
        self.stackedWidget = QStackedWidget(self)
        self.continuousInterface = ContinuousInterface(self)
        self.singleShotInterface = SingleShotInterface(self)
        
        self.stackedWidget.addWidget(self.continuousInterface)
        self.stackedWidget.addWidget(self.singleShotInterface)
        
        self.vBoxLayout.addWidget(self.stackedWidget)

    def onPivotChanged(self, key):
        if key == "Continuous":
            self.stackedWidget.setCurrentWidget(self.continuousInterface)
        else:
            self.stackedWidget.setCurrentWidget(self.singleShotInterface)


class ContinuousInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_interface = parent
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(15)
        
        # --- Config Card ---
        self.configCard = CardWidget(self)
        self.configCard.setFixedHeight(80)
        self.configLayout = QHBoxLayout(self.configCard)
        self.configLayout.setContentsMargins(20, 10, 20, 10)
        
        self.nameLabel = BodyLabel("动作名称:", self.configCard)
        self.nameEdit = LineEdit(self.configCard)
        self.nameEdit.setPlaceholderText("可选 (如: walk_test)")
        self.nameEdit.setFixedWidth(200)
        
        self.durationLabel = BodyLabel("持续时间 (秒, 0=无限):", self.configCard)
        self.durationSpin = SpinBox(self.configCard)
        self.durationSpin.setRange(0, 3600)
        self.durationSpin.setValue(0)
        
        self.startBtn = PrimaryPushButton("开始采集", self.configCard)
        self.startBtn.clicked.connect(self.toggleCapture)
        self.stopBtn = PrimaryPushButton("停止", self.configCard) # 备用，主要由 startBtn 切换状态
        self.stopBtn.hide()
        
        self.configLayout.addWidget(self.nameLabel)
        self.configLayout.addWidget(self.nameEdit)
        self.configLayout.addSpacing(20)
        self.configLayout.addWidget(self.durationLabel)
        self.configLayout.addWidget(self.durationSpin)
        self.configLayout.addStretch(1)
        self.configLayout.addWidget(self.startBtn)
        
        self.vBoxLayout.addWidget(self.configCard)
        
        # --- Status & Log ---
        self.statusLabel = StrongBodyLabel("就绪", self)
        self.vBoxLayout.addWidget(self.statusLabel)
        
        self.logDisplay = QPlainTextEdit(self)
        self.logDisplay.setReadOnly(True)
        self.logDisplay.setPlaceholderText("等待开始...")
        font = self.logDisplay.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.logDisplay.setFont(font)
        
        self.vBoxLayout.addWidget(self.logDisplay)
        
        self.thread = None

    def toggleCapture(self):
        if self.thread and self.thread.isRunning():
            # Stop
            self.thread.stop()
            self.startBtn.setEnabled(False)
            self.startBtn.setText("正在停止...")
        else:
            # Start
            action_name = self.nameEdit.text()
            duration = self.durationSpin.value()
            
            self.logDisplay.clear()
            self.logDisplay.appendPlainText(f"启动持续采集... (Duration: {duration}s)")
            
            self.thread = ContinuousCollectThread(
                self.parent_interface.dataCollector,
                action_name,
                duration,
                self
            )
            self.thread.progress_update.connect(self.onProgress)
            self.thread.saved.connect(self.onSaved)
            self.thread.error.connect(self.onError)
            self.thread.finished.connect(self.onFinished)
            
            self.thread.start()
            self.startBtn.setText("停止采集")
            self.nameEdit.setEnabled(False)
            self.durationSpin.setEnabled(False)

    def onProgress(self, data):
        t = data["time"]
        fc = data["frame_count"]
        epc = data["last_epc"]
        self.statusLabel.setText(f"采集进行中: {t:.1f}s | 帧数: {fc}")
        self.logDisplay.appendPlainText(f"[{t:.1f}s] Frame: {fc}, Last EPC: {epc}")
        sb = self.logDisplay.verticalScrollBar()
        sb.setValue(sb.maximum())

    def onSaved(self, path):
        self.logDisplay.appendPlainText(f"\n[成功] 文件已保存: {path}")
        InfoBar.success(
            title='采集完成',
            content=f"数据已保存至 {path}",
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000
        )

    def onError(self, msg):
        self.logDisplay.appendPlainText(f"\n[错误] {msg}")
        InfoBar.error(
            title='采集出错',
            content=msg,
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT
        )

    def onFinished(self):
        self.startBtn.setText("开始采集")
        self.startBtn.setEnabled(True)
        self.nameEdit.setEnabled(True)
        self.durationSpin.setEnabled(True)
        self.statusLabel.setText("就绪")


class SingleShotInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_interface = parent
        self.collected_points = [] # List of {label, data}
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(15)
        
        # --- Action Name ---
        self.topLayout = QHBoxLayout()
        self.actionNameEdit = LineEdit(self)
        self.actionNameEdit.setPlaceholderText("本次采集任务名称 (用于文件名)")
        self.topLayout.addWidget(BodyLabel("任务名称:", self))
        self.topLayout.addWidget(self.actionNameEdit)
        self.topLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.topLayout)

        # --- Point Control Card ---
        self.ctrlCard = CardWidget(self)
        self.ctrlCard.setFixedHeight(80)
        self.ctrlLayout = QHBoxLayout(self.ctrlCard)
        self.ctrlLayout.setContentsMargins(20, 10, 20, 10)
        
        self.ptLabel = BodyLabel("当前点标签:", self.ctrlCard)
        self.ptEdit = LineEdit(self.ctrlCard)
        self.ptEdit.setPlaceholderText("如: P1, Loc_A")
        
        self.ptDurLabel = BodyLabel("时长(s):", self.ctrlCard)
        self.ptDurSpin = SpinBox(self.ctrlCard)
        self.ptDurSpin.setRange(1, 10)
        self.ptDurSpin.setValue(3)
        
        self.captureBtn = PrimaryPushButton("采集该点", self.ctrlCard)
        self.captureBtn.clicked.connect(self.capturePoint)
        
        self.finishBtn = PrimaryPushButton("完成并保存", self.ctrlCard)
        self.finishBtn.clicked.connect(self.finishSession)
        
        self.ctrlLayout.addWidget(self.ptLabel)
        self.ctrlLayout.addWidget(self.ptEdit)
        self.ctrlLayout.addWidget(self.ptDurLabel)
        self.ctrlLayout.addWidget(self.ptDurSpin)
        self.ctrlLayout.addStretch(1)
        self.ctrlLayout.addWidget(self.captureBtn)
        self.ctrlLayout.addSpacing(10)
        self.ctrlLayout.addWidget(self.finishBtn)
        
        self.vBoxLayout.addWidget(self.ctrlCard)
        
        # --- Table ---
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "标签 (Label)", "捕获EPC数", "预览 (Top 1)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vBoxLayout.addWidget(self.table)
        
        self.thread = None
        self.stateTooltip = None

    def capturePoint(self):
        if self.thread and self.thread.isRunning():
            return
            
        label = self.ptEdit.text().strip()
        if not label:
            label = f"Point_{len(self.collected_points) + 1}"
            
        duration = self.ptDurSpin.value()
        
        self.captureBtn.setEnabled(False)
        self.finishBtn.setEnabled(False)
        
        self.thread = SingleShotCollectThread(
            self.parent_interface.dataCollector,
            label,
            duration,
            self
        )
        self.thread.capture_finished.connect(self.onPointCaptured)
        self.thread.error.connect(self.onError)
        self.thread.start()
        
        if self.window():
            self.stateTooltip = StateToolTip('正在采集', f'正在采集点: {label}...', self.window())
            self.stateTooltip.move(self.stateTooltip.x(), 50)
            self.stateTooltip.show()

    def onPointCaptured(self, data, label):
        self.captureBtn.setEnabled(True)
        self.finishBtn.setEnabled(True)
        
        if self.stateTooltip:
            self.stateTooltip.setContent('采集完成')
            self.stateTooltip.setState(True)
            self.stateTooltip = None
            
        if not data:
            InfoBar.warning(
                title='无数据',
                content='未检测到任何标签',
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT
            )
            return

        # Store data
        self.collected_points.append({
            "label": label,
            "data": data # {epc: [rssi, ...]}
        })
        
        # Update Table
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(label))
        self.table.setItem(row, 2, QTableWidgetItem(str(len(data))))
        
        # Preview
        first_epc = list(data.keys())[0]
        rssi_vals = data[first_epc]
        avg = sum(rssi_vals)/len(rssi_vals) if rssi_vals else 0
        preview = f"{first_epc[-4:]} ({avg:.1f})"
        self.table.setItem(row, 3, QTableWidgetItem(preview))
        
        # Auto increment label
        if label.startswith("Point_") or label[-1].isdigit():
             # Simple heuristic
             pass 
        self.ptEdit.setText("")
        self.ptEdit.setFocus()

    def onError(self, msg):
        self.captureBtn.setEnabled(True)
        self.finishBtn.setEnabled(True)
        if self.stateTooltip:
            self.stateTooltip.setState(True)
            self.stateTooltip = None
        InfoBar.error(title='错误', content=msg, parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def finishSession(self):
        if not self.collected_points:
            InfoBar.warning(title='无数据', content='列表为空，无法保存', parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
            return
            
        try:
            today = datetime.now().strftime("%Y%m%d")
            out_dir = Path(self.parent_interface.dataCollector.config.output_dir) / today / "single_shot_mode"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            action_name = self.actionNameEdit.text().strip()
            base_name = f"singleshot_{action_name}" if action_name else "singleshot"
            
            file_path = out_dir / f"{base_name}.csv"
            i = 2
            while file_path.exists():
                file_path = out_dir / f"{base_name}_v{i}.csv"
                i += 1
                
            # Collect all known EPCs
            all_epcs = set()
            for pt in self.collected_points:
                all_epcs.update(pt["data"].keys())
            sorted_epcs = sorted(list(all_epcs))
            
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                
                # Header
                header = ["ID", "Label"]
                for epc in sorted_epcs:
                    header.extend([f"{epc}_v1", f"{epc}_v2", f"{epc}_v3", f"{epc}_Avg"])
                w.writerow(header)
                
                # Rows
                for idx, pt in enumerate(self.collected_points):
                    row = [idx + 1, pt["label"]]
                    data = pt["data"]
                    for epc in sorted_epcs:
                        vals = data.get(epc, [])
                        # Pad to 3
                        vals = (vals + [0, 0, 0])[:3]
                        avg = sum(vals) / 3
                        row.extend(vals)
                        row.append(f"{avg:.2f}")
                    w.writerow(row)
            
            InfoBar.success(
                title='保存成功',
                content=f"已保存 {len(self.collected_points)} 个点至 {file_path}",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000
            )
            
            # Reset
            self.collected_points.clear()
            self.table.setRowCount(0)
            self.actionNameEdit.setText("")
            
        except Exception as e:
            InfoBar.error(title='保存失败', content=str(e), parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

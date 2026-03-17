# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit
from qfluentwidgets import (
    SubtitleLabel,
    CardWidget,
    StrongBodyLabel,
    PrimaryPushButton,
    SpinBox,
    BodyLabel,
    StateToolTip,
    InfoBar,
    InfoBarPosition
)
from core.settings import ConfigManager
from ..threads import InventoryThread

class DiagnosticsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("diagnosticsInterface")
        self.config = ConfigManager()
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # Header
        self.titleLabel = SubtitleLabel("系统诊断", self)
        self.vBoxLayout.addWidget(self.titleLabel)

        # Control Card
        self.controlCard = CardWidget(self)
        self.controlCard.setFixedHeight(80)
        self.controlCardLayout = QHBoxLayout(self.controlCard)
        self.controlCardLayout.setContentsMargins(20, 10, 20, 10)
        self.controlCardLayout.setSpacing(15)

        self.cardTitle = StrongBodyLabel("读写器连接检查", self.controlCard)
        
        self.startBtn = PrimaryPushButton("开始检查", self.controlCard)
        self.startBtn.clicked.connect(self.toggleCheck)

        self.controlCardLayout.addWidget(self.cardTitle)
        self.controlCardLayout.addStretch(1)
        self.controlCardLayout.addWidget(self.startBtn)

        self.vBoxLayout.addWidget(self.controlCard)

        # Log Display
        self.logDisplay = QPlainTextEdit(self)
        self.logDisplay.setReadOnly(True)
        self.logDisplay.setPlaceholderText("等待开始检查...")
        # Use a monospace font
        font = self.logDisplay.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.logDisplay.setFont(font)
        
        self.vBoxLayout.addWidget(self.logDisplay)

        self.thread = None
        self.stateTooltip = None

    def toggleCheck(self):
        if self.thread and self.thread.isRunning():
            # Stop
            self.thread.stop()
            self.startBtn.setEnabled(False)
            self.startBtn.setText("正在停止...")
            return

        # Start
        self.logDisplay.clear()
        self.logDisplay.appendPlainText(f"正在准备检查... (COM: {self.config.com}, Baud: {self.config.baud})")
        
        self.startBtn.setText("停止检查")
        
        self.thread = InventoryThread(
            self.config.com, 
            self.config.baud, 
            parent=self
        )
        self.thread.epc_received.connect(self.onEpcReceived)
        self.thread.status_changed.connect(self.onStatusChanged)
        self.thread.error_occurred.connect(self.onError)
        self.thread.finished_check.connect(self.onFinished)
        
        self.thread.start()
        
        # Show state tooltip
        if self.window():
            self.stateTooltip = StateToolTip('正在检查', '正在连接读写器...', self.window())
            self.stateTooltip.move(self.stateTooltip.x(), 50)
            self.stateTooltip.show()

    def onEpcReceived(self, text):
        self.logDisplay.appendPlainText(text)
        # Auto scroll
        sb = self.logDisplay.verticalScrollBar()
        sb.setValue(sb.maximum())

    def onStatusChanged(self, text):
        if self.stateTooltip:
            self.stateTooltip.setContent(text)
        self.logDisplay.appendPlainText(f"[系统] {text}")

    def onError(self, text):
        self.logDisplay.appendPlainText(f"[错误] {text}")
        if self.stateTooltip:
            self.stateTooltip.setContent(f"错误: {text}")
            # StateToolTip doesn't have an error state, we just close it or let it be
            self.stateTooltip.setState(True) # Close it
            self.stateTooltip = None
        
        InfoBar.error(
            title='检查出错',
            content=text,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000
        )
        # Enable button
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始检查")

    def onFinished(self):
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始检查")
        if self.stateTooltip:
            self.stateTooltip.setContent('检查完成')
            self.stateTooltip.setState(True)
            self.stateTooltip = None

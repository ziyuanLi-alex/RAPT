from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (
    SubtitleLabel,
    BodyLabel,
    CardWidget,
    IconWidget,
    FluentIcon as FIF,
    PrimaryPushButton,
    StrongBodyLabel,
    InfoBar,
    InfoBarPosition
)

# 引入后端逻辑
from core.settings import ConfigManager
from uhf.reader import GClient

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        
        self.config = ConfigManager()
        # self.config.load() 

        # 主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # 1. 标题头
        self.titleLabel = SubtitleLabel("欢迎使用 RAPT", self)
        self.descLabel = BodyLabel("RFID Analysis & Pose Toolkit - 多模态数据采集与分析平台", self)
        
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.descLabel)

        # 2. 状态卡片区域
        self.statusLayout = QHBoxLayout()
        self.statusLayout.setSpacing(15)
        
        # 读写器状态卡片
        self.readerCard, self.readerStatusLabel, self.readerBtn = self.createStatusCard(
            FIF.IOT, "RFID Reader", "未连接", "检查连接"
        )
        self.readerBtn.clicked.connect(self.checkReaderStatus)

        # 摄像头状态卡片
        self.cameraCard, self.cameraStatusLabel, self.cameraBtn = self.createStatusCard(
            FIF.CAMERA, "Vision Camera", "就绪 (模拟)", "预览"
        )
        self.cameraBtn.setEnabled(False) # 暂时禁用
        
        self.statusLayout.addWidget(self.readerCard)
        self.statusLayout.addWidget(self.cameraCard)
        self.statusLayout.addStretch(1) # 靠左对齐
        
        self.vBoxLayout.addLayout(self.statusLayout)
        self.vBoxLayout.addStretch(1) # 顶上去

    def createStatusCard(self, icon, title, status, btn_text):
        """ 创建一个包含图标、状态和按钮的卡片 """
        card = CardWidget(self)
        card.setFixedSize(280, 100)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 图标
        iconWidget = IconWidget(icon)
        iconWidget.setFixedSize(36, 36)
        
        # 文本区域
        textLayout = QVBoxLayout()
        titleLabel = StrongBodyLabel(title, card)
        statusLabel = BodyLabel(status, card)
        
        # 根据状态变色 (初始化)
        if "未连接" in status:
            statusLabel.setStyleSheet("color: #cfcfcf") # 灰色
        else:
            statusLabel.setStyleSheet("color: #009faa") # 绿色
            
        textLayout.addWidget(titleLabel)
        textLayout.addWidget(statusLabel)
        
        # 按钮
        actionBtn = PrimaryPushButton(btn_text, card)
        actionBtn.setFixedWidth(80)
        
        layout.addWidget(iconWidget)
        layout.addLayout(textLayout)
        layout.addStretch(1)
        layout.addWidget(actionBtn)
        
        return card, statusLabel, actionBtn

    def checkReaderStatus(self):
        """检查读写器连接状态"""
        self.readerBtn.setEnabled(False)
        self.readerBtn.setText("检查中...")
        self.readerStatusLabel.setText("正在连接...")
        
        # 重新加载配置，确保使用最新的 COM 口
        # self.config.load()
        
        # 为了不卡顿 UI，可以在这里使用 QThread，但为了简单演示，先同步执行(因为打开串口通常很快，除非超时)
        # 如果需要更丝滑的体验，建议放入 QThread
        
        try:
            client = GClient()
            if client.openSerial((self.config.com, self.config.baud)):
                self.readerStatusLabel.setText(f"已连接 ({self.config.com})")
                self.readerStatusLabel.setStyleSheet("color: #009faa") # Green
                client.close()
                InfoBar.success(
                    title='连接成功',
                    content=f"成功连接到读写器 {self.config.com}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
            else:
                self.readerStatusLabel.setText("连接失败")
                self.readerStatusLabel.setStyleSheet("color: #d00000") # Red
                InfoBar.error(
                    title='连接失败',
                    content=f"无法打开串口 {self.config.com}，请检查配置或物理连接。",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
        except Exception as e:
            self.readerStatusLabel.setText("错误")
            InfoBar.error(
                title='系统错误',
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
        finally:
            self.readerBtn.setText("检查连接")
            self.readerBtn.setEnabled(True)

# -*- coding: utf-8 -*-
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from qfluentwidgets import (
    ScrollArea, ExpandLayout, SettingCardGroup, SettingCard,
    ComboBoxSettingCard, SwitchSettingCard, PushSettingCard,
    FluentIcon as FIF, InfoBar, LineEdit, SpinBox, ComboBox
)

from core.settings import ConfigManager

class LineEditSettingCard(SettingCard):
    """ 带 LineEdit 的自定义设置卡片 """
    
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.lineEdit = LineEdit(self)
        self.hBoxLayout.addWidget(self.lineEdit, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        # 默认样式
        self.lineEdit.setFixedWidth(150)

class SpinBoxSettingCard(SettingCard):
    """ 带 SpinBox 的自定义设置卡片 """
    
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.spinBox = SpinBox(self)
        self.hBoxLayout.addWidget(self.spinBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class CustomComboBoxSettingCard(SettingCard):
    """ 带 ComboBox 的自定义设置卡片 (修复 AttributeError) """
    
    def __init__(self, icon, title, content=None, texts=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.items = texts or []
        self.comboBox.addItems(self.items)
        self.comboBox.setFixedWidth(150) # 保持宽度一致

    def setValue(self, value):
        self.comboBox.setCurrentText(str(value))


class SettingsInterface(ScrollArea):
    """ 设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.config = ConfigManager()
        self.config.load()
        
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # 设置滚动区域属性
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingsInterface')

        # 初始化UI
        self.__initWidgets()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidgets(self):
        # === 1. 设备连接组 ===
        self.deviceGroup = SettingCardGroup("设备连接", self.scrollWidget)
        
        # COM口 (自定义 LineEdit 卡片)
        self.comCard = LineEditSettingCard(
            FIF.IOT, 
            "串口号 (COM Port)", 
            "输入读写器连接的串口 (如 COM3)"
        )
        self.comCard.lineEdit.setText(self.config.com)
        
        # 波特率
        self.baudCard = CustomComboBoxSettingCard(
            FIF.SPEED_HIGH,
            "波特率 (Baud Rate)",
            "选择读写器通信波特率",
            texts=['9600', '19200', '38400', '57600', '115200'],
            parent=self.deviceGroup
        )
        # 设置当前选中项
        if str(self.config.baud) in self.baudCard.items:
            self.baudCard.setValue(str(self.config.baud))
        else:
            self.baudCard.setValue('115200')

        # === 2. 数据采集组 ===
        self.dataGroup = SettingCardGroup("数据采集", self.scrollWidget)
        
        # 帧长度 (自定义 SpinBox 卡片)
        self.frameCard = SpinBoxSettingCard(
            FIF.STOP_WATCH,
            "帧长度 (ms)",
            "每次读取数据的持续时间 (毫秒)"
        )
        self.frameCard.spinBox.setRange(10, 5000)
        self.frameCard.spinBox.setValue(self.config.frame_duration_ms)

        # 输出格式
        self.formatCard = CustomComboBoxSettingCard(
            FIF.DOCUMENT,
            "输出格式",
            "选择数据保存的文件格式",
            texts=['h5', 'csv', 'both'],
            parent=self.dataGroup
        )
        self.formatCard.setValue(getattr(self.config, 'output_format', 'h5'))

        # 输出目录
        self.dirCard = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "数据输出目录",
            self.config.output_dir,
            self.dataGroup
        )

    def __initLayout(self):
        self.deviceGroup.addSettingCard(self.comCard)
        self.deviceGroup.addSettingCard(self.baudCard)
        
        self.dataGroup.addSettingCard(self.frameCard)
        self.dataGroup.addSettingCard(self.formatCard)
        self.dataGroup.addSettingCard(self.dirCard)

        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        
        self.expandLayout.addWidget(self.deviceGroup)
        self.expandLayout.addWidget(self.dataGroup)

    def __connectSignalToSlot(self):
        # 绑定信号以实现自动保存
        
        # COM
        self.comCard.lineEdit.editingFinished.connect(self.__onComChanged)
        
        # Baud
        self.baudCard.comboBox.currentTextChanged.connect(self.__onBaudChanged)
        
        # Frame
        self.frameCard.spinBox.valueChanged.connect(self.__onFrameChanged)
        
        # Format
        self.formatCard.comboBox.currentTextChanged.connect(self.__onFormatChanged)
        
        # Dir
        self.dirCard.clicked.connect(self.__onDirClicked)

    # --- 槽函数 ---

    def __onComChanged(self):
        new_com = self.comCard.lineEdit.text().strip()
        if new_com != self.config.com:
            self.config.com = new_com
            self.config.save()
            self.__showRestartTip()

    def __onBaudChanged(self, text):
        new_baud = int(text)
        if new_baud != self.config.baud:
            self.config.baud = new_baud
            self.config.save()
            self.__showRestartTip()

    def __onFrameChanged(self, value):
        if value != self.config.frame_duration_ms:
            self.config.frame_duration_ms = value
            self.config.save()

    def __onFormatChanged(self, text):
        if text != getattr(self.config, 'output_format', 'h5'):
            self.config.output_format = text
            self.config.save()

    def __onDirClicked(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.config.output_dir
        )
        if directory:
            self.config.output_dir = directory
            self.dirCard.setContent(directory)
            self.config.save()

    def __showRestartTip(self):
        InfoBar.warning(
            title="配置已更新",
            content="部分硬件设置（如串口、波特率）可能需要重启程序或重连设备才能生效。",
            parent=self,
            duration=3000
        )

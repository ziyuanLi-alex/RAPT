# -*- coding: utf-8 -*-
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from qfluentwidgets import (
    ScrollArea, ExpandLayout, SettingCardGroup, SettingCard,
    ComboBoxSettingCard, SwitchSettingCard, PushSettingCard,
    FluentIcon as FIF, InfoBar, LineEdit, SpinBox, ComboBox, PrimaryPushButton,
    StateToolTip, MessageBoxBase, SubtitleLabel, BodyLabel
)

from core.settings import ConfigManager
from utils.serial_utils import get_serial_ports, check_reader_connection, get_serial_ports_details
from ui.threads import PortListThread, PortScannerThread, ConnectionCheckThread

class PortDetailDialog(MessageBoxBase):
    """ 显示串口详细信息的自定义对话框 """
    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("串口详细信息", self)
        self.contentLabel = BodyLabel(content, self)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        
        self.yesButton.setText("关闭")
        self.cancelButton.hide() # 隐藏取消按钮
        self.widget.setMinimumWidth(350)

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
    """ 带 ComboBox 的自定义设置卡片"""
    
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


class ComPortSettingCard(SettingCard):
    """ 带下拉框和验证按钮的串口设置卡片 """
    
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        
        # 扫描按钮
        self.scanBtn = PrimaryPushButton("扫描", self)
        self.scanBtn.setFixedWidth(60)

        # 验证连接按钮
        self.checkBtn = PrimaryPushButton("验证", self)
        self.checkBtn.setFixedWidth(60)
        
        # 详细信息按钮 (图标按钮或普通按钮)
        self.detailBtn = PrimaryPushButton("详情", self)
        self.detailBtn.setFixedWidth(60)

        # 串口下拉框
        self.comboBox = ComboBox(self)
        self.comboBox.setFixedWidth(120)
        self.comboBox.setPlaceholderText("请选择串口") 
        
        self.hBoxLayout.addWidget(self.scanBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.checkBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.detailBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def setPorts(self, ports):
        self.comboBox.clear()
        self.comboBox.addItems(ports)
        
    def setValue(self, value):
        self.comboBox.setCurrentText(str(value))


class SettingsInterface(ScrollArea):
    """ 设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.config = ConfigManager()
        
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
        
        # COM口 (使用 ComPortSettingCard)
        self.comCard = ComPortSettingCard(
            FIF.IOT, 
            "串口号 (COM Port)", 
            "选择读写器连接的串口"
        )
        
        # 初始化线程但不启动
        self.listThread = PortListThread()
        self.listThread.finished.connect(self.__onPortListLoaded)
        
        # 仅加载配置中的端口
        if self.config.com:
            self.comCard.comboBox.addItem(self.config.com)
            self.comCard.setValue(self.config.com)
        
        # 波特率
        self.baudCard = CustomComboBoxSettingCard(
            FIF.SPEED_HIGH,
            "波特率 (Baud Rate)",
            "选择读写器通信波特率",
            texts=['9600', '19200', '38400', '57600', '115200', '230400', '460800'],
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

        # === 3. SkellyCam 集成组 ===
        self.skellycamGroup = SettingCardGroup("SkellyCam 集成", self.scrollWidget)

        self.skellycamUrlCard = LineEditSettingCard(
            FIF.IOT,
            "SkellyCam 地址",
            "SkellyCam HTTP API base URL",
            self.skellycamGroup,
        )
        self.skellycamUrlCard.lineEdit.setFixedWidth(320)
        self.skellycamUrlCard.lineEdit.setText(self.config.skellycam_base_url)

        self.skellycamDirCard = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "SkellyCam 录制目录",
            self.config.skellycam_recording_dir,
            self.skellycamGroup,
        )

    def __initLayout(self):
        self.deviceGroup.addSettingCard(self.comCard)
        self.deviceGroup.addSettingCard(self.baudCard)
        
        self.dataGroup.addSettingCard(self.frameCard)
        self.dataGroup.addSettingCard(self.formatCard)
        self.dataGroup.addSettingCard(self.dirCard)

        self.skellycamGroup.addSettingCard(self.skellycamUrlCard)
        self.skellycamGroup.addSettingCard(self.skellycamDirCard)

        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        
        self.expandLayout.addWidget(self.deviceGroup)
        self.expandLayout.addWidget(self.dataGroup)
        self.expandLayout.addWidget(self.skellycamGroup)

    def __connectSignalToSlot(self):
        # 绑定信号以实现自动保存
        
        # COM
        self.comCard.comboBox.currentTextChanged.connect(self.__onComChanged)
        self.comCard.scanBtn.clicked.connect(self.__onScanPorts) # 绑定扫描按钮
        self.comCard.checkBtn.clicked.connect(self.__onCheckConnection)
        self.comCard.detailBtn.clicked.connect(self.__onShowPortDetails)
        
        # Baud
        self.baudCard.comboBox.currentTextChanged.connect(self.__onBaudChanged)
        
        # Frame
        self.frameCard.spinBox.valueChanged.connect(self.__onFrameChanged)
        
        # Format
        self.formatCard.comboBox.currentTextChanged.connect(self.__onFormatChanged)
        
        # Dir
        self.dirCard.clicked.connect(self.__onDirClicked)

        # SkellyCam
        self.skellycamUrlCard.lineEdit.editingFinished.connect(self.__onSkellyCamUrlChanged)
        self.skellycamDirCard.clicked.connect(self.__onSkellyCamDirClicked)

    # --- 槽函数 ---

    def __onScanPorts(self):
        self.comCard.comboBox.clear()
        self.comCard.comboBox.setPlaceholderText("扫描中...")
        self.listThread.start()

    def __onComChanged(self, text):
        new_com = text.strip()
        if new_com != self.config.com and new_com != "无可用串口":
            self.config.com = new_com
            self.config.save()
            self.__showRestartTip()

    def __onCheckConnection(self):
        current_port = self.comCard.comboBox.currentText()
        if not current_port or current_port == "无可用串口" or current_port == "扫描中...":
            InfoBar.warning(
                title="无法验证",
                content="请先选择一个有效的串口。",
                parent=self,
                duration=3000
            )
            return

        # 1. 显示顶部加载提示
        self.stateTooltip = StateToolTip('正在验证连接', '请稍候...', self.window())
        self.stateTooltip.move(
            (self.window().width() - self.stateTooltip.width()) // 2, 
            50
        )
        self.stateTooltip.show()

        # 2. 仅禁用按钮，不改文字
        self.comCard.checkBtn.setEnabled(False)
        
        # 启动验证线程
        self.checkThread = ConnectionCheckThread(current_port, self.config.baud)
        self.checkThread.finished.connect(self.__onConnectionChecked)
        self.checkThread.start()

    def __onConnectionChecked(self, is_connected, port):
        # 1. 关闭 StateToolTip
        if self.stateTooltip:
            self.stateTooltip.setContent('验证完成')
            self.stateTooltip.setState(True) # 设置为完成状态
            self.stateTooltip = None 

        if is_connected:
            InfoBar.success(
                title="连接成功",
                content=f"成功连接到设备: {port}",
                parent=self,
                duration=3000
            )
        else:
            InfoBar.error(
                title="连接失败",
                content=f"无法连接到 {port}，请检查设备或波特率设置。",
                parent=self,
                duration=3000
            )
            
        # 2. 仅恢复按钮可用，不重置文字
        self.comCard.checkBtn.setEnabled(True)

    def __onShowPortDetails(self):
        # 1. 显示加载提示
        self.stateTooltip = StateToolTip('正在获取系统串口信息', '请稍候...', self.window())
        self.stateTooltip.move(
            (self.window().width() - self.stateTooltip.width()) // 2, 
            50
        )
        self.stateTooltip.show()

        # 2. 启动扫描线程
        self.scannerThread = PortScannerThread()
        self.scannerThread.finished.connect(self.__onScanFinished)
        self.scannerThread.start()

    def __onScanFinished(self, ports):
        # 3. 准备内容
        content = "系统中未发现可用串口。"
        if ports:
            lines = []
            for p in ports:
                lines.append(f"设备: {p.device}")
                lines.append(f"描述: {p.description}")
                lines.append(f"硬件ID: {p.hwid}")
                lines.append("-" * 30)
            content = "\n".join(lines)

        # 4. 关闭加载提示并显示对话框
        if self.stateTooltip:
            self.stateTooltip.setContent('获取成功')
            self.stateTooltip.setState(True)
            self.stateTooltip = None 

        w = PortDetailDialog(content, self)
        w.exec()

    def __onPortListLoaded(self, ports):
        if not ports:
            ports = ["无可用串口"]
        self.comCard.setPorts(ports)
        
        # 如果配置中的串口不在列表中，也加进去
        if self.config.com and self.config.com not in ports:
            self.comCard.comboBox.addItem(self.config.com)
            
        self.comCard.setValue(self.config.com)

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

    def __onSkellyCamUrlChanged(self):
        value = self.skellycamUrlCard.lineEdit.text().strip()
        if value and value != self.config.skellycam_base_url:
            self.config.skellycam_base_url = value
            self.config.save()

    def __onSkellyCamDirClicked(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择 SkellyCam 录制目录", self.config.skellycam_recording_dir
        )
        if directory:
            self.config.skellycam_recording_dir = directory
            self.skellycamDirCard.setContent(directory)
            self.config.save()

    def __showRestartTip(self):
        InfoBar.warning(
            title="配置已更新",
            content="部分硬件设置（如串口、波特率）可能需要重启程序或重连设备才能生效。",
            parent=self,
            duration=3000
        )

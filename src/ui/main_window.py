import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import logging
from core.settings import ConfigManager # 引入 ConfigManager

logging.getLogger().setLevel(logging.WARNING)

from qfluentwidgets import (
    FluentWindow, 
    NavigationItemPosition, 
    FluentIcon as FIF,
    SplashScreen
)
from ui.i18n import t

from .views import (
    HomeInterface,
    CollectInterface,
    SettingsInterface,
    DiagnosticsInterface,
    TagsInterface,
    VideoInterface,
    IntegratedInterface,
)


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 全局加载配置
        self.config = ConfigManager()
        self.config.load()
        
        logging.info("MainWindow constructor called")
        self.initWindow()
        logging.info("MainWindow initialized")
        # 移除了这里的重复设置，统一在 initWindow 中处理，或直接依赖 QApplication 的图标
        # self.setWindowIcon(QIcon('resources/RAPT_icon.png')) 

        # 1. 初始化子页面
        self.homeInterface = HomeInterface(self)
        self.collectInterface = CollectInterface(self)
        self.tagsInterface = TagsInterface(self)
        self.videoInterface = VideoInterface(self)
        self.integratedInterface = IntegratedInterface(self)
        self.diagnosticsInterface = DiagnosticsInterface(self)
        self.settingsInterface = SettingsInterface(self)

        # 2. 初始化导航栏
        self.initNavigation()
        logging.info("Navigation initialized")


    def initWindow(self):
        self.setWindowTitle(t("app.window_title", self.config))
        self.setMinimumSize(1100, 720)

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        target_w, target_h = int(w * 0.68), int(h * 0.68)
        self.resize(target_w, target_h)
        self.move(w // 2 - target_w // 2, h // 2 - target_h // 2)

    def initNavigation(self):
        # --- 顶部导航区域 ---
        
        # 首页 / 仪表盘
        self.addSubInterface(
            self.homeInterface,
            FIF.HOME,
            t("nav.home", self.config),
            NavigationItemPosition.TOP
        )
        logging.info("Home interface added to navigation")  

        self.addSubInterface(
            self.collectInterface,
            FIF.PLAY, # 或者用 VIDEO 图标
            t("nav.collect", self.config),
            NavigationItemPosition.TOP
        )
        logging.info("Collect interface added to navigation")  

        # 标签管理 (对应原 CLI 的 "标签绑定管理")
        self.addSubInterface(
            self.tagsInterface,
            FIF.TAG,
            t("nav.tags", self.config),
            NavigationItemPosition.TOP
        )

        self.addSubInterface(
            self.videoInterface,
            FIF.CAMERA,
            t("nav.video", self.config),
            NavigationItemPosition.TOP
        )

        self.addSubInterface(
            self.integratedInterface,
            FIF.PLAY,
            t("nav.integrated", self.config),
            NavigationItemPosition.TOP
        )

        # --- 底部导航区域 ---
        
        # 系统诊断
        self.addSubInterface(
            self.diagnosticsInterface,
            FIF.HEART,
            t("nav.diagnostics", self.config),
            NavigationItemPosition.TOP
        )

        # 系统设置
        self.addSubInterface(
            self.settingsInterface,
            FIF.SETTING,
            t("nav.settings", self.config),
            NavigationItemPosition.BOTTOM
        )

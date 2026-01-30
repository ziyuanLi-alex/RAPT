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

from .views import HomeInterface, CollectInterface, SettingsInterface


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
        self.settingsInterface = SettingsInterface(self)
        # self.tagsInterface = TagsInterface(self)

        # 2. 初始化导航栏
        self.initNavigation()
        logging.info("Navigation initialized")


    def initWindow(self):
        self.resize(1100, 750)
        self.setWindowTitle('RAPT - RFID Analysis & Pose Toolkit')
        
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def initNavigation(self):
        # --- 顶部导航区域 ---
        
        # 首页 / 仪表盘
        self.addSubInterface(
            self.homeInterface,
            FIF.HOME,
            "总览 (Dashboard)",
            NavigationItemPosition.TOP
        )
        logging.info("Home interface added to navigation")  

        self.addSubInterface(
            self.collectInterface,
            FIF.PLAY, # 或者用 VIDEO 图标
            "采集监控 (Monitor)",
            NavigationItemPosition.TOP
        )
        logging.info("Collect interface added to navigation")  

        # 标签管理 (对应原 CLI 的 "标签绑定管理")
        # self.addSubInterface(
        #     self.tagsInterface,
        #     FIF.TAG,
        #     "标签管理 (Tags)",
        #     NavigationItemPosition.TOP
        # )

        # --- 底部导航区域 ---
        
        # 系统设置
        self.addSubInterface(
            self.settingsInterface,
            FIF.SETTING,
            "设置 (Settings)",
            NavigationItemPosition.BOTTOM
        )
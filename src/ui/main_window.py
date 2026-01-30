from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import logging
logging.getLogger().setLevel(logging.INFO)

from qfluentwidgets import (
    FluentWindow, 
    NavigationItemPosition, 
    FluentIcon as FIF,
    SplashScreen
)

from .views import HomeInterface, CollectInterface


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        logging.info("MainWindow constructor called")
        self.initWindow()
        logging.info("MainWindow initialized")

        # 1. 初始化子页面
        self.homeInterface = HomeInterface(self)
        self.collectInterface = CollectInterface(self)
        # self.tagsInterface = TagsInterface(self)
        # self.settingsInterface = SettingsInterface(self)

        # 2. 初始化导航栏
        self.initNavigation()
        logging.info("Navigation initialized")
        
        # 3. 启动画面 (可选，显得更专业)
        # self.splashScreen = SplashScreen(self.windowIcon(), self)
        # self.splashScreen.setIconSize(QSize(100, 100))
        # self.show()
        
        # 模拟加载耗时操作，然后关闭启动画面
        # QApplication.processEvents()
        # self.splashScreen.finish()

    def initWindow(self):
        self.resize(1100, 750)
        self.setWindowTitle('RAPT')
        # 设置窗口图标，建议找一个 .ico 文件
        # self.setWindowIcon(QIcon('resources/icon.png')) 
        
        # 居中显示
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

        # 数据采集 (对应原 CLI 的 "开始数据采集")
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
        # self.addSubInterface(
        #     self.settingsInterface,
        #     FIF.SETTING,
        #     "设置 (Settings)",
        #     NavigationItemPosition.BOTTOM
        # )
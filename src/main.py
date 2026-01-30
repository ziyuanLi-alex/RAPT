import sys
import os
import logging
logging.getLogger().setLevel(logging.INFO)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

if __name__ == '__main__':
    logging.info("RAPT application started")
    # 2. 设置高分屏属性 (建议保留，否则在 Win10/11 上界面会模糊)
    # 这些必须在创建 QApplication 之前设置
    # QApplication.setHighDpiScaleFactorRoundingPolicy(
    #     Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # 3. 【关键步骤】创建 QApplication 实例
    # 这一步必须在任何 Widget 被加载或创建之前完成！

    app = QApplication(sys.argv)
    logging.info("QApplication created")
    
    # 4. 设置主题
    setTheme(Theme.AUTO)
    logging.info("Theme set to AUTO")

    # 5. 【修复核心】延迟导入 MainWindow
    # 只有当 app 跑起来之后，再去加载 UI 文件
    # 这样可以防止 UI 文件里的静态对象在 App 创建前就初始化导致崩溃
    from ui.main_window import MainWindow
    logging.info("MainWindow imported")

    # 6. 显示窗口
    w = MainWindow()
    logging.info("MainWindow instance created")
    w.show()
    
    # 7. 进入事件循环
    sys.exit(app.exec())
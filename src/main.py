import sys
import os
import ctypes
import logging
logging.getLogger().setLevel(logging.WARNING)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from qfluentwidgets import setTheme, Theme

from ui.main_window import MainWindow
from core.paths import resource_path

if __name__ == '__main__':
    logging.info("RAPT application started")

    try:
        myappid = 'edu.sustech.eee.RAPT.v0.0.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except (AttributeError, OSError):
        pass

    icon_path = resource_path("resources", "RAPT_icon.png")

    app = QApplication(sys.argv)
    
    # 设置应用图标
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        logging.warning(f"Icon not found at {icon_path}")

    logging.info("QApplication created")
    
    setTheme(Theme.AUTO)
    logging.info("Theme set to AUTO")


    logging.info("MainWindow imported")

    w = MainWindow()
    logging.info("MainWindow instance created")
    w.show()
    
    sys.exit(app.exec())

# -*- coding: utf-8 -*-
from PyQt6.QtCore import QThread, pyqtSignal
from utils.serial_utils import get_serial_ports, get_serial_ports_details, check_reader_connection

class PortListThread(QThread):
    """ 获取简单串口列表的线程 """
    finished = pyqtSignal(list)

    def run(self):
        ports = get_serial_ports()
        self.finished.emit(ports)

class PortScannerThread(QThread):
    """ 获取详细串口信息的线程 """
    finished = pyqtSignal(list)

    def run(self):
        ports = get_serial_ports_details()
        self.finished.emit(ports)

class ConnectionCheckThread(QThread):
    """ 验证串口连接的线程 """
    finished = pyqtSignal(bool, str) # result, message (optional)

    def __init__(self, port, baud, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud

    def run(self):
        result = check_reader_connection(self.port, self.baud)
        self.finished.emit(result, self.port)

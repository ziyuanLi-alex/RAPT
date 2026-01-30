# -*- coding: utf-8 -*-
from PyQt6.QtCore import QThread, pyqtSignal
from utils.serial_utils import get_serial_ports, get_serial_ports_details, check_reader_connection
import time
from uhf.reader import GClient, MsgBaseInventoryEpc, MsgBaseStop, EnumG, LogBaseEpcInfo

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

class InventoryThread(QThread):
    """ 盘点测试线程 """
    epc_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    finished_check = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, port, baud, duration=3, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self.duration = duration
        self.is_running = False
        self.client = None

    def run(self):
        self.is_running = True
        self.client = GClient()
        
        try:
            self.status_changed.emit(f"正在连接 {self.port}...")
            if not self.client.openSerial((self.port, self.baud)):
                self.error_occurred.emit(f"无法打开串口 {self.port}")
                return

            self.client.callEpcInfo = self._on_epc_received
            
            self.status_changed.emit("开始盘点...")
            msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                      inventoryMode=EnumG.InventoryMode_Inventory.value)
            
            if self.client.sendSynMsg(msg) == 0:
                start_time = time.time()
                while self.is_running and (time.time() - start_time < self.duration):
                    self.msleep(100)
                
                self.status_changed.emit("停止盘点...")
                stop = MsgBaseStop()
                self.client.sendSynMsg(stop)
            else:
                self.error_occurred.emit("发送盘点指令失败")

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if self.client:
                self.client.close()
            self.status_changed.emit("检查完成")
            self.finished_check.emit()

    def _on_epc_received(self, epc_info):
        if epc_info.result == 0:
            text = f"Read EPC: {epc_info.epc}, RSSI: {epc_info.rssi}"
            self.epc_received.emit(text)

    def stop(self):
        self.is_running = False

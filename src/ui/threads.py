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

    def __init__(self, port, baud, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
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
                while self.is_running:
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

class TagScanThread(QThread):
    """ 扫描附近标签线程 (用于绑定管理) """
    tags_found = pyqtSignal(list) # [epc1, epc2, ...]
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 1.0 # 默认扫描1秒

    def run(self):
        try:
            client = GClient()
            found_epcs = set()
            
            def on_epc(epc_info):
                if epc_info.result == 0:
                    found_epcs.add(epc_info.epc)
            
            # 使用默认配置尝试打开串口
            # 这里我们无法直接获取 config，所以假设外部已经配好了，或者需要从 ConfigManager 获取
            # 为了简单起见，我们假设调用方确保串口可用，或者这里使用 ConfigManager
            from core.settings import ConfigManager
            config = ConfigManager()
            
            if not client.openSerial((config.com, config.baud)):
                self.error.emit(f"无法打开串口 {config.com}")
                return
                
            client.callEpcInfo = on_epc
            
            msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                      inventoryMode=EnumG.InventoryMode_Inventory.value)
            
            if client.sendSynMsg(msg) == 0:
                time.sleep(self.duration)
                stop = MsgBaseStop()
                client.sendSynMsg(stop)
                
            client.close()
            self.tags_found.emit(list(found_epcs))
            
        except Exception as e:
            self.error.emit(str(e))

class ContinuousCollectThread(QThread):
    """ 持续采集线程 (对应原线形模式) """
    progress_update = pyqtSignal(dict) # {time, frame_count, last_epc}
    saved = pyqtSignal(str) # file_path
    error = pyqtSignal(str)
    
    def __init__(self, data_collector, action_name, duration=0, parent=None):
        super().__init__(parent)
        self.dc = data_collector
        self.action_name = action_name
        self.duration = duration
        self.is_running = False

    def run(self):
        self.is_running = True
        try:
            # 导入 DataCollector 相关依赖
            from collections import defaultdict
            import statistics
            import csv
            import os
            from pathlib import Path
            from datetime import datetime

            stream = self.dc.stream()
            
            start_t = time.time()
            buckets = defaultdict(lambda: defaultdict(list))
            frame_span = 0.1
            frame_count = 0
            
            # 使用 queue 来非阻塞读取 stream
            from queue import Queue, Empty
            import threading
            q = Queue(maxsize=10000)
            stop_sentinel = object()
            
            def feeder():
                try:
                    for raw in stream:
                        q.put(raw)
                        if not self.is_running: break
                except Exception:
                    pass
                finally:
                    q.put(stop_sentinel)
            
            feeder_thread = threading.Thread(target=feeder, daemon=True)
            feeder_thread.start()
            
            while self.is_running:
                # 检查时长限制
                elapsed = time.time() - start_t
                if self.duration > 0 and elapsed >= self.duration:
                    break
                
                try:
                    item = q.get(timeout=0.1)
                except Empty:
                    continue
                    
                if item is stop_sentinel:
                    break
                    
                # 处理数据
                ts = float(item.get("ts", time.time()))
                epc = str(item["epc"])
                rssi = float(item.get("rssi", item.get("intensity", 0)))
                
                idx = int((ts - start_t) / frame_span)
                if idx < 0: idx = 0
                buckets[epc][idx].append(rssi)
                frame_count += 1
                
                # 更新 UI (降频)
                if frame_count % 5 == 0:
                    self.progress_update.emit({
                        "time": elapsed,
                        "frame_count": frame_count,
                        "last_epc": epc
                    })
            
            # 停止采集
            self.dc.stop_stream()
            feeder_thread.join(timeout=1.0)
            
            # 保存数据
            if not buckets:
                self.error.emit("未采集到数据")
                return

            # 数据后处理
            total_span = elapsed
            end_idx = max(1, int(total_span / frame_span))
            epc_order = list(buckets.keys())
            per_epc_rows = {}
            
            for epc in epc_order:
                rows = []
                table = buckets[epc]
                for fidx in range(end_idx):
                    vals = table.get(fidx, [])
                    t_rel = round((fidx + 1) * frame_span, 6)
                    if vals:
                        sv = sorted(vals)
                        n = len(sv)
                        median = sv[n // 2] if n % 2 == 1 else 0.5 * (sv[n // 2 - 1] + sv[n // 2])
                        cnt, vmax, mean = n, max(vals), sum(vals) / n
                    else:
                        median = cnt = vmax = mean = 0.0
                    rows.append((t_rel, median, cnt, vmax, mean))
                per_epc_rows[epc] = rows

            # 生成文件路径
            today = datetime.now().strftime("%Y%m%d")
            out_dir = Path(self.dc.config.output_dir) / today / "continuous_mode"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            parts = ["continuous"]
            if self.duration > 0: parts.append("timed")
            if self.action_name: parts.append(self.action_name.strip())
            base_name = "_".join(parts)
            
            file_path = out_dir / f"{base_name}.csv"
            # 简单去重命名逻辑
            i = 2
            while file_path.exists():
                file_path = out_dir / f"{base_name}_v{i}.csv"
                i += 1
            
            # 写入 CSV
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                # 简单表头，不依赖 BindingManager (UI 层可处理展示，文件保留原始数据)
                header_row = []
                for epc in epc_order:
                    header_row.extend([f"{epc}_Time", f"{epc}_Median", f"{epc}_Count", f"{epc}_Max", f"{epc}_Mean", ""])
                w.writerow(header_row)
                
                for r in range(end_idx):
                    row = []
                    for epc in epc_order:
                        row.extend(list(per_epc_rows[epc][r]))
                        row.append("") # Spacer
                    w.writerow(row)
            
            self.saved.emit(str(file_path))
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False


class SingleShotCollectThread(QThread):
    """ 单次采集线程 (对应原点形模式的一次 Trigger) """
    capture_finished = pyqtSignal(dict, str) # {epc: [rssi, ...]}, point_label
    error = pyqtSignal(str)

    def __init__(self, data_collector, point_label, duration=3.0, parent=None):
        super().__init__(parent)
        self.dc = data_collector
        self.point_label = point_label
        self.duration = duration

    def run(self):
        try:
            from collections import defaultdict
            import threading
            from queue import Queue, Empty
            
            stream = self.dc.stream()
            q = Queue(maxsize=10000)
            stop_sentinel = object()
            
            def feeder():
                try:
                    for raw in stream:
                        q.put(raw)
                finally:
                    q.put(stop_sentinel)
            
            feeder_thread = threading.Thread(target=feeder, daemon=True)
            feeder_thread.start()
            
            start_t = time.time()
            collected = defaultdict(list)
            
            while time.time() - start_t <= self.duration:
                try:
                    item = q.get(timeout=0.1)
                    if item is stop_sentinel:
                        break
                    
                    epc = str(item.get("epc", "")).strip()
                    rssi = float(item.get("rssi", item.get("intensity", 0)))
                    
                    # 仅保留每个 EPC 的前 3 个数据点 (参考原逻辑)
                    if len(collected[epc]) < 3:
                        collected[epc].append(rssi)
                        
                except Empty:
                    continue
            
            self.dc.stop_stream()
            feeder_thread.join(timeout=1.0)
            
            # 返回字典
            result = {k: v for k, v in collected.items()}
            self.capture_finished.emit(result, self.point_label)
            
        except Exception as e:
            self.error.emit(str(e))

# -*- coding: utf-8 -*-
import time
import os
from uhf.reader import *
import h5py
import json
import statistics
from collections import defaultdict
import questionary
import csv
import datetime
import contextlib, io
from settings import ConfigManager


class DataCollector:
    """
    从 RFID 读写器采集数据并保存。
    支持输出模式：
      - 'h5'  ：写 HDF5
      - 'csv' ：写 CSV
      - 'both'：同时输出两种格式
    """

    # ---------------------- 串口初始化 ----------------------
    def _ensure_client_open_for_stream(self):
        """确保 gclient 已连接串口，未连则打开。"""
        created = False
        if not hasattr(self, "gclient") or self.gclient is None:
            self.gclient = GClient()
            self.gclient.openSerial((self.config.com, self.config.baud))
            created = True
        else:
            try:
                _ = self.gclient  # 验证连接是否有效
            except Exception:
                self.gclient = GClient()
                self.gclient.openSerial((self.config.com, self.config.baud))
                created = True
        return created

    # ---------------------- 流式采集接口 ----------------------
    def stream(self):
        """
        【数据流生成器】供线形/点形模式调用
        持续产出：
          {"ts": 秒时间戳, "frame_idx": int, "epc": str, "rssi": float, "ant": int}
        """
        from queue import Queue, Empty
        import threading

        if getattr(self, "_stream_running", False):
            raise RuntimeError("stream() 已在运行中")

        # 打开串口
        if not hasattr(self, "gclient") or self.gclient is None:
            self.gclient = GClient()
        if not getattr(self, "_stream_opened_client", False):
            self.gclient.openSerial((self.config.com, self.config.baud))
            self._stream_opened_client = True

        # 天线列表（兜底为 [1]）
        ants = getattr(self.config, "antennas", [1])
        ants = [int(a) for a in ants if str(a).isdigit() and 1 <= int(a) <= 4] or [1]

        ant_enum = []
        for a in ants:
            try:
                ant_enum.append((a, getattr(EnumG, f"AntennaNo_{a}").value))
            except Exception:
                pass
        if not ant_enum:
            ant_enum = [(1, EnumG.AntennaNo_1.value)]

        # 队列与状态
        q: Queue = Queue(maxsize=10000)
        stop_sentinel = object()
        self._stream_queue = q
        self._stream_running = True
        self._stream_thread = None
        frame_idx = 0
        current_ant = {"val": ant_enum[0][0]}

        # 备份原回调
        old_info = self.gclient.callEpcInfo
        old_over = self.gclient.callEpcOver

        # --- EPC 到达回调 ---
        def _cb_epc(epcInfo: LogBaseEpcInfo):
            if not self._stream_running or epcInfo is None or epcInfo.result != 0:
                return
            ant = getattr(epcInfo, "ant", None) or getattr(epcInfo, "antenna", None) \
                or getattr(epcInfo, "antennaNo", None) or getattr(epcInfo, "ant_id", None) \
                or getattr(epcInfo, "Antenna", None)
            try:
                ant = int(ant)
            except Exception:
                ant = current_ant["val"]
            try:
                q.put_nowait({
                    "ts": time.time(),
                    "frame_idx": None,
                    "epc": str(epcInfo.epc),
                    "rssi": float(epcInfo.rssi),
                    "ant": ant,
                })
            except Exception:
                pass

        def _cb_over(_):
            pass  # 不打印多余信息

        self.gclient.callEpcInfo = _cb_epc
        self.gclient.callEpcOver = _cb_over

        # --- 轮询线程：保持 sent/receive 正常显示 ---
        def _poller():
            try:
                while self._stream_running:
                    for a, a_enum in ant_enum:
                        if not self._stream_running:
                            break
                        current_ant["val"] = a
                        msg = MsgBaseInventoryEpc(
                            antennaEnable=a_enum,
                            inventoryMode=EnumG.InventoryMode_Inventory.value,
                        )
                        try:
                            self.gclient.sendSynMsg(msg)
                        except Exception:
                            time.sleep(0.05)
                        time.sleep(0.12)
            finally:
                try:
                    q.put_nowait(stop_sentinel)
                except Exception:
                    pass

        self._stream_thread = threading.Thread(target=_poller, daemon=True)
        self._stream_thread.start()

        # --- 主生成器 ---
        try:
            while self._stream_running:
                try:
                    item = q.get(timeout=0.5)
                except Empty:
                    continue
                if item is stop_sentinel:
                    break
                item["frame_idx"] = frame_idx
                frame_idx += 1
                yield item
        except KeyboardInterrupt:
            pass
        finally:
            # ---- 收尾阶段（静音）----
            self._stream_running = False
            try:
                if self._stream_thread and self._stream_thread.is_alive():
                    self._stream_thread.join(timeout=1.0)
            except Exception:
                pass

            # 清空回调，防止 STOP 打印
            try:
                def _noop(*a, **kw): return None
                self.gclient.callEpcInfo = _noop
                self.gclient.callEpcOver = _noop
            except Exception:
                pass

            # 静音 STOP
            try:
                stop = MsgBaseStop()
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    self.gclient.sendSynMsg(stop)
            except Exception:
                pass

            # 静音关闭串口
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    if getattr(self, "_stream_opened_client", False):
                        self.gclient.close()
            except Exception:
                pass
            finally:
                self._stream_opened_client = False

            time.sleep(0.3)  # 稍等，防止菜单残留输出

    # ---------------------- 停止流采集 ----------------------
    def stop_stream(self):
        """请求停止 stream() 轮询线程。"""
        self._stream_running = False

    # ---------------------- 初始化 ----------------------
    def __init__(self, config: ConfigManager):
        self.config = config
        self.frame_duration_ms = config.frame_duration_ms
        self.frame_duration_sec = self.frame_duration_ms / 1000.0
        self.output_dir = config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # 状态
        self.session_active = False
        self.session_start_time = 0.0
        self.session_action_type = "default"
        self.h5_file = None

        # 帧缓存
        self.current_frame_index = 0
        self.frame_buffer = defaultdict(list)
        self.known_epcs_in_session = set()

        # CSV
        self._csv_rows = []
        self.csv_filepath = None

        # 新模式状态
        self._stream_running = False
        self._stream_thread = None
        self._stream_queue = None
        self._stream_opened_client = False

    # ---------------------- Reader 回调 ----------------------
    def receivedEpc(self, epcInfo: LogBaseEpcInfo):
        if epcInfo.result == 0:
            self.on_data_received(epcInfo.epc, epcInfo.rssi)
            print(epcInfo.epc, end="\r")

    def receivedEpcOver(self, _):
        print("LogBaseEpcOver")

    # ---------------------- 会话控制 ----------------------
    def start_session(self, action_type: str):
        """启动新的数据采集会话"""
        if self.session_active:
            print("警告：已有会话在进行中。")
            return

        print("连接读卡器...")
        self.gclient = GClient()
        self.gclient.openSerial((self.config.com, self.config.baud))
        self.gclient.callEpcInfo = self.receivedEpc
        self.gclient.callEpcOver = self.receivedEpcOver

        print(f"开启新会话：{action_type}")
        self.session_active = True
        self.session_action_type = action_type
        self.session_start_time = time.perf_counter()
        self.current_frame_index = 0
        self.known_epcs_in_session.clear()
        self.frame_buffer.clear()

        h5_enabled = getattr(self.config, "output_format", "h5") in ("h5", "both")
        csv_enabled = getattr(self.config, "output_format", "h5") in ("csv", "both")

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_name = f"{timestamp}_{action_type}"

        # HDF5
        if h5_enabled:
            h5_path = os.path.join(self.output_dir, base_name + ".h5")
            self.h5_file = h5py.File(h5_path, "w")
            self.h5_file.attrs["action_type"] = action_type
            cfg = {k: v for k, v in self.config.__dict__.items() if not k.startswith("_")}
            self.h5_file.attrs["config"] = json.dumps(cfg)
            print(f"保存至 HDF5: {h5_path}")
        else:
            self.h5_file = None

        # CSV
        if csv_enabled:
            self.csv_filepath = os.path.join(self.output_dir, base_name + ".csv")
            if not os.path.exists(self.csv_filepath):
                with open(self.csv_filepath, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["frame_idx", "time_s", "epc", "median", "count", "max"])
            print(f"保存至 CSV: {self.csv_filepath}")

    def stop_session(self):
        """停止采集会话"""
        if not self.session_active:
            return

        print("正在停止会话...")
        try:
            self._process_frame()

            print("停止读卡器...")
            try:
                if hasattr(self, "gclient") and self.gclient:
                    stop = MsgBaseStop()
                    if self.gclient.sendSynMsg(stop) == 0:
                        print(stop.rtMsg)
            finally:
                try:
                    if hasattr(self, "gclient") and self.gclient:
                        self.gclient.close()
                except Exception as e:
                    print(f"关闭读卡器警告: {e}")

            if getattr(self.config, "output_format", "h5") in ("csv", "both"):
                self._flush_csv()
                if getattr(self, "csv_filepath", None):
                    print(f"CSV 已保存至: {self.csv_filepath}")

            if self.h5_file:
                try:
                    self.h5_file.flush()
                except Exception:
                    pass
                self.h5_file.close()

            print("会话已停止，数据已保存。")
        finally:
            self.session_active = False

    # ---------------------- CSV 相关 ----------------------
    def _init_csv(self):
        """创建 CSV 文件（兜底用）"""
        if self.csv_filepath:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{ts}_{self.session_action_type}.csv"
        self.csv_filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(self.csv_filepath):
            with open(self.csv_filepath, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["frame_idx", "time_s", "epc", "median", "count", "max"])

    def _flush_csv(self):
        """写入缓冲区数据"""
        if not self._csv_rows or not self.csv_filepath:
            return
        with open(self.csv_filepath, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerows(self._csv_rows)
        self._csv_rows.clear()

    # ---------------------- 数据处理 ----------------------
    def on_data_received(self, epc: str, rssi: int):
        """接收 EPC 数据"""
        if not self.session_active:
            return
        self.known_epcs_in_session.add(epc)
        elapsed = time.perf_counter() - self.session_start_time
        expected_frame = int(elapsed / self.frame_duration_sec)
        while self.current_frame_index < expected_frame:
            self._process_frame()
            self.current_frame_index += 1
        self.frame_buffer[epc].append(rssi)

    def _process_frame(self):
        """处理并保存一帧数据"""
        if not self.session_active:
            return
        frame_time = self.current_frame_index * self.frame_duration_sec
        h5_enabled = self.h5_file is not None
        csv_enabled = getattr(self.config, "output_format", "h5") in ("csv", "both")
        if csv_enabled and not getattr(self, "csv_filepath", None):
            self._init_csv()

        for epc, lst in self.frame_buffer.items():
            if not lst:
                continue
            cnt, med, vmax = len(lst), statistics.median(lst), max(lst)
            if h5_enabled:
                row = [frame_time, med, cnt, vmax]
                if epc not in self.h5_file:
                    self.h5_file.create_dataset(epc, data=[row], maxshape=(None, 4), chunks=True)
                else:
                    ds = self.h5_file[epc]
                    ds.resize(ds.shape[0] + 1, axis=0)
                    ds[-1] = row
            if csv_enabled:
                self._csv_rows.append([
                    self.current_frame_index, round(frame_time, 3), epc, med, cnt, vmax
                ])

        if h5_enabled:
            for epc in self.known_epcs_in_session:
                if epc in self.frame_buffer:
                    continue
                row = [frame_time, 0, 0, 0]
                if epc not in self.h5_file:
                    self.h5_file.create_dataset(epc, data=[row], maxshape=(None, 4), chunks=True)
                else:
                    ds = self.h5_file[epc]
                    ds.resize(ds.shape[0] + 1, axis=0)
                    ds[-1] = row
        self.frame_buffer.clear()

    # ---------------------- 主入口 ----------------------
    def data_collect_entry(self):
        """旧版采集流程"""
        if not questionary.confirm("要开始数据采集吗？").ask():
            return
        action_type = questionary.text("请输入动作类型：").ask()
        self.start_session(action_type)
        print(f"数据采集已启动（模式：{getattr(self.config, 'output_format', 'h5')}），按 Ctrl+C 停止。")
        try:
            while True:
                msg = MsgBaseInventoryEpc(
                    antennaEnable=EnumG.AntennaNo_1.value,
                    inventoryMode=EnumG.InventoryMode_Inventory.value,
                )
                if self.gclient.sendSynMsg(msg) == 0:
                    print(msg.rtMsg)
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_session()
            print("数据采集已停止。")

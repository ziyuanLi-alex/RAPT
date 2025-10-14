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

from settings import ConfigManager


class DataCollector:
    """
    负责从RFID读写器收集数据，进行分帧、预处理，并以会话形式存储。
    支持三种输出模式（由 config.output_format 决定）：
      - 'h5'  ：仅写 HDF5
      - 'csv' ：仅写 CSV（Excel 直接打开）
      - 'both'：同时写 HDF5 与 CSV
    HDF5 每个 EPC 一个 dataset，行：[frame_time, median, count, max]
    CSV 行：[frame_idx, time_s, epc, median, count, max]
    """
    def __init__(self, config: ConfigManager):
        # --- 从配置中加载参数 ---
        self.config = config
        self.frame_duration_ms = config.frame_duration_ms
        self.frame_duration_sec = self.frame_duration_ms / 1000.0
        self.output_dir = config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # --- 会话状态变量 ---
        self.session_active = False
        self.session_start_time = 0.0
        self.session_action_type = "default"
        self.h5_file = None

        # --- 帧处理相关变量 ---
        self.current_frame_index = 0
        self.frame_buffer = defaultdict(list)   # {epc: [rssi, ...]} 当前帧
        self.known_epcs_in_session = set()      # 会话中出现过的 EPC（用于补零）

        # --- CSV 输出相关 ---
        self._csv_rows = []          # 行缓冲
        self.csv_filepath = None     # CSV 文件路径

    # ---------------------- Reader 回调 ----------------------
    def receivedEpc(self, epcInfo: LogBaseEpcInfo):
        if epcInfo.result == 0:
            self.on_data_received(epcInfo.epc, epcInfo.rssi)
            print(epcInfo.epc, end='\r')  # 简单回显

    def receivedEpcOver(self, epcOver: LogBaseEpcOver):
        print("LogBaseEpcOver")

    # ---------------------- 会话控制 ----------------------
    def start_session(self, action_type: str):
        """
        开始一个新的数据采集会话。
        仅在 output_format 为 'h5' 或 'both' 时创建 HDF5 文件；'csv' 时不建 HDF5。
        """
        if self.session_active:
            print("警告：一个会话已在进行中。请先停止当前会话。")
            return

        print("连接读卡器...")
        # --连接读卡器--
        self.gclient = GClient()
        self.gclient.openSerial((self.config.com, self.config.baud))
        self.gclient.callEpcInfo = self.receivedEpc
        self.gclient.callEpcOver = self.receivedEpcOver

        print(f"开启新会话，动作类型: '{action_type}'")
        self.session_active = True
        self.session_action_type = action_type
        self.session_start_time = time.perf_counter()
        self.current_frame_index = 0
        self.known_epcs_in_session.clear()
        self.frame_buffer.clear()

        # 判定模式
        h5_enabled  = getattr(self.config, "output_format", "h5") in ("h5", "both")
        csv_enabled = getattr(self.config, "output_format", "h5") in ("csv", "both")

        # 基础文件名
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_name = f"{timestamp}_{action_type}"

        # 仅当启用 H5 时才创建 HDF5
        if h5_enabled:
            h5_path = os.path.join(self.output_dir, base_name + ".h5")
            self.h5_file = h5py.File(h5_path, 'w')
            self.h5_file.attrs['action_type'] = action_type
            config_dict = {k: v for k, v in self.config.__dict__.items() if not k.startswith('_')}
            self.h5_file.attrs['config'] = json.dumps(config_dict)
            print(f"数据将保存至 HDF5: {h5_path}")
        else:
            self.h5_file = None  # 明确无 H5

        # 若启用 CSV，则准备 CSV（与 H5 同名改后缀；无 H5 时用 base_name）
        if csv_enabled:
            if self.h5_file is not None:
                self.csv_filepath = self.h5_file.filename.replace(".h5", ".csv")
            else:
                self.csv_filepath = os.path.join(self.output_dir, base_name + ".csv")
            if not os.path.exists(self.csv_filepath):
                with open(self.csv_filepath, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["frame_idx", "time_s", "epc", "median", "count", "max"])
            print(f"数据将保存至 CSV: {self.csv_filepath}")
        else:
            self.csv_filepath = None
            self._csv_rows.clear()

    def stop_session(self):
        """停止当前的数据采集会话。"""
        if not self.session_active:
            return

        print("正在停止会话...")

        try:
            # 处理最后一帧
            self._process_frame()

            # 停止读卡器
            print("停止读卡器...")
            try:
                if hasattr(self, "gclient") and self.gclient:
                    stop = MsgBaseStop()
                    if self.gclient.sendSynMsg(stop) == 0:
                        print(stop.rtMsg)
            finally:
                # 兼容不同 SDK 的关闭方式
                try:
                    if hasattr(self, "gclient") and self.gclient:
                        # 有的 SDK 是 closeSerial()/close()，你现在用的是 close()
                        self.gclient.close()
                except Exception as e:
                    print(f"关闭读卡器警告: {e}")

            # 写 CSV（若启用）
            if getattr(self.config, "output_format", "h5") in ("csv", "both"):
                self._flush_csv()
                if getattr(self, "csv_filepath", None):
                    print(f"CSV 已保存至: {self.csv_filepath}")

            # 写 HDF5（若启用）
            if self.h5_file:
                try:
                    self.h5_file.flush()
                except Exception:
                    pass
                self.h5_file.close()

            print("会话已停止，数据已保存。")

        finally:
            self.session_active = False

    # ---------------------- CSV 工具 ----------------------
    def _init_csv(self):
        """按需初始化 CSV（常规情况下 start_session 已完成；这里作惰性兜底）。"""
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
        """把缓冲的 CSV 行写入磁盘。"""
        if not self._csv_rows or not self.csv_filepath:
            return
        with open(self.csv_filepath, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerows(self._csv_rows)
        self._csv_rows.clear()

    # ---------------------- 数据路径 ----------------------
    def on_data_received(self, epc: str, rssi: int):
        """
        接收原始RFID读数的主入口。
        这个方法应该被ReaderHandler的回调函数调用。
        """
        if not self.session_active:
            return

        # 更新会话中所有已知的EPC
        self.known_epcs_in_session.add(epc)

        # --- 核心的分帧逻辑 ---
        elapsed_time = time.perf_counter() - self.session_start_time
        expected_frame = int(elapsed_time / self.frame_duration_sec)

        # 如果进入了新的一帧（或多帧），处理之前缓存的帧数据
        while self.current_frame_index < expected_frame:
            self._process_frame()
            self.current_frame_index += 1

        # 将当前读数添加到本帧的缓冲区
        self.frame_buffer[epc].append(rssi)

    def _process_frame(self):
        """
        处理并保存一个完整帧的数据。
        - CSV：只写“本帧实际读到的 EPC”，不补 0
        - HDF5：对本帧缺席的 EPC 补 0
        """
        if not self.session_active:
            return

        frame_time = self.current_frame_index * self.frame_duration_sec

        h5_enabled = self.h5_file is not None
        csv_enabled = getattr(self.config, "output_format", "h5") in ("csv", "both")
        # 极端兜底：若启用 CSV 但路径未就绪，初始化一次
        if csv_enabled and not getattr(self, "csv_filepath", None):
            self._init_csv()

        # === 1) 本帧实际读到的 EPC：统计并写入 ===
        for epc, rssi_list in self.frame_buffer.items():
            if not rssi_list:
                continue
            read_count = len(rssi_list)
            rssi_median = statistics.median(rssi_list)
            rssi_max = max(rssi_list)

            # HDF5：写真实数据行
            if h5_enabled:
                data_row = [frame_time, rssi_median, read_count, rssi_max]
                if epc not in self.h5_file:
                    self.h5_file.create_dataset(epc, data=[data_row], maxshape=(None, 4), chunks=True)
                else:
                    ds = self.h5_file[epc]
                    ds.resize(ds.shape[0] + 1, axis=0)
                    ds[-1] = data_row

            # CSV：只写真实数据行，不补 0
            if csv_enabled:
                self._csv_rows.append([
                    self.current_frame_index,
                    round(frame_time, 3),
                    epc,
                    rssi_median,
                    read_count,
                    rssi_max
                ])

        # === 2)（仅 HDF5）对“会话出现过但本帧缺席”的 EPC 补 0 ===
        if h5_enabled:
            for epc in self.known_epcs_in_session:
                if epc in self.frame_buffer:
                    continue
                data_row = [frame_time, 0, 0, 0]
                if epc not in self.h5_file:
                    self.h5_file.create_dataset(epc, data=[data_row], maxshape=(None, 4), chunks=True)
                else:
                    ds = self.h5_file[epc]
                    ds.resize(ds.shape[0] + 1, axis=0)
                    ds[-1] = data_row

        # 帧结束，清空仅限本帧的缓冲
        self.frame_buffer.clear()

    # ---------------------- 入口 ----------------------
    def data_collect_entry(self):
        if not questionary.confirm("要开始数据采集吗？").ask():
            return
        action_type = questionary.text("请输入本次动作类型：").ask()
        self.start_session(action_type)
        print(f"数据采集已启动（输出模式：{getattr(self.config, 'output_format', 'h5')}），按 Ctrl+C 停止。")
        try:
            while True:
                msg = MsgBaseInventoryEpc(
                    antennaEnable=EnumG.AntennaNo_1.value,
                    inventoryMode=EnumG.InventoryMode_Inventory.value
                )
                if self.gclient.sendSynMsg(msg) == 0:
                    print(msg.rtMsg)
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_session()
            print("数据采集已停止。")

import time
import os
import h5py
import statistics
from collections import defaultdict
import questionary

from settings import ConfigManager

class DataCollector:
    """
    负责从RFID读写器收集数据，进行分帧、预处理，并以会话形式存储。
    """
    def __init__(self, config: ConfigManager):
        """
        使用一个配置字典来初始化数据收集器。

        Args:
            config (dict): 包含所有设置的字典。
        """
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
        # 使用defaultdict(list)可以方便地为新出现的EPC创建列表
        self.frame_buffer = defaultdict(list)
        # 记录会话中出现过的所有EPC，用于补零
        self.known_epcs_in_session = set()

    def start_session(self, action_type: str):
        """
        开始一个新的数据采集会话。

        Args:
            action_type (str): 手动为本次会话添加的动作类型标签。
        """
        if self.session_active:
            print("警告：一个会话已在进行中。请先停止当前会话。")
            return

        print(f"开启新会话，动作类型: '{action_type}'")
        self.session_active = True
        self.session_action_type = action_type
        self.session_start_time = time.perf_counter()
        self.current_frame_index = 0
        self.known_epcs_in_session.clear()
        self.frame_buffer.clear()

        # 创建 HDF5 文件用于存储
        # 文件名示例: 20250623-103000_walking.h5
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}_{action_type}.h5"
        filepath = os.path.join(self.output_dir, filename)

        self.h5_file = h5py.File(filepath, 'w')
        self.h5_file.attrs['action_type'] = action_type
        config_dict = {
            k: v for k, v in self.config_obj.__dict__.items() if not k.startswith('_')
        }
        self.h5_file.attrs['config'] = json.dumps(config_dict)
        
        # 预先不知道有多少数据，所以先不创建dataset，在处理时追加
        print(f"数据将保存至: {filepath}")

    def stop_session(self):
        """停止当前的数据采集会话。"""
        if not self.session_active:
            return

        print("正在停止会话...")
        # 处理最后一帧的剩余数据
        self._process_frame()
        
        self.session_active = False
        if self.h5_file:
            self.h5_file.close()
            print("会话已停止，数据已保存。")

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
        # 计算当前时间点应该属于第几帧
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
        """
        if not self.h5_file:
            return

        frame_time = self.current_frame_index * self.frame_duration_sec
        # print(f"处理帧: {self.current_frame_index} @ {frame_time:.2f}s")

        # 遍历会话中出现过的所有EPC，以确保对未出现的标签进行补零
        for epc in self.known_epcs_in_session:
            rssi_list = self.frame_buffer.get(epc, [])

            if rssi_list:
                # 帧内有数据
                read_count = len(rssi_list)
                rssi_median = statistics.median(rssi_list)
                rssi_max = max(rssi_list)
            else:
                # 帧内信息缺失，使用0进行空值填充
                read_count = 0
                rssi_median = 0
                rssi_max = 0

            # --- 数据存储 ---
            # 每个EPC一个dataset，以帧为单位追加数据
            # 数据格式: [帧时间, 中值RSSI, 读数次数, 最大值RSSI]
            data_row = [frame_time, rssi_median, read_count, rssi_max]
            
            if epc not in self.h5_file:
                self.h5_file.create_dataset(
                    epc, 
                    data=[data_row], 
                    maxshape=(None, 4), # 4列，行数无限
                    chunks=True
                )
            else:
                dataset = self.h5_file[epc]
                dataset.resize(dataset.shape[0] + 1, axis=0)
                dataset[-1] = data_row

        # 清空缓冲区，为下一帧做准备
        self.frame_buffer.clear()

    def data_collect_entry(self):
        if not questionary.confirm("要开始数据采集吗？").ask():
            return
        action_type = questionary.text("请输入本次动作类型：").ask()
        self.start_session(action_type)
        print("数据采集已启动，按 Ctrl+C 停止。")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_session()
            print("数据采集已停止。")
        


# --- 使用示例 ---
if __name__ == '__main__':
    pass
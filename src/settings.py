import questionary
import json
import os

def settings_workflow(config):
    """系统设置工作流。"""
    choice = questionary.select(
        "请选择要修改的设置:",
        choices=[
            '1. 修改串口和波特率',
            '2. 修改滤波器设置',
            '3. 保存当前配置',
            '4. 返回主菜单'
        ]
    ).ask()
    
    if choice == '1. 修改串口和波特率':
        baud, com = set_baud()
        config.baud = int(baud)
        config.com = com
        print(f"已更新: 波特率={config.baud}, COM口={config.com}")
    elif choice == '2. 修改滤波器设置':
        apply_filter, window_length = set_filter()
        config.apply_filter = apply_filter
        config.window_length = int(window_length)
        print(f"已更新滤波器设置: 启用={config.apply_filter}, 窗口长度={config.window_length}")
    elif choice == '3. 保存当前配置':
        config.save()
        print("配置已保存")
    elif choice == '4. 返回主菜单':
        return

def set_baud():
    """设置读写器波特率。"""
    baud = questionary.select(
        "请选择读写器波特率:",
        choices=[
            '9600',
            '19200',
            '38400',
            '57600',
            '115200'
        ]
    ).ask()

    com = questionary.text("从什么串口读取数据？（例如COM6，不分大小，windows下可以使用mode命令查看）").ask()

    return baud, com

def set_filter():
    apply_filter = questionary.confirm("要使用中值滤波器吗？",default=False).ask()
    if apply_filter:
        window_length = questionary.text("请输入滤波器窗口长度（建议为奇数）：",default="5").ask()
    else:
        window_length = "1"

    window_length = int(window_length)

    return apply_filter, window_length

class ConfigManager():
    
    def __init__(self) -> None:
        # --- 通用配置 ---
        self.config_file = "config.json"
        
        # --- 读写器硬件配置 ---
        self.baud = 115200
        self.com = "COM6"
        
        # --- 数据处理配置 ---
        self.frame_duration_ms = 100
        self.output_dir = "data" 
    
    def save(self):
        """保存配置到文件。"""
        config_data = {
            "baud": self.baud,
            "com": self.com,
            "frame_duration_ms": self.frame_duration_ms,
            "output_dir": self.output_dir
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load(self):
        """从文件加载配置。"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.baud = config_data.get("baud", self.baud)
                    self.com = config_data.get("com", self.com)
                    self.frame_duration_ms = config_data.get("frame_duration_ms", self.frame_duration_ms)
                    self.output_dir = config_data.get("output_dir", self.output_dir)
                print(f"已加载配置: COM口={self.com}, 波特率={self.baud}")
            except Exception as e:
                print(f"加载配置失败，使用默认配置: {e}")
        else:
            print("配置文件不存在，使用默认配置")
    

    


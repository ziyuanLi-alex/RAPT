import questionary
import json
from questionary import Choice

try:
    from .paths import app_dir, bundled_default_path, resolve_runtime_path
except ImportError:
    from paths import app_dir, bundled_default_path, resolve_runtime_path


def settings_workflow(config):
    """系统设置工作流（旧菜单里新增“选择输出模式”）。"""
    while True:
        choice = questionary.select(
            "请选择要修改的设置:",
            choices=[
                '1. 修改串口和波特率',
                '2. 修改帧长度',
                '3. 选择输出模式（HDF5 / CSV / BOTH）',  # ← 新增
                '4. 保存当前配置',
                '5. 返回主菜单'
            ]
        ).ask()

        if choice is None or choice == '5. 返回主菜单':
            return

        if choice == '1. 修改串口和波特率':
            baud, com = set_baud()
            if baud:  # 避免 None
                config.baud = int(baud)
            if com:
                config.com = com
            print(f"已更新: 波特率={config.baud}, COM口={config.com}")

        elif choice == '2. 修改帧长度':
            frame_duration_ms = questionary.text(
                "请输入新的帧长度（毫秒）：", default=str(config.frame_duration_ms)
            ).ask()
            if frame_duration_ms and frame_duration_ms.isdigit():
                config.frame_duration_ms = int(frame_duration_ms)
                print(f"已更新: 帧长度={config.frame_duration_ms}毫秒")
            else:
                print("输入无效，已忽略。")

        elif choice == '3. 选择输出模式（HDF5 / CSV / BOTH）':
            mode = questionary.select(
                f"选择输出模式（当前：{getattr(config, 'output_format', 'h5')}）",
                choices=[
                    Choice("仅 HDF5（原始模式）", "h5"),
                    Choice("仅 CSV（Excel 直接打开）", "csv"),
                    Choice("同时输出 HDF5 + CSV", "both"),
                    Choice("↩ 返回上级", "back"),
                ]
            ).ask()
            if mode in ("h5", "csv", "both"):
                config.output_format = mode
                print(f"已设置输出模式：{config.output_format}")

        elif choice == '4. 保存当前配置':
            config.save()
            print("配置已保存")

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

def singleton(cls):
    """单例装饰器"""
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class ConfigManager():
    
    def __init__(self) -> None:
        # --- 通用配置 ---
        self.config_file = app_dir() / "config.json"
        
        # --- 读写器硬件配置 ---
        self.baud = 115200
        self.com = "COM6"
        
        # --- 数据处理配置 ---
        self.frame_duration_ms = 100
        self.output_dir = str(app_dir() / "data")
        self.output_format = "h5"  #  "h5" | "csv" | "both"
        self.skellycam_base_url = "http://localhost:53117"
        self.skellycam_recording_dir = r"H:\lib\Skellycam_recording"
        self.locale = "auto"

    def save(self):
        """保存配置到文件。"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            "baud": self.baud,
            "com": self.com,
            "frame_duration_ms": self.frame_duration_ms,
            "output_dir": self.output_dir,
            "output_format": self.output_format,
            "skellycam_base_url": self.skellycam_base_url,
            "skellycam_recording_dir": self.skellycam_recording_dir,
            "locale": self.locale,
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load(self):
        """从文件加载配置。"""
        load_path = self.config_file if self.config_file.exists() else bundled_default_path("config.json")
        if load_path.exists():
            try:
                with open(load_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.baud = config_data.get("baud", self.baud)
                    self.com = config_data.get("com", self.com)
                    self.frame_duration_ms = config_data.get("frame_duration_ms", self.frame_duration_ms)
                    self.output_dir = str(resolve_runtime_path(config_data.get("output_dir", self.output_dir)))
                    self.output_format = config_data.get("output_format", getattr(self, "output_format", "h5"))
                    self.skellycam_base_url = config_data.get(
                        "skellycam_base_url", self.skellycam_base_url
                    )
                    self.skellycam_recording_dir = config_data.get(
                        "skellycam_recording_dir", self.skellycam_recording_dir
                    )
                    self.locale = config_data.get("locale", self.locale)
                if load_path != self.config_file:
                    self.save()
                print(f"已加载配置: COM口={self.com}, 波特率={self.baud}")
            except Exception as e:
                print(f"加载配置失败，使用默认配置: {e}")
        else:
            print("配置文件不存在，使用默认配置")
    

    


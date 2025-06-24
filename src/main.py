import questionary
from rich.console import Console
from settings import ConfigManager
from check_status import *
from binding import BindingManager
from DataCollector import DataCollector

def main_menu():
    """显示主菜单并等待用户选择。"""
    choice = questionary.select(
        "欢迎使用RFID数据采集工具，请选择操作:",
        choices=[
            '1. 开始数据采集',
            '2. 标签绑定管理',
            '3. 检查读写器状态',
            '4. 系统设置',
            'q. 退出程序'
        ]
    ).ask()
    return choice

def start_collection_workflow(config):
    """开始数据采集工作流。"""
    # TODO: 实现数据采集逻辑
    print(f"使用配置: COM口={config.com}, 波特率={config.baud}")
    pass


def run():
    console = Console()
    # 创建配置管理器实例
    config = ConfigManager()
    config.load()  # 加载配置

    # 创建绑定管理器实例
    binding_manager = BindingManager(config)
    data_collector = DataCollector(config)
    
    while True:
        choice = main_menu()
        
        if choice == '1. 开始数据采集':
            data_collector.data_collect_entry()
        elif choice == '2. 标签绑定管理':
            binding_manager.binding_entry(config)
        elif choice == '3. 检查读写器状态':
            check_status_workflow(config)
        elif choice == '4. 系统设置':
            from settings import settings_workflow
            settings_workflow(config)
        elif choice == 'q. 退出程序' or choice is None:
            console.print("感谢使用，程序已退出。", style="bold green")
            break
    
if __name__ == "__main__":
    run()
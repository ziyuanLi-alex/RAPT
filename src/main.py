import questionary
from rich.console import Console

def main_menu():
    """显示主菜单并等待用户选择。"""
    choice = questionary.select(
        "欢迎使用RFID数据采集工具，请选择操作:",
        choices=[
            '1. 开始数据采集',
            '2. 绑定新标签',
            '3. 检查读写器状态',
            '4. 系统设置',
            'q. 退出程序'
        ]
    ).ask()
    return choice

def run():
    console = Console()
    while True:
        choice = main_menu()
        
        if choice == '1. 开始数据采集':
            start_collection_workflow()
        elif choice == '2. 绑定新标签':
            bind_tag_workflow()
        elif choice == '3. 检查读写器状态':
            check_status_workflow()
        elif choice == '4. 系统设置':
            settings_workflow()
        elif choice == 'q. 退出程序' or choice is None:
            console.print("感谢使用，程序已退出。", style="bold green")
            break
    
if __name__ == "__main__":
    run()
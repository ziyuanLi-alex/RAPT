# -*- coding: utf-8 -*-
import questionary
from rich.console import Console

from settings import ConfigManager, settings_workflow
from check_status import check_status_workflow
from binding import BindingManager
from DataCollector import DataCollector


def main_menu() -> str | None:
    """
    显示主菜单并等待用户选择。
    返回所选菜单项（字符串）。用户按 ESC/CTRL+C 时返回 None。
    """
    return questionary.select(
        "欢迎使用 RFID 数据采集工具，请选择操作：\n"
        "（提示：在任意子流程中按 Ctrl+C 可返回主菜单）",
        choices=[
            "1. 开始数据采集",
            "2. 标签绑定管理",
            "3. 检查读写器状态",
            "4. 系统设置",
            "q. 退出程序",
        ],
    ).ask()


def start_collection_workflow(config: ConfigManager, data_collector: DataCollector, console: Console) -> None:
    """
    开始数据采集工作流。
    在该流程内部，按 Ctrl+C 可安全中断并返回主菜单。
    """
    console.print(
        f"[bold]使用配置：[/]COM口={config.com}  波特率={config.baud}  帧长={config.frame_duration_ms}ms  "
        f"输出目录={config.output_dir}  输出模式={getattr(config, 'output_format', 'h5')}",
        style="cyan",
    )
    console.print("[dim]提示：采集中按 Ctrl+C 可停止并返回主菜单。[/dim]")
    try:
        data_collector.data_collect_entry()
    except KeyboardInterrupt:
        console.print("\n[yellow]采集已中断，正在收尾...[/yellow]")
        try:
            data_collector.stop_session()
        except Exception:
            pass
        console.print("[green]已返回主菜单。[/green]")


def run() -> None:
    console = Console()

    # 1) 读取配置
    config = ConfigManager()
    config.load()  # 首次运行会生成默认配置文件

    # 2) 管理器与采集器
    binding_manager = BindingManager(config)
    data_collector = DataCollector(config)

    # 3) 主循环
    while True:
        choice = main_menu()

        if choice is None:
            # 用户按了 ESC / Ctrl+C 退出主菜单选择，询问是否退出
            confirm = questionary.confirm("确定要退出程序吗？").ask()
            if confirm:
                console.print("感谢使用，程序已退出。", style="bold green")
                break
            else:
                continue

        if choice == "1. 开始数据采集":
            start_collection_workflow(config, data_collector, console)

        elif choice == "2. 标签绑定管理":
            try:
                binding_manager.binding_entry(config)
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "3. 检查读写器状态":
            try:
                check_status_workflow(config)
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "4. 系统设置":
            try:
                settings_workflow(config)  # 直接进入“旧菜单”，其中含“选择输出模式”等
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "q. 退出程序":
            console.print("感谢使用，程序已退出。", style="bold green")
            break

        else:
            console.print("[yellow]未识别的选项，已返回主菜单。[/yellow]")


if __name__ == "__main__":
    run()

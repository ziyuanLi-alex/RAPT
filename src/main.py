# -*- coding: utf-8 -*-
import questionary
from rich.console import Console

from settings import ConfigManager, settings_workflow
from check_status import check_status_workflow
from binding import BindingManager
from DataCollector import DataCollector

# 新采集模式（线形/点形）
from mode import run_line_mode, run_point_mode


def main_menu() -> str | None:
    """显示主菜单"""
    return questionary.select(
        "欢迎使用 RFID 数据采集工具，请选择操作：\n"
        "（提示：在任意子流程中按 Ctrl+C 可返回主菜单）",
        choices=[
            "1. 新采集模式（线形/点形）",
            "2. 开始数据采集 (旧)",
            "3. 标签绑定管理",
            "4. 检查读写器状态",
            "5. 系统设置",
            "q. 退出程序",
        ],
    ).ask()


def start_collection_workflow(config: ConfigManager, data_collector: DataCollector, console: Console) -> None:
    """旧采集模式：持续采集"""
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


def make_stream(dc: DataCollector):
    """返回标准化数据流"""
    if hasattr(dc, "stream") and callable(getattr(dc, "stream")):
        return dc.stream()
    raise RuntimeError("未检测到 DataCollector.stream()，请在 DataCollector 中实现该生成器。")


# --- (已修改) 增加了一个 binding_manager 参数 ---
def collect_menu_new(config: ConfigManager, data_collector: DataCollector, console: Console,
                     binding_manager: BindingManager) -> None:
    """新采集模式主菜单"""
    choice = questionary.select(
        "请选择新采集模式：",
        choices=[
            "线形采集（持续，Ctrl+C 停止）",
            "线形采集（定时，输入时长秒）",
            "点形采集（手动触发：每次3个≤3s，不足补0）",
            "返回主菜单",
        ],
    ).ask()
    if choice in (None, "返回主菜单"):
        return

    out_dir = getattr(config, "output_dir", "data")
    action_name = questionary.text("请输入本次采集的类型/描述（写入文件名，可留空）：", default="").ask()

    # ---------------- 线形采集（持续） ----------------
    if choice.startswith("线形采集（持续"):
        console.print("[bold cyan]线形-持续模式：按 Ctrl+C 停止。[/bold cyan]")
        stream = None
        try:
            stream = make_stream(data_collector)
            out = run_line_mode(
                stream=stream,
                out_dir=out_dir,
                stop_after_seconds=None,
                action_name=action_name,
                binder=binding_manager  # --- (已修改) 传递 binder ---
            )
            if not out:
                console.print("[yellow]本次未采集到任何数据，未保存文件。[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[yellow]已停止。[/yellow]")
        finally:
            try:
                data_collector.stop_stream()
            except Exception:
                pass

    # ---------------- 线形采集（定时） ----------------
    elif choice.startswith("线形采集（定时"):
        sec = questionary.text("请输入采集时长（秒）", default="5").ask()
        try:
            sec = float(sec)
        except Exception:
            sec = 5.0
        console.print(f"[bold cyan]线形-定时模式：{sec:.1f} 秒。[/bold cyan]")
        stream = None
        try:
            stream = make_stream(data_collector)
            out = run_line_mode(
                stream=stream,
                out_dir=out_dir,
                stop_after_seconds=sec,
                action_name=action_name,
                binder=binding_manager  # --- (已修改) 传递 binder ---
            )
            if not out:
                console.print("[yellow]本次未采集到任何数据，未保存文件。[/yellow]")
        finally:
            try:
                data_collector.stop_stream()
            except Exception:
                pass

    # ---------------- 点形采集 ----------------
    elif choice.startswith("点形采集（手动触发"):
        stream = None
        try:
            stream = make_stream(data_collector)
            out = run_point_mode(
                stream=stream,
                out_dir=out_dir,
                timeout_per_trigger=3.0,
                action_name=action_name,
                binder=binding_manager  # --- (已修改) 传递 binder ---
            )
        finally:
            try:
                data_collector.stop_stream()
            except Exception:
                pass
            import io, time, contextlib
            _buf = io.StringIO()
            with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
                time.sleep(0.3)


def run() -> None:
    """主程序入口"""
    console = Console()
    config = ConfigManager()
    config.load()
    binding_manager = BindingManager(config)
    data_collector = DataCollector(config)

    while True:
        choice = main_menu()
        if choice is None:
            if questionary.confirm("确定要退出程序吗？").ask():
                console.print("感谢使用，程序已退出。", style="bold green")
                break
            else:
                continue

        # --- (已修改) 在调用时传入 binding_manager ---
        if choice == "1. 新采集模式（线形/点形）":
            try:
                collect_menu_new(config, data_collector, console, binding_manager)
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "2. 开始数据采集 (旧)":
            start_collection_workflow(config, data_collector, console)

        elif choice == "3. 标签绑定管理":
            try:
                binding_manager.binding_entry(config)
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "4. 检查读写器状态":
            try:
                check_status_workflow(config)
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "5. 系统设置":
            try:
                settings_workflow(config)
            except KeyboardInterrupt:
                console.print("\n[green]已返回主菜单。[/green]")

        elif choice == "q. 退出程序":
            console.print("感谢使用，程序已退出。", style="bold green")
            break

        else:
            console.print("[yellow]未识别的选项，已返回主菜单。[/yellow]")


if __name__ == "__main__":
    run()
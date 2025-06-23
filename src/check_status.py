import questionary
from uhf.reader import *
from time import sleep
import threading
from collections import deque
from rich.live import Live
from rich.panel import Panel
from rich.console import Console

# 创建一个线程安全的双端队列，用于存放最新的5条日志
log_lines = deque(maxlen=5)
log_lines_lock = threading.Lock()

def receivedEpc(epcInfo: LogBaseEpcInfo):
    """此回调函数由读写器SDK的后台线程调用。"""
    if epcInfo.result == 0:
        with log_lines_lock:
            log_lines.append(f"Read EPC: {epcInfo.epc}, RSSI: {epcInfo.rssi}")

def receivedEpcOver(epcOver: LogBaseEpcOver):
    """盘点结束的回调，在这里可以什么都不做。"""
    pass


def check_status_workflow(config, check_duration=3):
    """
    检查系统状态，并使用滚动面板显示实时读数。
    """
    if not questionary.confirm("要检查系统状态吗？", default=True).ask():
        return

    console = Console()
    console.print(f"当前配置: 波特率={config.baud}, COM口={config.com}", style="bold")
    if config.apply_filter:
        console.print(f"当前滤波器设置: 启用={config.apply_filter}, 窗口长度={config.window_length}", style="bold")
    else:
        console.print("当前滤波器设置: 未启用", style="bold")

    # 将所有与硬件交互的阻塞代码封装在一个函数中，以便在单独的线程中运行
    def reader_task():
        g_client = GClient()
        if g_client.openSerial((config.com, config.baud)):
            g_client.callEpcInfo = receivedEpc
            g_client.callEpcOver = receivedEpcOver

            msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                      inventoryMode=EnumG.InventoryMode_Inventory.value)
            
            # 开始盘点，但不阻塞主线程
            if g_client.sendSynMsg(msg) == 0:
                sleep(check_duration)  # 持续盘点一段时间
                stop = MsgBaseStop()
                g_client.sendSynMsg(stop) # 发送停止指令
            g_client.close()

    # 清空旧的读数，准备本次检查
    log_lines.clear()

    # 启动读写器线程
    reader_thread = threading.Thread(target=reader_task)
    reader_thread.start()
    
    console.print(f"\n正在检查系统状态 (持续 {check_duration} 秒)...")

    # 使用 rich.live 实时更新UI
    with Live(Panel("等待读数...", title="[bold cyan]实时读数[/]"), 
              console=console, 
              refresh_per_second=10) as live:
        # 当读写器线程还在工作时，持续更新界面
        while reader_thread.is_alive():
            with log_lines_lock:
                # 从共享队列中读取最新数据并更新面板
                live.update(Panel("\n".join(log_lines), 
                                  title="[bold cyan]实时读数[/]", 
                                  border_style="green"))
            sleep(0.1) # 控制UI刷新率

    console.print("\n[bold green]✅ 检查完成。[/bold green]")

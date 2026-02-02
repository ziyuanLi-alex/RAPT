import questionary
from uhf.reader import *
from time import sleep
import json
from rich.console import Console  # 引入rich，让打印更好看


class BindingManager():

    def __init__(self, config) -> None:
        self.bind_dict = {}
        self.config = config
        self.console = Console()  # 使用rich Console
        self.load_binding()

    def bind(self, epc: str, name: str) -> None:
        """绑定标签。"""
        self.bind_dict[epc] = name
        self.save_binding()

    def remove_binding(self, epc: str) -> bool:
        """移除标签绑定。如果存在则删除并保存，返回 True；否则返回 False。"""
        if epc in self.bind_dict:
            del self.bind_dict[epc]
            self.save_binding()
            return True
        return False

    def check_bind(self, epc: str) -> bool:
        """(已修改) 检查标签是否绑定，此版本不再打印信息。"""
        return epc in self.bind_dict

    def get_name(self, epc: str) -> str:
        """获取标签绑定名称。如果未绑定，安全地返回EPC本身。"""
        return self.bind_dict.get(epc, epc)

    def load_binding(self, path: str = "binding.json"):
        """从文件加载绑定信息。"""
        try:
            with open(path, "r", encoding='utf-8') as f:
                self.bind_dict = json.load(f)
        except FileNotFoundError:
            self.console.print(f"文件 {path} 未找到，跳过加载绑定信息。")
        except json.JSONDecodeError:
            self.console.print(f"文件 {path} 格式错误，跳过加载绑定信息。")

    def save_binding(self, path: str = "binding.json"):
        """将绑定信息保存到文件。"""
        try:
            with open(path, "w", encoding='utf-8') as f:
                json.dump(self.bind_dict, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.console.print(f"[bold red]保存绑定文件 {path} 失败: {e}[/]")

    def bind_tag_workflow(self):
        """绑定新标签工作流。"""
        read_epc = []

        def receivedEpc(epcInfo: LogBaseEpcInfo):
            if epcInfo.result == 0:
                self.console.print(f"EPC read: {epcInfo.epc}", end='\r')
                if epcInfo.epc not in read_epc:
                    read_epc.append(epcInfo.epc)

        def receivedEpcOver(epcOver: LogBaseEpcOver):
            pass

        g_client = GClient()
        g_client.printLog = False
        while True:
            read_epc.clear()
            if not questionary.confirm("要扫描并绑定新标签吗？", default=True).ask():
                break

            self.console.print("正在扫描标签 (1秒)...")
            serial_opened = False
            try:
                if g_client.openSerial((self.config.com, self.config.baud)):
                    serial_opened = True  # 标记串口已成功打开
                    g_client.callEpcInfo = receivedEpc
                    g_client.callEpcOver = receivedEpcOver
                    msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                              inventoryMode=EnumG.InventoryMode_Inventory.value)
                    if g_client.sendSynMsg(msg) == 0:
                        sleep(1)
                        stop = MsgBaseStop()
                        g_client.sendSynMsg(stop)
                else:
                    self.console.print(f"[bold red]错误：无法打开串口 {self.config.com}[/]")
                    break
            finally:
                # --- 这是修复点 ---
                if serial_opened:  # 只有在成功打开后才关闭
                    g_client.close()

            if not read_epc:
                self.console.print("未扫描到任何标签。")
                continue

            epc_choice = questionary.select(
                "请选择要绑定的标签:",
                choices=read_epc
            ).ask()
            if epc_choice is None: continue

            current_name_str = f" (当前已绑定: [bold cyan]{self.get_name(epc_choice)}[/])" if self.check_bind(
                epc_choice) else ""
            name = questionary.text(f"请输入标签名称{current_name_str}:").ask()
            if name is None or not name.strip():
                self.console.print("[yellow]已取消输入。[/yellow]")
                continue

            self.bind(epc_choice, name)
            self.console.print(f"[green]绑定成功：[/]{epc_choice} -> [bold green]{name}[/]")

        self.save_binding()

    def check_bind_interactive(self):
        """检查绑定状态的工作流。"""
        read_epc = []

        def receivedEpc(epcInfo: LogBaseEpcInfo):
            if epcInfo.result == 0:
                self.console.print(f"EPC read: {epcInfo.epc}", end='\r')
                if epcInfo.epc not in read_epc:
                    read_epc.append(epcInfo.epc)

        def receivedEpcOver(epcOver: LogBaseEpcOver):
            pass

        g_client = GClient()
        g_client.printLog = False
        self.console.print("正在扫描标签 (1秒)...")
        serial_opened = False
        try:
            if g_client.openSerial((self.config.com, self.config.baud)):
                serial_opened = True  # 标记串口已成功打开
                g_client.callEpcInfo = receivedEpc
                g_client.callEpcOver = receivedEpcOver
                msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                          inventoryMode=EnumG.InventoryMode_Inventory.value)
                if g_client.sendSynMsg(msg) == 0:
                    sleep(1)
                    stop = MsgBaseStop()
                    g_client.sendSynMsg(stop)
            else:
                self.console.print(f"[bold red]错误：无法打开串口 {self.config.com}[/]")
                return
        finally:
            # --- 这是修复点 ---
            if serial_opened:  # 只有在成功打开后才关闭
                g_client.close()

        self.console.print("\n--- 扫描结果 ---")
        if not read_epc:
            self.console.print("未扫描到任何标签。")
        for epc in read_epc:
            if self.check_bind(epc):
                self.console.print(f"✅ 标签 {epc} 已绑定到 -> [bold green]{self.get_name(epc)}[/]")
            else:
                self.console.print(f"❌ 标签 {epc} [yellow]未绑定[/]")
        self.console.print("----------------")

    def binding_entry(self, config):
        """绑定标签入口。"""
        while True:
            choice = questionary.select(
                "请选择绑定操作",
                choices=[
                    "绑定/更新标签",
                    "检查附近标签的绑定状态",
                    "返回主菜单"
                ]
            ).ask()
            if choice == "绑定/更新标签":
                self.bind_tag_workflow()
            elif choice == "检查附近标签的绑定状态":
                self.check_bind_interactive()
            elif choice == "返回主菜单" or choice is None:
                return
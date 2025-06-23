import questionary
from uhf.reader import *
from time import sleep
import json

class BindingManager():

    def __init__(self, config) -> None:
        self.bind_dict = {}
        self.config = config
        self.load_binding()

    def bind(self, epc: str, name: str) -> None:
        """绑定标签。"""
        self.bind_dict[epc] = name
        self.save_binding()

    def check_bind(self, epc: str) -> bool:
        """检查标签是否绑定。"""
        try:
            self.bind_dict[epc]
            return True
        except KeyError:
            print(f"标签 {epc} 未绑定")
            return False
    
    def get_name(self, epc: str) -> str:
        """获取标签绑定名称。"""
        return self.bind_dict[epc]

    def load_binding(self, path: str = "binding.json"):
        """从文件加载绑定信息。"""
        try:
            with open(path, "r") as f:
                self.bind_dict = json.load(f)
        except FileNotFoundError:
            print(f"文件 {path} 未找到，跳过加载绑定信息。")
        except json.JSONDecodeError:
            print(f"文件 {path} 格式错误，跳过加载绑定信息。")
    
    def save_binding(self, path: str = "binding.json"):
        """将绑定信息保存到文件。"""
        try:
            with open(path, "w") as f:
                json.dump(self.bind_dict, f, indent=4)
        except FileNotFoundError:
            print(f"文件 {path} 未找到，跳过保存绑定信息。")
        except json.JSONDecodeError:
            print(f"文件 {path} 格式错误，跳过保存绑定信息。")

    def bind_tag_workflow(self):
        """绑定新标签工作流。"""
        read_epc = []

        def receivedEpc(epcInfo: LogBaseEpcInfo):
            if epcInfo.result == 0:
                print(f"EPC read: {epcInfo.epc}", end='\r')
                if epcInfo.epc not in read_epc:
                    read_epc.append(epcInfo.epc)
                # print(epcInfo.rssi)

        def receivedEpcOver(epcOver: LogBaseEpcOver):
            """盘点结束的回调，在这里可以什么都不做。"""
            pass

        g_client = GClient()
        g_client.printLog = False
        while True:
            read_epc.clear
            if not questionary.confirm("要绑定标签吗？", default=True).ask():
                break

            if g_client.openSerial((self.config.com, self.config.baud)):
                g_client.callEpcInfo = receivedEpc
                g_client.callEpcOver = receivedEpcOver

                msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                        inventoryMode=EnumG.InventoryMode_Inventory.value)
                
                if g_client.sendSynMsg(msg) == 0:
                    sleep(1)  # 持续盘点
                    stop = MsgBaseStop()
                    g_client.sendSynMsg(stop)
                g_client.close()
            
            epc_choice = questionary.select(
                "请选择要绑定的标签:",
                choices=read_epc
            ).ask()
            name = questionary.text("请输入标签名称:").ask()
            self.bind(epc_choice, name)

        stop = MsgBaseStop()
        if g_client.sendSynMsg(stop) == 0:
            # print(stop.rtMsg)
            pass
        g_client.close()
        self.save_binding()

    def check_bind_interactive(self):
        read_epc = []

        def receivedEpc(epcInfo: LogBaseEpcInfo):
            if epcInfo.result == 0:
                print(f"EPC read: {epcInfo.epc}",end='\r')
                if epcInfo.epc not in read_epc:
                    read_epc.append(epcInfo.epc)

        def receivedEpcOver(epcOver: LogBaseEpcOver):
            """盘点结束的回调，在这里可以什么都不做。"""
            pass

        g_client = GClient()
        g_client.printLog = False
        if g_client.openSerial((self.config.com, self.config.baud)):
            g_client.callEpcInfo = receivedEpc
            g_client.callEpcOver = receivedEpcOver

            msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                      inventoryMode=EnumG.InventoryMode_Inventory.value)
            
            if g_client.sendSynMsg(msg) == 0:
                sleep(1)  # 持续盘点
                stop = MsgBaseStop()
        
        for epc in read_epc:
            if self.check_bind(epc):
                print(f"标签 {epc} 已绑定到 {self.get_name(epc)}")
            else:
                print(f"标签 {epc} 未绑定")

        stop = MsgBaseStop()
        if g_client.sendSynMsg(stop) == 0:
            # print(stop.rtMsg)
            pass
        g_client.close()

    def binding_entry(self, config):
        """绑定标签入口。"""
        choice = questionary.select(
            "请选择绑定操作",
            choices=[
                "绑定新标签",
                "检查绑定状态",
                "退出"
            ]
        ).ask()
        if choice == "绑定新标签":
            self.bind_tag_workflow()
        elif choice == "检查绑定状态":
            self.check_bind_interactive()
        elif choice == "退出":
            return

        

    
        
        
        





        




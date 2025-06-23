from uhf.reader import *
from time import *


def receivedEpc(epcInfo: LogBaseEpcInfo):
    if epcInfo.result == 0:
        print(epcInfo.epc)


def receivedEpcOver(epcOver: LogBaseEpcOver):
    print("LogBaseEpcOver")


if __name__ == '__main__':
    g_client = GClient()
    if g_client.openSerial(("com6", 115200)): # com不分大小
    # if g_client.openTcp(("192.168.1.168", 8160)):
        # 订阅标签回调
        g_client.callEpcInfo = receivedEpc
        g_client.callEpcOver = receivedEpcOver

        # 读epc
        msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                  inventoryMode=EnumG.InventoryMode_Inventory.value)
        if g_client.sendSynMsg(msg) == 0:
            print(msg.rtMsg)

        # 5s后执行停止盘点以及关闭连接
        sleep(5)

        stop = MsgBaseStop()
        if g_client.sendSynMsg(stop) == 0:
            print(stop.rtMsg)

        g_client.close()

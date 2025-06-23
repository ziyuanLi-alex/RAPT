from uhf.reader import *
from time import *


def receivedEpc(epcInfo: LogBaseEpcInfo):
    if epcInfo.result == 0:
        print(epcInfo.epc + "-->" + epcInfo.tid)
        print(epcInfo.rssi)

def receivedEpcOver(epcOver: LogBaseEpcOver):
    print("LogBaseEpcOver")


if __name__ == '__main__':
    g_client = GClient()
    if g_client.openSerial(("COM6", 115200)):
    # if g_client.openTcp(("192.168.1.168", 8160)):
        # 订阅标签回调
        g_client.callEpcInfo = receivedEpc
        g_client.callEpcOver = receivedEpcOver

        # 读epc
        msg = MsgBaseInventoryEpc(antennaEnable=EnumG.AntennaNo_1.value,
                                  inventoryMode=EnumG.InventoryMode_Inventory.value)

        # 匹配TID读 E280110520007993A8F708A8 可选参数
        # epc_filter = ParamEpcFilter(EnumG.ParamFilterArea_TID.value, 0, "E280110520007993A8F708A8")
        # msg.filter = epc_filter

        # 读TID 默认只读EPC 可选参数
        tid = ParamEpcReadTid(mode=EnumG.ParamTidMode_Auto.value, dataLen=6)
        msg.readTid = tid

        # 读UserData 可选参数
        # userData = ParamEpcReadUserData(start=0, dataLen=4)  # word
        # msg.readUserData = userData

        # 读保留区 可选参数
        # reserved = ParamEpcReadReserved(start=0, dataLen=4)  # word
        # msg.readReserved = reserved

        if g_client.sendSynMsg(msg) == 0:
            print(msg.rtMsg)
            # print(msg.readUserData)
            # print(msg.readReserved)


        # 5s后执行停止盘点以及关闭连接
        sleep(1)

        stop = MsgBaseStop()
        if g_client.sendSynMsg(stop) == 0:
            print(stop.rtMsg)

        g_client.close()

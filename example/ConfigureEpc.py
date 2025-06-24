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
    if g_client.openSerial(("com6", 115200)): # com不分大小
    # if g_client.openTcp(("192.168.1.168", 8160)):
        # 订阅标签回调
        g_client.callEpcInfo = receivedEpc
        g_client.callEpcOver = receivedEpcOver

        readerInfo = MsgBaseGetCapabilities()
        if g_client.sendSynMsg(readerInfo) == 0:
            print("Max Power is: {}".format(readerInfo.maxPower))
            print("Min Power is: {}".format(readerInfo.minPower))
            print("Antenna Count is {}".format(readerInfo.antennaCount))
        
        # dicPower = {"1": 33}
        # msg = MsgBaseSetPower(**dicPower)
        # if g_client.sendSynMsg(msg) == 0:
        #     print("Set Power to {} is {}".format(dicPower["1"], msg.rtMsg))
        
        basebandInfo = MsgBaseGetBaseband()
        if g_client.sendSynMsg(basebandInfo) == 0:
            print(f"Baseband Speed is {basebandInfo.baseSpeed}")
            print(f"Baseband qValue is {basebandInfo.qValue}")
            print(f"Baseband session is {basebandInfo.session}")
            print(f"Baseband inventoryFlag is {basebandInfo.inventoryFlag}")

        

        g_client.close()

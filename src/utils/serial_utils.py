import serial.tools.list_ports
from uhf.reader import GClient, MsgBaseStop

def get_serial_ports_details():
    """
    获取系统中所有可用的串口详细信息。
    返回 List[ListPortInfo] 对象列表。
    """
    return serial.tools.list_ports.comports()

def get_serial_ports():
    """获取系统中所有可用的串口名称列表 (仅返回设备名)"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def check_reader_connection(port, baud_rate=115200):
    """
    验证指定串口是否连接了有效的读写器。
    
    Args:
        port (str): 串口号 (e.g. "COM3")
        baud_rate (int): 波特率
        
    Returns:
        bool: True if connected and handshake passed, False otherwise.
    """
    client = GClient()
    try:
        if client.openSerial((port, baud_rate)):
            # 尝试发送停止指令作为握手
            msg = MsgBaseStop()
            # 发送同步消息，返回 0 表示成功
            success = (client.sendSynMsg(msg) == 0)
            client.close()
            return success
    except Exception:
        pass
    return False

import questionary
from questionary import question

def settings_workflow():
    """系统设置工作流。"""
    pass

def set_baud():
    """设置读写器波特率。"""
    baud = questionary.select(
        "请选择读写器波特率:",
        choices=[
            '9600',
            '19200',
            '38400',
            '57600',
            '115200'
        ]
    ).ask()

    com = questionary.text("从什么串口读取数据？（例如COM6，不分大小，windows下可以使用mode命令查看）").ask()

    return baud, com

def set_filter():
    apply_filter = questionary.conform("要使用中值滤波器吗？",default=True)
    if apply_filter:
        window_length = questionary.text("请输入滤波器窗口长度（建议为奇数）：",default=5).ask()
    else:
        window_length = 1
    return apply_filter, window_length



    


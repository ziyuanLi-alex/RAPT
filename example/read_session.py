import h5py
import json

def read_session_h5(filepath):
    """读取session h5文件的最简单脚本"""
    
    # 打开h5文件
    f = h5py.File(filepath, 'r')
    
    # 读取元数据
    action_type = f.attrs['action_type']
    config = json.loads(f.attrs['config'])
    
    print(f"动作类型: {action_type}")
    print(f"配置信息: {config}")
    print("\n数据内容:")
    
    # 遍历所有EPC数据集
    for epc in f.keys():
        data = f[epc][:]
        print(f"\nEPC: {epc}")
        print(f"数据形状: {data.shape}")
        print("前5行数据 [帧时间, 中值RSSI, 读数次数, 最大值RSSI]:")
        print(data[:5])
    
    f.close()

if __name__ == "__main__":
    # 使用示例
    filepath = "data/20250624-181323_run.h5"  # 修改为实际文件路径
    read_session_h5(filepath)
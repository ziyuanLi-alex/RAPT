# RAPT (RFID Analysis & Pose Toolkit)

RAPT 是一个面向 RFID RSSI、视频与 SkellyCam 同步实验的数据采集工具。主程序是基于 PyQt6 和 PyQt6-Fluent-Widgets 的 Windows GUI 应用，支持 RFID 读写器连接检查、标签绑定、RFID 采集、视频采集、RFID + 单摄像头采集，以及 RFID + SkellyCam 多摄像头采集。

## 当前功能

### 图形界面

运行 `python src/main.py` 会启动 RAPT GUI。主窗口包含以下页面：

- 总览：应用入口与 RFID 读写器、视频和 SkellyCam 实验状态总览。
- 采集监控：RFID 采集，包括连续采集与单次采集。
- 标签管理：标签绑定，包括扫描附近 EPC、绑定名称、搜索和删除已保存绑定。
- 视频采集：视频采集，以及 RFID + 单摄像头采集。
- 集成采集：RFID + SkellyCam 多摄像头采集，通过 HTTP 控制 SkellyCam 并同步记录 RFID 原始读数。
- 系统诊断：RFID 读写器连接检查，并实时显示 EPC/RSSI。
- 设置：串口、波特率、输出目录、输出格式、界面语言、SkellyCam 地址与录制目录。

### RFID 采集

RAPT 通过 `uhfReaderApi` 连接 UHF RFID 读写器，当前主要使用串口连接。配置项包括：

- COM 口
- 波特率
- RFID 帧长度
- 输出目录
- 输出格式：`h5`、`csv`、`both`

底层 `DataCollector.stream()` 会持续输出标准化 RFID 读数：

```python
{
    "ts": 采集时间戳,
    "frame_idx": 帧序号,
    "epc": "标签 EPC",
    "rssi": RSSI 数值,
    "ant": 天线编号,
}
```

### 采集监控

“采集监控”提供两类 RFID 采集：

- 持续采集：输入任务名称和持续时间。持续时间为 `0` 时一直采集到手动停止。
- 单次采集：为每个点输入 label 和采集时长，逐点采集，最后统一保存。

持续采集默认将数据写到：

```text
data/YYYYMMDD/continuous_mode/
```

单次采集默认将数据写到：

```text
data/YYYYMMDD/single_shot_mode/
```

### 标签管理

“标签管理”用于维护 `binding.json` 中的 EPC 绑定关系。

支持：

- 扫描附近 EPC。
- 为 EPC 绑定易读名称。
- 查看、搜索、删除已有绑定。

示例：

```json
{
    "e280699500005002012078f7": "head",
    "e2000016200601690430e74e": "hand"
}
```

### 视频采集

“视频采集”使用 OpenCV 和 PyQt6 摄像头接口完成视频预览与录制。

支持三种模式：

- `Joint`：RFID + 单摄像头采集，同时启动视频录制和 RFID 原始采集。
- `Video`：视频采集，仅录制视频。
- `RFID`：RFID 采集，仅记录 RFID 原始读数。

视频文件和帧时间戳 metadata 默认写到：

```text
data/YYYYMMDD/video_mode/
```

RFID 原始模式默认写到：

```text
data/YYYYMMDD/raw_mode/
```

### RFID + SkellyCam 多摄像头采集

“集成采集”用于 RFID + SkellyCam 多摄像头同步实验。应用会先检查 SkellyCam HTTP 服务，然后：

1. 创建 RAPT session 目录。
2. 启动 RFID raw logging。
3. 调用 SkellyCam `/skellycam/camera/group/all/record/start`。
4. 支持写入 `sync_start` 和 `sync_end` 同步事件。
5. 停止时调用 SkellyCam `/skellycam/camera/group/all/record/stop`。
6. 保存 RFID CSV、事件 CSV 和 session metadata。

集成采集默认数据结构：

```text
data/RAPT_dataset/
└── session_YYYY_MM_DD_001/
    ├── rfid/
    │   ├── rfid_reads.csv
    │   └── rfid_events.csv
    └── session_meta.json
```

`rfid_reads.csv` 包含 session、trial、tag、antenna、rssi、reader timestamp 和主机时间戳。`rfid_events.csv` 记录同步事件。`session_meta.json` 保存 subject、action、trial、SkellyCam 请求结果、录制目录和同步协议信息。

### 系统诊断与设置

“系统诊断”会使用当前串口配置连接读写器并持续盘点，实时显示读取到的 EPC 和 RSSI。

“设置”支持：

- 修改界面语言：`auto`、`zh_CN`、`en_US`。
- 扫描串口。
- 查看串口详细信息。
- 验证读写器连接。
- 修改波特率。
- 修改 RFID 帧长度。
- 修改输出目录和输出格式。
- 修改 SkellyCam HTTP base URL。
- 修改 SkellyCam 录制目录。

配置保存在运行目录下的 `config.json`。源码运行时通常位于项目根目录；打包后位于 `dist/RAPT/`。

## 环境依赖

- Python 3.8+
- 依赖库列表见 `requirements.txt`
- 核心依赖为 uhfReaderApi

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python src/main.py
```

### 3. 操作指南

启动后将看到主菜单，可以使用键盘方向键选择功能：

1. **新采集模式**：进入线形/点形采集流程。
2. **标签绑定管理**：扫描新标签并设置名称，或查看已有绑定。
3. **系统设置**：配置串口号、波特率、输出目录等。
4. **检查读写器状态**：测试设备连接是否正常。

## 项目结构

```text
h:\projects\RAPT\
├── docs/               # 文档
├── src/                # 源代码目录
│   ├── main.py         # 程序入口
│   ├── mode.py         # 采集模式逻辑
│   ├── binding.py      # 标签绑定管理器
│   ├── DataCollector.py# 核心数据采集类
│   └── ...
├── example/            # 示例脚本
├── config.json         # 用户配置文件
├── requirements.txt    # Python 依赖
└── README.md           # 说明文档
```

## 开发计划

- [ ] 集成 C++ 模块。
- [ ] 使用PyQT和PyQt Fluent Widgets实现美观的GUI。
- [ ] 整合基于视觉的数据采集功能。
- [ ] 现在使用RS232转USB，未来可加入USB HID支持。




# RAPT (RFID Analysis & Pose Toolkit)

RAPT 是一个面向 RFID RSSI、视频与 SkellyCam 同步实验的数据采集工具。主程序是基于 PyQt6 和 PyQt6-Fluent-Widgets 的 Windows GUI 应用，支持 RFID 读写器连接检查、标签绑定、连续/单次 RFID 采集、摄像头视频采集、RFID + 单摄像头采集，以及 RFID + Skellycam 多摄像头采集。

## 当前功能

### 图形界面

运行 `python src/main.py` 会启动 RAPT GUI。主窗口包含以下页面：

- 总览 (Dashboard)：应用入口与状态总览。
- 采集监控 (Monitor)：RFID 连续采集与单次采集。
- 标签管理 (Tags)：扫描附近标签、绑定 EPC 名称、搜索和删除已保存绑定。
- 视频采集 (Video)：摄像头预览、视频采集、RFID/视频/双模采集。
- 集成采集 (Integrated)：通过 HTTP 控制 SkellyCam，并同步记录 RFID 原始读数。
- 系统诊断 (Diagnostics)：连接读写器并实时显示 EPC/RSSI。
- 设置 (Settings)：串口、波特率、输出目录、输出格式、SkellyCam 地址与录制目录。

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

“采集监控 (Monitor)”提供两类 RFID 采集：

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

“标签管理 (Tags)”用于维护 `binding.json` 中的 EPC 绑定关系。

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

“视频采集 (Video)”使用 OpenCV 和 PyQt6 摄像头接口完成视频预览与录制。

支持三种模式：

- `Joint`：同时启动视频和 RFID 原始采集。
- `Video`：仅录制视频。
- `RFID`：仅记录 RFID 原始读数。

视频文件和帧时间戳 metadata 默认写到：

```text
data/YYYYMMDD/video_mode/
```

RFID 原始模式默认写到：

```text
data/YYYYMMDD/raw_mode/
```

### SkellyCam + RFID 集成采集

“集成采集 (Integrated)”用于联合 SkellyCam 与 RFID。应用会先检查 SkellyCam HTTP 服务，然后：

1. 创建 RAPT session 目录。
2. 启动 RFID raw logging。
3. 调用 SkellyCam `/start_recording`。
4. 支持写入 `sync_start` 和 `sync_end` 同步事件。
5. 停止时调用 SkellyCam `/stop_recording`。
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

“系统诊断 (Diagnostics)”会使用当前串口配置连接读写器并持续盘点，实时显示读取到的 EPC 和 RSSI。

“设置 (Settings)”支持：

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

推荐环境：

- Windows
- Python 3.11
- UHF RFID 读写器及可用 COM 口
- 摄像头，可选
- SkellyCam HTTP 服务，可选，仅集成采集需要

安装 Python 依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

可以用下面的命令快速检查关键依赖：

```powershell
python -c "import PyQt6, qfluentwidgets, cv2, h5py, uhf.reader; print('imports ok')"
```

## 快速开始

### 1. 准备配置

确认 `config.json` 中的串口、波特率、输出目录和 SkellyCam 配置适合当前机器：

```json
{
    "baud": 115200,
    "com": "COM6",
    "frame_duration_ms": 100,
    "output_dir": "data",
    "output_format": "h5",
    "skellycam_base_url": "http://localhost:53117",
    "skellycam_recording_dir": "H:\\lib\\Skellycam_recording"
}
```

也可以启动 GUI 后在“设置 (Settings)”页面修改。

### 2. 启动应用

```powershell
python src/main.py
```

### 3. 推荐采集流程

1. 打开“设置”，扫描串口并验证读写器连接。
2. 打开“系统诊断”，确认能读到 EPC/RSSI。
3. 打开“标签管理”，为实验标签绑定易读名称。
4. 根据实验选择“采集监控”“视频采集”或“集成采集”。
5. 到配置的输出目录中检查生成的数据。

## SkellyCam 集成检查

集成采集前请确认 SkellyCam HTTP 服务已经启动，并且录制目录存在。

可以使用脚本做 smoke test：

```powershell
python scripts/smoke_skellycam.py `
  --base-url http://localhost:53117 `
  --recording-dir H:\lib\Skellycam_recording
```

脚本会依次调用 health check、start recording 和 stop recording。

## 测试

当前仓库包含不依赖真实硬件的集成 session 单元测试：

```powershell
python -m unittest tests/test_integrated_session.py
```

该测试会验证 session 目录创建、RFID CSV、事件 CSV、SkellyCam metadata 和 `session_meta.json` 写入逻辑。

## 从源码构建 dist 下的 .exe

Windows 打包使用仓库内的 `RAPT.spec`。它会收集 qfluentwidgets、uhfReaderApi、资源文件、`config.json` 和 `binding.json`，并生成 GUI 应用。

### 1. 安装构建依赖

建议使用干净的 Python 3.11 环境：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. 构建

在项目根目录运行：

```powershell
python -m PyInstaller --noconfirm --clean RAPT.spec
```

构建结果：

```text
dist/
└── RAPT/
    ├── RAPT.exe
    ├── config.json
    ├── binding.json
    └── _internal/
```

### 3. 运行打包应用

```powershell
.\dist\RAPT\RAPT.exe
```

注意：

- 使用 `dist/RAPT/RAPT.exe`。
- 不要使用旧的 `dist/main.exe`；那是早期 CLI 构建产物，不是当前 GUI 应用。
- 打包后请保持 `config.json` 和 `binding.json` 与 `RAPT.exe` 在同一目录。
- 打包应用运行时会在可执行程序所在目录读写配置、绑定和相对输出路径。

### 4. 可选图标

PyInstaller 的 Windows exe 图标需要 `.ico` 文件。可以将：

```text
src/resources/RAPT_icon.png
```

转换为：

```text
src/resources/RAPT_icon.ico
```

然后在 `RAPT.spec` 的 `EXE(...)` 中加入：

```python
icon="src/resources/RAPT_icon.ico",
```

## 项目结构

```text
RAPT/
├── README.md
├── BUILD.md
├── RAPT.spec
├── config.json
├── binding.json
├── requirements.txt
├── scripts/
│   └── smoke_skellycam.py
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── DataCollector.py
│   │   ├── binding.py
│   │   ├── check_status.py
│   │   ├── integrated_session.py
│   │   ├── paths.py
│   │   ├── settings.py
│   │   └── skellycam_client.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── threads.py
│   │   └── views/
│   ├── utils/
│   │   └── serial_utils.py
│   └── resources/
├── tests/
│   └── test_integrated_session.py
├── build/
└── dist/
```

## 备注
。
- `src/core/main.py` 和部分 questionary workflow 保留了早期 CLI 逻辑s。
- RFID、视频、SkellyCam 分别依赖真实硬件或服务；没有硬件时仍可运行不依赖硬件的单元测试。

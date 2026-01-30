# RAPT (RFID Analysis & Pose Toolkit)

RAPT 是一个基于 Python 的 RFID 数据采集与管理工具。

## 功能特性

- **多模式数据采集**
  - **线形采集**：支持持续采集（手动停止）和定时采集。
  - **点形采集**：支持手动触发采集（每次采集固定时间）。
- **标签绑定管理**
  - 将 EPC 代码绑定为指定的部位。
  - 支持持久化存储绑定关系 (`binding.json`)。
- **设备交互**
  - 基于 Python包 uhfReaderApi 连接RFID读写器。
  - 支持RS232（Serial/COM）连接。
  - 使用6C规格天线。
  - 可配置波特率、射频功率、天线端口等参数。
- **CLI 界面**
  - 使用 `rich` 和 `questionary` 构建。
- **扩展性**
  - 预留 C++ 扩展接口（规划中），用于高性能数据处理。

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




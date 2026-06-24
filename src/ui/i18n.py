# -*- coding: utf-8 -*-
from __future__ import annotations

import locale as system_locale


LOCALE_AUTO = "auto"
LOCALE_ZH_CN = "zh_CN"
LOCALE_EN_US = "en_US"

LOCALE_OPTIONS = (
    (LOCALE_AUTO, "跟随系统", "System"),
    (LOCALE_ZH_CN, "简体中文", "Chinese"),
    (LOCALE_EN_US, "English", "English"),
)


TRANSLATIONS = {
    LOCALE_ZH_CN: {
        "app.window_title": "RAPT",
        "nav.home": "总览",
        "nav.collect": "采集监控",
        "nav.tags": "标签管理",
        "nav.video": "视频采集",
        "nav.integrated": "集成采集",
        "nav.diagnostics": "系统诊断",
        "nav.settings": "设置",
        "home.title": "欢迎使用 RAPT",
        "home.description": "面向 RFID RSSI、视频与 SkellyCam 同步实验的数据采集工具。以下指南帮助您快速上手。",
        "home.quick_start": "快速开始",
        "home.step1_title": "配置串口与波特率",
        "home.step1_desc": "前往「设置」页面，选择 RFID 读写器对应的 COM 口和波特率。",
        "home.step2_title": "连接 RFID 读写器",
        "home.step2_desc": "将读写器通过 USB 转串口接入电脑，确认设备管理器中可识别。",
        "home.step3_title": "准备摄像头",
        "home.step3_desc": "如需视频采集，打开 SkellyCam 服务或在「视频采集」页面选择本地摄像头。",
        "home.step4_title": "开始采集",
        "home.step4_desc": "前往「集成采集」或「采集监控」页面，填写试验信息后点击开始。",
        "home.features": "功能概览",
        "home.feat_tags_title": "标签管理",
        "home.feat_tags_desc": "绑定 RFID 标签与受试者信息，支持批量导入导出。",
        "home.feat_monitor_title": "采集监控",
        "home.feat_monitor_desc": "实时查看 RFID 读数、RSSI 曲线与事件标记。",
        "home.feat_diag_title": "系统诊断",
        "home.feat_diag_desc": "检测读写器、摄像头与 SkellyCam 服务的连接状态。",
        "video.title": "视频 / RFID + 单摄像头采集",
        "video.camera": "摄像头:",
        "video.start_capture": "开始采集",
        "video.joint": "RFID+摄像头",
        "video.video_only": "仅视频",
        "video.rfid_only": "仅RFID",
        "integrated.title": "RFID + SkellyCam 多摄像头采集",
        "integrated.subject_id": "受试者 ID",
        "integrated.action": "动作",
        "integrated.trial_id": "试次 ID",
        "integrated.recording_name": "SkellyCam 录制名",
        "integrated.notes": "备注",
        "integrated.skellycam_url": "SkellyCam 地址",
        "integrated.recording_dir": "SkellyCam 录制目录",
        "integrated.health": "服务状态",
        "integrated.browse": "浏览",
        "integrated.check": "检查 SkellyCam",
        "integrated.start": "开始集成采集",
        "integrated.sync_start": "写入 sync_start",
        "integrated.sync_end": "写入 sync_end",
        "integrated.stop": "停止采集",
        "settings.language_group": "界面",
        "settings.language": "界面语言",
        "settings.language_desc": "选择界面显示语言，重启后生效",
        "settings.language_saved_title": "语言已更新",
        "settings.language_saved_content": "重启 RAPT 后生效",
    },
    LOCALE_EN_US: {
        "app.window_title": "RAPT",
        "nav.home": "Dashboard",
        "nav.collect": "Monitor",
        "nav.tags": "Tags",
        "nav.video": "Video",
        "nav.integrated": "Integrated",
        "nav.diagnostics": "Diagnostics",
        "nav.settings": "Settings",
        "home.title": "Welcome to RAPT",
        "home.description": "Data collection for RFID RSSI, video, and SkellyCam synchronized experiments. Follow the guide below to get started.",
        "home.quick_start": "Quick Start",
        "home.step1_title": "Configure Serial Port & Baud Rate",
        "home.step1_desc": "Go to Settings and select the COM port and baud rate for your RFID reader.",
        "home.step2_title": "Connect the RFID Reader",
        "home.step2_desc": "Plug in the reader via USB-serial adapter and verify it appears in Device Manager.",
        "home.step3_title": "Prepare Camera",
        "home.step3_desc": "For video capture, start the SkellyCam service or select a local camera in the Video page.",
        "home.step4_title": "Start Collecting",
        "home.step4_desc": "Navigate to Integrated or Monitor page, fill in trial info, and click Start.",
        "home.features": "Features",
        "home.feat_tags_title": "Tag Management",
        "home.feat_tags_desc": "Bind RFID tags to subject info with batch import/export support.",
        "home.feat_monitor_title": "Capture Monitor",
        "home.feat_monitor_desc": "Real-time RFID reads, RSSI curves, and event markers.",
        "home.feat_diag_title": "System Diagnostics",
        "home.feat_diag_desc": "Check connectivity of reader, camera, and SkellyCam service.",
        "video.title": "Video / RFID + Single Camera",
        "video.camera": "Camera:",
        "video.start_capture": "Start",
        "video.joint": "RFID+Camera",
        "video.video_only": "Video Only",
        "video.rfid_only": "RFID Only",
        "integrated.title": "RFID + SkellyCam Multi-Camera Capture",
        "integrated.subject_id": "Subject ID",
        "integrated.action": "Action",
        "integrated.trial_id": "Trial ID",
        "integrated.recording_name": "SkellyCam Recording",
        "integrated.notes": "Notes",
        "integrated.skellycam_url": "SkellyCam URL",
        "integrated.recording_dir": "SkellyCam Directory",
        "integrated.health": "Health",
        "integrated.browse": "Browse",
        "integrated.check": "Check SkellyCam",
        "integrated.start": "Start Integrated Capture",
        "integrated.sync_start": "Write sync_start",
        "integrated.sync_end": "Write sync_end",
        "integrated.stop": "Stop",
        "settings.language_group": "Interface",
        "settings.language": "Language",
        "settings.language_desc": "Choose the interface language. Restart required.",
        "settings.language_saved_title": "Language Updated",
        "settings.language_saved_content": "Restart RAPT to apply the change.",
    },
}


def normalize_locale(value: str | None) -> str:
    normalized = (value or "").replace("-", "_").lower()
    if normalized.startswith("zh"):
        return LOCALE_ZH_CN
    if normalized.startswith("en"):
        return LOCALE_ZH_CN
    return LOCALE_ZH_CN


def get_system_locale() -> str:
    try:
        lang, _ = system_locale.getlocale()
    except Exception:
        lang = None
    return normalize_locale(lang)


def resolve_locale(config=None) -> str:
    value = getattr(config, "locale", LOCALE_AUTO)
    if value == LOCALE_AUTO:
        return get_system_locale()
    return normalize_locale(value)


def t(key: str, config=None) -> str:
    lang = resolve_locale(config)
    return TRANSLATIONS.get(lang, TRANSLATIONS[LOCALE_ZH_CN]).get(
        key, TRANSLATIONS[LOCALE_ZH_CN].get(key, key)
    )


def locale_label(code: str, config=None) -> str:
    active_lang = resolve_locale(config)
    for item_code, zh_label, en_label in LOCALE_OPTIONS:
        if item_code == code:
            return en_label if active_lang == LOCALE_EN_US else zh_label
    return code


def locale_code_from_label(label: str) -> str:
    for code, zh_label, en_label in LOCALE_OPTIONS:
        if label in (zh_label, en_label):
            return code
    return LOCALE_AUTO

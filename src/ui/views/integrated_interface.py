# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QFormLayout, QFileDialog
from qfluentwidgets import (
    SubtitleLabel,
    CardWidget,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    BodyLabel,
    StrongBodyLabel,
    InfoBar,
    InfoBarPosition,
)

from core.settings import ConfigManager
from core.integrated_session import build_recording_name
from ui.i18n import t
from ui.threads import IntegratedRecordingThread, SkellyCamHealthThread


class IntegratedInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("integratedInterface")

        self.config = ConfigManager()
        self.recordingThread = None
        self.healthThread = None

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        self.titleLabel = SubtitleLabel(t("integrated.title", self.config), self)
        self.vBoxLayout.addWidget(self.titleLabel)

        self.contentLayout = QHBoxLayout()
        self.vBoxLayout.addLayout(self.contentLayout, 1)

        self.formCard = CardWidget(self)
        self.formLayout = QFormLayout(self.formCard)
        self.formLayout.setContentsMargins(20, 20, 20, 20)
        self.formLayout.setSpacing(14)

        self.subjectEdit = LineEdit(self.formCard)
        self.subjectEdit.setPlaceholderText("sub001")
        self.actionEdit = LineEdit(self.formCard)
        self.actionEdit.setPlaceholderText("squat")
        self.trialEdit = LineEdit(self.formCard)
        self.trialEdit.setPlaceholderText("trial001")
        self.notesEdit = QPlainTextEdit(self.formCard)
        self.notesEdit.setPlaceholderText("备注")
        self.notesEdit.setFixedHeight(90)

        self.recordingNameEdit = LineEdit(self.formCard)
        self.recordingNameEdit.setReadOnly(True)
        self.recordingNameEdit.setText(self._recording_name())

        self.healthLabel = StrongBodyLabel("SkellyCam: 未检查", self.formCard)
        self.baseUrlLabel = BodyLabel(self.config.skellycam_base_url, self.formCard)

        self.dirEdit = LineEdit(self.formCard)
        self.dirEdit.setReadOnly(True)
        self.dirEdit.setText(self.config.skellycam_recording_dir)
        self.dirBrowseBtn = PushButton(t("integrated.browse", self.config), self.formCard)
        self.dirBrowseBtn.setFixedWidth(60)
        self.dirRow = QWidget(self.formCard)
        self.dirRowLayout = QHBoxLayout(self.dirRow)
        self.dirRowLayout.setContentsMargins(0, 0, 0, 0)
        self.dirRowLayout.setSpacing(8)
        self.dirRowLayout.addWidget(self.dirEdit, 1)
        self.dirRowLayout.addWidget(self.dirBrowseBtn, 0)

        self.formLayout.addRow(t("integrated.subject_id", self.config), self.subjectEdit)
        self.formLayout.addRow(t("integrated.action", self.config), self.actionEdit)
        self.formLayout.addRow(t("integrated.trial_id", self.config), self.trialEdit)
        self.formLayout.addRow(t("integrated.recording_name", self.config), self.recordingNameEdit)
        self.formLayout.addRow(t("integrated.notes", self.config), self.notesEdit)
        self.formLayout.addRow(t("integrated.skellycam_url", self.config), self.baseUrlLabel)
        self.formLayout.addRow(t("integrated.recording_dir", self.config), self.dirRow)
        self.formLayout.addRow(t("integrated.health", self.config), self.healthLabel)

        self.contentLayout.addWidget(self.formCard, 1)

        self.logCard = CardWidget(self)
        self.logLayout = QVBoxLayout(self.logCard)
        self.statusLabel = StrongBodyLabel("采集状态: 就绪", self.logCard)
        self.logDisplay = QPlainTextEdit(self.logCard)
        self.logDisplay.setReadOnly(True)
        font = self.logDisplay.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.logDisplay.setFont(font)
        self.logLayout.addWidget(self.statusLabel)
        self.logLayout.addWidget(self.logDisplay, 1)
        self.contentLayout.addWidget(self.logCard, 1)

        self.controlCard = CardWidget(self)
        self.controlLayout = QHBoxLayout(self.controlCard)
        self.controlLayout.setContentsMargins(12, 12, 12, 12)
        self.checkBtn = PushButton(t("integrated.check", self.config), self.controlCard)
        self.startBtn = PrimaryPushButton(t("integrated.start", self.config), self.controlCard)
        self.syncStartBtn = PushButton(t("integrated.sync_start", self.config), self.controlCard)
        self.syncEndBtn = PushButton(t("integrated.sync_end", self.config), self.controlCard)
        self.stopBtn = PushButton(t("integrated.stop", self.config), self.controlCard)
        self.controlLayout.addWidget(self.checkBtn)
        self.controlLayout.addWidget(self.startBtn)
        self.controlLayout.addWidget(self.syncStartBtn)
        self.controlLayout.addWidget(self.syncEndBtn)
        self.controlLayout.addStretch(1)
        self.controlLayout.addWidget(self.stopBtn)
        self.vBoxLayout.addWidget(self.controlCard)

        self.syncStartBtn.setEnabled(False)
        self.syncEndBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)

        self.subjectEdit.textChanged.connect(self._update_recording_name)
        self.actionEdit.textChanged.connect(self._update_recording_name)
        self.trialEdit.textChanged.connect(self._update_recording_name)
        self.checkBtn.clicked.connect(self.check_skellycam)
        self.startBtn.clicked.connect(self.start_recording)
        self.stopBtn.clicked.connect(self.stop_recording)
        self.syncStartBtn.clicked.connect(lambda: self.write_sync_event("sync_start"))
        self.syncEndBtn.clicked.connect(lambda: self.write_sync_event("sync_end"))
        self.dirBrowseBtn.clicked.connect(self._browse_recording_dir)

    def _recording_name(self):
        return build_recording_name(
            self.subjectEdit.text() or "sub001",
            self.actionEdit.text() or "action",
            self.trialEdit.text() or "trial001",
        )

    def _update_recording_name(self):
        self.recordingNameEdit.setText(self._recording_name())

    def _browse_recording_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择 SkellyCam 录制目录", self.config.skellycam_recording_dir
        )
        if directory:
            self.config.skellycam_recording_dir = directory
            self.dirEdit.setText(directory)
            self.config.save()

    def append_log(self, text):
        self.logDisplay.appendPlainText(text)
        sb = self.logDisplay.verticalScrollBar()
        sb.setValue(sb.maximum())

    def check_skellycam(self):
        self.checkBtn.setEnabled(False)
        self.healthLabel.setText("SkellyCam: 检查中...")
        self.append_log(f"GET {self.config.skellycam_base_url}/health")
        self.healthThread = SkellyCamHealthThread(self.config.skellycam_base_url, self)
        self.healthThread.finished.connect(self.on_health_checked)
        self.healthThread.start()

    def on_health_checked(self, ok, message):
        self.checkBtn.setEnabled(True)
        if ok:
            self.healthLabel.setText("SkellyCam: OK")
            self.append_log(f"[SkellyCam Health] {message}")
        else:
            self.healthLabel.setText("SkellyCam: 失败")
            self.append_log(f"[SkellyCam Health Error] {message}")

    def start_recording(self):
        if self.recordingThread and self.recordingThread.isRunning():
            return
        subject_id = self.subjectEdit.text().strip() or "sub001"
        action = self.actionEdit.text().strip() or "action"
        trial_id = self.trialEdit.text().strip() or "trial001"
        notes = self.notesEdit.toPlainText().strip()

        self.logDisplay.clear()
        self.append_log("检查 SkellyCam 并启动 RFID raw logging...")
        self.recordingThread = IntegratedRecordingThread(
            self.config, subject_id, action, trial_id, notes, self
        )
        self.recordingThread.started_info.connect(self.on_recording_started)
        self.recordingThread.progress_update.connect(self.on_progress)
        self.recordingThread.saved.connect(self.on_recording_saved)
        self.recordingThread.error.connect(self.on_recording_error)
        self.recordingThread.finished.connect(self.on_recording_thread_finished)
        self.recordingThread.start()

        self.startBtn.setEnabled(False)
        self.checkBtn.setEnabled(False)
        self.syncStartBtn.setEnabled(False)
        self.syncEndBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.subjectEdit.setEnabled(False)
        self.actionEdit.setEnabled(False)
        self.trialEdit.setEnabled(False)
        self.notesEdit.setEnabled(False)
        self.statusLabel.setText("采集状态: 启动中")

    def on_recording_started(self, info):
        self.statusLabel.setText("采集状态: 进行中")
        self.syncStartBtn.setEnabled(True)
        self.syncEndBtn.setEnabled(True)
        self.append_log(f"[Session] {info['session_id']}")
        self.append_log(f"[Folder] {info['session_dir']}")
        self.append_log(f"[SkellyCam Start] {info.get('skellycam_response', '')}")

    def on_progress(self, data):
        self.append_log(f"RFID reads={data['read_count']} last={data['last_epc']}")

    def write_sync_event(self, event_type):
        if not self.recordingThread:
            return
        event = self.recordingThread.add_sync_event(event_type)
        if event:
            self.append_log(f"[Event] {event_type} {event['host_perf_counter_ns']}")

    def stop_recording(self):
        if self.recordingThread and self.recordingThread.isRunning():
            self.statusLabel.setText("采集状态: 正在停止")
            self.stopBtn.setEnabled(False)
            self.recordingThread.stop()

    def on_recording_saved(self, meta_path):
        self.append_log(f"[Saved] {meta_path}")
        had_error = bool(self.recordingThread and getattr(self.recordingThread, "_had_error", False))
        self.statusLabel.setText("采集状态: 错误" if had_error else "采集状态: 完成")
        self._reset_controls()
        if not had_error:
            InfoBar.success(
                title="集成采集完成",
                content="session_meta.json 与 RFID CSV 已保存",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT,
            )

    def on_recording_error(self, message):
        self.append_log(f"[Error] {message}")
        self.statusLabel.setText("采集状态: 错误")
        if not (self.recordingThread and self.recordingThread.isRunning()):
            self._reset_controls()

    def on_recording_thread_finished(self):
        if self.statusLabel.text().endswith("错误"):
            self._reset_controls()

    def _reset_controls(self):
        self.startBtn.setEnabled(True)
        self.checkBtn.setEnabled(True)
        self.syncStartBtn.setEnabled(False)
        self.syncEndBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)
        self.subjectEdit.setEnabled(True)
        self.actionEdit.setEnabled(True)
        self.trialEdit.setEnabled(True)
        self.notesEdit.setEnabled(True)

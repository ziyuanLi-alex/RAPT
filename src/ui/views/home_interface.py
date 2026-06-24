from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    ScrollArea,
    SubtitleLabel,
    BodyLabel,
    CardWidget,
    IconWidget,
    FluentIcon as FIF,
    StrongBodyLabel,
)

from core.settings import ConfigManager
from ui.i18n import t


class _StepCard(CardWidget):
    def __init__(self, number: int, title: str, description: str, icon, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        num_label = SubtitleLabel(str(number), self)
        num_label.setFixedWidth(28)
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_label.setStyleSheet("color: #009faa; font-size: 20px; font-weight: bold;")

        icon_widget = IconWidget(icon, self)
        icon_widget.setFixedSize(24, 24)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = StrongBodyLabel(title, self)
        desc_label = BodyLabel(description, self)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888;")
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        layout.addWidget(num_label)
        layout.addWidget(icon_widget)
        layout.addLayout(text_layout, 1)


class _InfoCard(CardWidget):
    def __init__(self, icon, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        icon_widget = IconWidget(icon, self)
        icon_widget.setFixedSize(22, 22)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = StrongBodyLabel(title, self)
        desc_label = BodyLabel(description, self)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888;")
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        layout.addWidget(icon_widget)
        layout.addLayout(text_layout, 1)


class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")

        self.config = ConfigManager()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(36, 24, 36, 24)
        root.setSpacing(16)

        root.addWidget(SubtitleLabel(t("home.title", self.config), self))

        desc = BodyLabel(t("home.description", self.config), self)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaa; font-size: 13px;")
        root.addWidget(desc)

        root.addWidget(StrongBodyLabel(t("home.quick_start", self.config), self))

        steps = [
            (FIF.SETTING, t("home.step1_title", self.config), t("home.step1_desc", self.config)),
            (FIF.IOT,     t("home.step2_title", self.config), t("home.step2_desc", self.config)),
            (FIF.CAMERA,  t("home.step3_title", self.config), t("home.step3_desc", self.config)),
            (FIF.PLAY,    t("home.step4_title", self.config), t("home.step4_desc", self.config)),
        ]
        for i, (icon, title, desc_text) in enumerate(steps, 1):
            root.addWidget(_StepCard(i, title, desc_text, icon, self))

        root.addSpacing(4)

        root.addWidget(StrongBodyLabel(t("home.features", self.config), self))

        features = [
            (FIF.TAG,   t("home.feat_tags_title", self.config),    t("home.feat_tags_desc", self.config)),
            (FIF.PLAY,  t("home.feat_monitor_title", self.config), t("home.feat_monitor_desc", self.config)),
            (FIF.HEART, t("home.feat_diag_title", self.config),    t("home.feat_diag_desc", self.config)),
        ]
        for icon, title, desc_text in features:
            root.addWidget(_InfoCard(icon, title, desc_text, self))

        root.addStretch(1)

        scroll.setWidget(container)
        outer.addWidget(scroll)

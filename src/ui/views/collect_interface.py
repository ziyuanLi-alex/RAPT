from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel

class CollectInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("collectInterface")
        
        layout = QVBoxLayout(self)
        layout.addWidget(SubtitleLabel("采集监控界面 (开发中)", self))
        layout.addStretch(1)

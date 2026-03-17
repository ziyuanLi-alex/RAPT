# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QSize
from qfluentwidgets import (
    SubtitleLabel, SegmentedWidget, CardWidget, LineEdit, 
    PrimaryPushButton, BodyLabel, StrongBodyLabel,
    InfoBar, InfoBarPosition, SearchLineEdit, ToolButton, FluentIcon
)

from core.settings import ConfigManager
from core.binding import BindingManager
from ..threads import TagScanThread
import json

class TagsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("tagsInterface")
        
        self.config = ConfigManager()
        self.binder = BindingManager(self.config)
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(20)

        # Header
        self.headerLayout = QHBoxLayout()
        self.titleLabel = SubtitleLabel("标签管理", self)
        
        self.pivot = SegmentedWidget(self)
        self.pivot.addItem("Binding", "绑定管理")
        self.pivot.addItem("Database", "已存列表")
        self.pivot.setCurrentItem("Binding")
        self.pivot.currentItemChanged.connect(self.onPivotChanged)
        
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.pivot)
        
        self.vBoxLayout.addLayout(self.headerLayout)

        # Content
        self.stackedWidget = QStackedWidget(self)
        self.bindingView = BindingView(self)
        self.databaseView = DatabaseView(self)
        
        self.stackedWidget.addWidget(self.bindingView)
        self.stackedWidget.addWidget(self.databaseView)
        
        self.vBoxLayout.addWidget(self.stackedWidget)

    def onPivotChanged(self, key):
        if key == "Binding":
            self.stackedWidget.setCurrentWidget(self.bindingView)
        else:
            self.databaseView.refreshTable()
            self.stackedWidget.setCurrentWidget(self.databaseView)


class BindingView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_interface = parent
        
        self.hLayout = QHBoxLayout(self)
        self.hLayout.setContentsMargins(0, 0, 0, 0)
        
        # Left: Scan & List
        self.leftContainer = QWidget()
        self.leftLayout = QVBoxLayout(self.leftContainer)
        self.leftLayout.setContentsMargins(0, 0, 10, 0)
        
        self.scanBtn = PrimaryPushButton("扫描附近标签", self.leftContainer)
        self.scanBtn.clicked.connect(self.startScan)
        
        self.epcList = QListWidget(self.leftContainer)
        self.epcList.itemClicked.connect(self.onItemClicked)
        
        self.leftLayout.addWidget(self.scanBtn)
        self.leftLayout.addWidget(self.epcList)
        
        # Right: Details & Edit
        self.rightContainer = CardWidget(self)
        self.rightLayout = QVBoxLayout(self.rightContainer)
        self.rightLayout.setContentsMargins(20, 20, 20, 20)
        self.rightLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.detailTitle = StrongBodyLabel("标签详情", self.rightContainer)
        
        self.epcLabel = BodyLabel("EPC:", self.rightContainer)
        self.epcValue = LineEdit(self.rightContainer)
        self.epcValue.setReadOnly(True)
        
        self.nameLabel = BodyLabel("绑定名称 (Label):", self.rightContainer)
        self.nameEdit = LineEdit(self.rightContainer)
        self.nameEdit.setPlaceholderText("请输入易读的名称")
        
        self.saveBtn = PrimaryPushButton("保存绑定", self.rightContainer)
        self.saveBtn.clicked.connect(self.saveBinding)
        self.saveBtn.setEnabled(False)
        
        self.delBtn = PrimaryPushButton("删除绑定", self.rightContainer)
        self.delBtn.clicked.connect(self.deleteBinding)
        self.delBtn.setEnabled(False)
        # Set delete button style to red/danger if possible, or just keep it standard
        # self.delBtn.setStyleSheet("background-color: #d00000; color: white;") 
        
        self.rightLayout.addWidget(self.detailTitle)
        self.rightLayout.addSpacing(20)
        self.rightLayout.addWidget(self.epcLabel)
        self.rightLayout.addWidget(self.epcValue)
        self.rightLayout.addSpacing(10)
        self.rightLayout.addWidget(self.nameLabel)
        self.rightLayout.addWidget(self.nameEdit)
        self.rightLayout.addSpacing(20)
        
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.saveBtn)
        btnLayout.addWidget(self.delBtn)
        self.rightLayout.addLayout(btnLayout)
        
        self.rightLayout.addStretch(1)
        
        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.leftContainer)
        self.splitter.addWidget(self.rightContainer)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        
        self.hLayout.addWidget(self.splitter)
        
        self.scanThread = None

    def startScan(self):
        self.scanBtn.setEnabled(False)
        self.scanBtn.setText("扫描中...")
        self.epcList.clear()
        
        self.scanThread = TagScanThread(self)
        self.scanThread.tags_found.connect(self.onTagsFound)
        self.scanThread.error.connect(self.onError)
        self.scanThread.finished.connect(self.onScanFinished)
        self.scanThread.start()

    def onTagsFound(self, epcs):
        if not epcs:
            InfoBar.warning(
                title='未发现标签',
                content='请确认读写器已连接且附近有标签',
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT
            )
            return
            
        for epc in epcs:
            item = QListWidgetItem(epc)
            # Check if bound
            name = self.parent_interface.binder.get_name(epc)
            if name != epc:
                item.setText(f"{epc} ({name})")
                item.setForeground(Qt.GlobalColor.darkGreen)
            self.epcList.addItem(item)
            
        InfoBar.success(
            title='扫描完成',
            content=f"发现 {len(epcs)} 个标签",
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT
        )

    def onError(self, msg):
        InfoBar.error(title='扫描错误', content=msg, parent=self.window(), position=InfoBarPosition.TOP_RIGHT)

    def onScanFinished(self):
        self.scanBtn.setEnabled(True)
        self.scanBtn.setText("扫描附近标签")

    def onItemClicked(self, item):
        full_text = item.text()
        epc = full_text.split(" (")[0] # Extract EPC
        self.epcValue.setText(epc)
        
        # Load existing name
        name = self.parent_interface.binder.get_name(epc)
        if name == epc:
            self.nameEdit.setText("")
            self.delBtn.setEnabled(False) # Not bound
        else:
            self.nameEdit.setText(name)
            self.delBtn.setEnabled(True) # Bound
            
        self.saveBtn.setEnabled(True)
        self.nameEdit.setFocus()

    def deleteBinding(self):
        epc = self.epcValue.text()
        if not epc:
            return
            
        if self.parent_interface.binder.remove_binding(epc):
            # Update UI
            self.nameEdit.setText("")
            self.delBtn.setEnabled(False)
            
            # Update List Item
            items = self.epcList.findItems(epc, Qt.MatchFlag.MatchStartsWith)
            for item in items:
                item.setText(epc)
                item.setForeground(Qt.GlobalColor.black) # Reset color
                
            InfoBar.success(
                title='删除成功',
                content=f"已移除 {epc} 的绑定",
                parent=self.window(),
                position=InfoBarPosition.TOP_RIGHT
            )

    def saveBinding(self):
        epc = self.epcValue.text()
        name = self.nameEdit.text().strip()
        
        if not epc:
            return
            
        if not name:
            InfoBar.warning(title='名称为空', content='请输入有效的绑定名称', parent=self.window(), position=InfoBarPosition.TOP_RIGHT)
            return
            
        self.parent_interface.binder.bind(epc, name)
        
        # Update List Item
        items = self.epcList.findItems(epc, Qt.MatchFlag.MatchStartsWith)
        for item in items:
            item.setText(f"{epc} ({name})")
            item.setForeground(Qt.GlobalColor.darkGreen)
            
        self.delBtn.setEnabled(True) # Now bound
            
        InfoBar.success(
            title='绑定成功',
            content=f"{epc} -> {name}",
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT
        )


class DatabaseView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_interface = parent
        
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = QHBoxLayout()
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText("搜索 EPC 或 名称")
        self.searchEdit.textChanged.connect(self.filterTable)
        
        self.refreshBtn = ToolButton(FluentIcon.SYNC, self)
        self.refreshBtn.clicked.connect(self.refreshTable)
        
        self.deleteBtn = ToolButton(FluentIcon.DELETE, self)
        self.deleteBtn.clicked.connect(self.deleteSelected)
        self.deleteBtn.setEnabled(False)
        
        self.toolbar.addWidget(self.searchEdit)
        self.toolbar.addWidget(self.refreshBtn)
        self.toolbar.addWidget(self.deleteBtn)
        self.toolbar.addStretch(1)
        
        self.vLayout.addLayout(self.toolbar)
        
        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["EPC", "绑定名称"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.onSelectionChanged)
        self.vLayout.addWidget(self.table)
        
        self.refreshTable()

    def onSelectionChanged(self):
        self.deleteBtn.setEnabled(len(self.table.selectedItems()) > 0)

    def deleteSelected(self):
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            return
            
        for row in sorted(list(selected_rows), reverse=True):
            epc = self.table.item(row, 0).text()
            self.parent_interface.binder.remove_binding(epc)
            
        self.refreshTable()
        InfoBar.success(
            title='删除完成',
            content=f"已删除 {len(selected_rows)} 个绑定",
            parent=self.window(),
            position=InfoBarPosition.TOP_RIGHT
        )

    def refreshTable(self):
        self.table.setRowCount(0)
        self.deleteBtn.setEnabled(False)
        bind_dict = self.parent_interface.binder.bind_dict
        
        for epc, name in bind_dict.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(epc))
            self.table.setItem(row, 1, QTableWidgetItem(name))

    def filterTable(self, text):
        text = text.lower()
        for r in range(self.table.rowCount()):
            epc = self.table.item(r, 0).text().lower()
            name = self.table.item(r, 1).text().lower()
            if text in epc or text in name:
                self.table.setRowHidden(r, False)
            else:
                self.table.setRowHidden(r, True)

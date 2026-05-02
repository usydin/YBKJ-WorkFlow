from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QMessageBox,
)

from app.database import SQLiteDataPool


class EmployeePage(QFrame):
    updated = Signal()

    def __init__(self, data_pool: SQLiteDataPool) -> None:
        super().__init__()
        self.data_pool = data_pool
        self.logger = logging.getLogger("ybkj_workflow.ui.employee")
        self.current_alias_id: int | None = None
        
        self.setObjectName("PlaceholderCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title_label = QLabel("员工映射管理")
        title_label.setObjectName("PlaceholderTitle")
        
        desc_label = QLabel(
            "微信网名不一定是真实姓名。请在此维护员工真实姓名、微信网名和常用别名。系统后续将根据该表自动映射维修人员字段。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_toolbar())
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        content_layout.addWidget(self._build_table(), 2)
        content_layout.addWidget(self._build_editor(), 1)
        
        layout.addLayout(content_layout, 1)
        
        self.refresh_page()

    def _build_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索真实姓名/网名/别名/班组/备注...")
        self.search_input.setObjectName("InputBox")
        self.search_input.textChanged.connect(self.refresh_page)

        self.show_inactive_check = QCheckBox("显示停用人员")
        self.show_inactive_check.stateChanged.connect(self.refresh_page)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        new_button = QPushButton("新增映射")
        new_button.setObjectName("PrimaryButton")
        new_button.clicked.connect(self.clear_form)

        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.show_inactive_check)
        layout.addWidget(refresh_button)
        layout.addWidget(new_button)
        return layout

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "ID", "真实姓名", "微信网名", "常用别名", "班组", "状态", "备注", "更新时间"
        ])
        self.table.setObjectName("InputArea")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.load_selected_alias)
        return self.table

    def _build_editor(self) -> QFrame:
        editor = QFrame()
        editor.setObjectName("PlaceholderCard")
        editor.setStyleSheet("background-color: transparent; border: 1px solid #334155; border-radius: 12px;")
        
        layout = QVBoxLayout(editor)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        editor_title = QLabel("映射详情编辑")
        editor_title.setObjectName("PlaceholderTitle")
        layout.addWidget(editor_title)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)

        self.real_name_input = QLineEdit()
        self.real_name_input.setObjectName("InputBox")
        self.wechat_nickname_input = QLineEdit()
        self.wechat_nickname_input.setObjectName("InputBox")
        self.alias_input = QLineEdit()
        self.alias_input.setObjectName("InputBox")
        self.team_input = QLineEdit()
        self.team_input.setObjectName("InputBox")
        self.is_active_check = QCheckBox("启用该映射")
        self.is_active_check.setChecked(True)
        self.note_input = QPlainTextEdit()
        self.note_input.setObjectName("InputArea")
        self.note_input.setMaximumHeight(100)

        form_layout.addRow("真实姓名*", self.real_name_input)
        form_layout.addRow("微信网名", self.wechat_nickname_input)
        form_layout.addRow("常用别名", self.alias_input)
        form_layout.addRow("班组", self.team_input)
        form_layout.addRow("状态", self.is_active_check)
        form_layout.addRow("备注", self.note_input)

        layout.addWidget(form_widget)

        btn_layout = QHBoxLayout()
        self.save_button = QPushButton("保存修改")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.save_alias)

        self.toggle_active_button = QPushButton("停用/启用")
        self.toggle_active_button.setObjectName("SecondaryButton")
        self.toggle_active_button.clicked.connect(self.toggle_alias_status)

        self.clear_button = QPushButton("清空")
        self.clear_button.setObjectName("SecondaryButton")
        self.clear_button.clicked.connect(self.clear_form)

        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.toggle_active_button)
        btn_layout.addWidget(self.clear_button)
        layout.addLayout(btn_layout)
        
        layout.addStretch(1)
        return editor

    def refresh_page(self) -> None:
        keyword = self.search_input.text().strip()
        include_inactive = self.show_inactive_check.isChecked()
        
        aliases = self.data_pool.list_employee_aliases(include_inactive, keyword)
        
        self.table.setRowCount(len(aliases))
        for i, a in enumerate(aliases):
            status_text = "启用" if a.get("is_active") else "停用"
            items = [
                str(a.get("id")),
                str(a.get("real_name")),
                str(a.get("wechat_nickname", "")),
                str(a.get("alias", "")),
                str(a.get("team", "")),
                status_text,
                str(a.get("note", "")),
                str(a.get("updated_at")),
            ]
            for j, val in enumerate(items):
                item = QTableWidgetItem(val)
                if status_text == "停用":
                    item.setForeground(Qt.GlobalColor.gray)
                self.table.setItem(i, j, item)
        
        self.table.resizeColumnsToContents()

    def load_selected_alias(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
            
        alias_id = int(selected[0].text())
        alias = self.data_pool.get_employee_alias(alias_id)
        if not alias:
            return
            
        self.current_alias_id = alias_id
        self.real_name_input.setText(str(alias.get("real_name")))
        self.wechat_nickname_input.setText(str(alias.get("wechat_nickname", "")))
        self.alias_input.setText(str(alias.get("alias", "")))
        self.team_input.setText(str(alias.get("team", "")))
        self.is_active_check.setChecked(bool(alias.get("is_active")))
        self.note_input.setPlainText(str(alias.get("note", "")))

    def clear_form(self) -> None:
        self.current_alias_id = None
        self.real_name_input.clear()
        self.wechat_nickname_input.clear()
        self.alias_input.clear()
        self.team_input.clear()
        self.is_active_check.setChecked(True)
        self.note_input.clear()
        self.table.clearSelection()

    def save_alias(self) -> None:
        data = {
            "real_name": self.real_name_input.text().strip(),
            "wechat_nickname": self.wechat_nickname_input.text().strip(),
            "alias": self.alias_input.text().strip(),
            "team": self.team_input.text().strip(),
            "is_active": self.is_active_check.isChecked(),
            "note": self.note_input.toPlainText().strip(),
        }
        
        try:
            if self.current_alias_id:
                self.data_pool.update_employee_alias(self.current_alias_id, data)
                msg = f"已更新员工映射：{data['real_name']}"
                self.logger.info("Employee alias updated: id=%s, name=%s", self.current_alias_id, data['real_name'])
            else:
                new_id = self.data_pool.create_employee_alias(data)
                self.current_alias_id = new_id
                msg = f"已新增员工映射：{data['real_name']}"
                self.logger.info("Employee alias created: id=%s, name=%s", new_id, data['real_name'])
            
            QMessageBox.information(self, "成功", msg)
            self.refresh_page()
            self.updated.emit()
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", str(e))
        except Exception as e:
            self.logger.exception("Failed to save alias")
            QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")

    def toggle_alias_status(self) -> None:
        if not self.current_alias_id:
            QMessageBox.warning(self, "提示", "请先选择一个员工映射")
            return
            
        new_status = not self.is_active_check.isChecked()
        self.data_pool.set_employee_alias_active(self.current_alias_id, new_status)
        self.is_active_check.setChecked(new_status)
        self.refresh_page()
        self.logger.info("Employee alias status toggled: id=%s, active=%s", self.current_alias_id, new_status)
        self.updated.emit()

from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import PROJECT_OPTIONS
from app.corrections import CorrectionsLogService
from app.database import SQLiteDataPool


SYSTEM_CATEGORY_OPTIONS = ["全部", "火灾报警", "视频监控", "其他装置及设备"]
WORK_TYPE_OPTIONS = ["全部", "安全交底 / 会议类", "培训", "巡检", "测试", "维修或维护", "其他"]
STATUS_OPTIONS = ["完成", "未完成", "待确认"]
CONFIRM_STATUS_OPTIONS = ["all", "pending", "confirmed", "ignored"]


class ConfirmPage(QFrame):
    updated = Signal()

    def __init__(
        self,
        data_pool: SQLiteDataPool,
        corrections_service: CorrectionsLogService,
        default_operator_name: str,
    ) -> None:
        super().__init__()
        self.data_pool = data_pool
        self.corrections_service = corrections_service
        self.default_operator_name = default_operator_name
        self.current_record_id: int | None = None
        self.current_record_snapshot: dict[str, Any] | None = None
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title_label = QLabel("人工确认")
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel(
            "对 parsed_records 进行人工修正、确认和忽略处理。确认后的记录将成为后续日报、统计和导出的可信来源。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_filters())
        layout.addWidget(self._build_table(), 1)
        layout.addWidget(self._build_editor())

        self.refresh_page()

    def _build_filters(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.confirm_status_filter = QComboBox()
        self.confirm_status_filter.setObjectName("InputBox")
        self.confirm_status_filter.addItems(["全部", "pending", "confirmed", "ignored"])

        self.project_filter = QComboBox()
        self.project_filter.setObjectName("InputBox")
        self.project_filter.addItems(["全部", *PROJECT_OPTIONS])

        self.system_filter = QComboBox()
        self.system_filter.setObjectName("InputBox")
        self.system_filter.addItems(SYSTEM_CATEGORY_OPTIONS)

        self.work_type_filter = QComboBox()
        self.work_type_filter.setObjectName("InputBox")
        self.work_type_filter.addItems(WORK_TYPE_OPTIONS)

        self.keyword_input = QLineEdit()
        self.keyword_input.setObjectName("InputBox")
        self.keyword_input.setPlaceholderText("关键词搜索")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        layout.addWidget(QLabel("确认状态"), 0, 0)
        layout.addWidget(self.confirm_status_filter, 0, 1)
        layout.addWidget(QLabel("项目/服务对象"), 0, 2)
        layout.addWidget(self.project_filter, 0, 3)
        layout.addWidget(QLabel("系统类别"), 1, 0)
        layout.addWidget(self.system_filter, 1, 1)
        layout.addWidget(QLabel("工作类型"), 1, 2)
        layout.addWidget(self.work_type_filter, 1, 3)
        layout.addWidget(QLabel("关键词"), 2, 0)
        layout.addWidget(self.keyword_input, 2, 1, 1, 2)
        layout.addWidget(refresh_button, 2, 3)
        return layout

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 17)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "日期",
                "项目",
                "系统类别",
                "工作类型",
                "状态",
                "时间段",
                "用时H",
                "微信网名",
                "维修人员",
                "是否需人员确认",
                "地点",
                "问题/工作描述",
                "处理方法",
                "结果",
                "确认状态",
                "原始文本摘要",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.load_selected_record)
        return self.table

    def _build_editor(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("PlaceholderCard")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        editor_title = QLabel("记录详情编辑")
        editor_title.setObjectName("PlaceholderTitle")
        layout.addWidget(editor_title)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(8)

        self.work_date_input = QLineEdit()
        self.work_date_input.setObjectName("InputBox")
        self.project_input = QComboBox()
        self.project_input.setObjectName("InputBox")
        self.project_input.addItems(PROJECT_OPTIONS)
        self.system_category_input = QComboBox()
        self.system_category_input.setObjectName("InputBox")
        self.system_category_input.addItems(SYSTEM_CATEGORY_OPTIONS[1:])
        self.work_type_input = QComboBox()
        self.work_type_input.setObjectName("InputBox")
        self.work_type_input.addItems(WORK_TYPE_OPTIONS[1:])
        self.status_input = QComboBox()
        self.status_input.setObjectName("InputBox")
        self.status_input.addItems(STATUS_OPTIONS)
        self.start_time_input = QLineEdit()
        self.start_time_input.setObjectName("InputBox")
        self.end_time_input = QLineEdit()
        self.end_time_input.setObjectName("InputBox")
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 999.0)
        self.duration_input.setDecimals(2)
        self.wechat_nickname_input = QLineEdit()
        self.wechat_nickname_input.setObjectName("InputBox")
        self.worker_names_input = QLineEdit()
        self.worker_names_input.setObjectName("InputBox")
        self.location_input = QLineEdit()
        self.location_input.setObjectName("InputBox")
        self.device_or_part_input = QLineEdit()
        self.device_or_part_input.setObjectName("InputBox")
        self.problem_description_input = QPlainTextEdit()
        self.problem_description_input.setObjectName("InputArea")
        self.solution_input = QPlainTextEdit()
        self.solution_input.setObjectName("InputArea")
        self.result_input = QPlainTextEdit()
        self.result_input.setObjectName("InputArea")
        self.note_input = QPlainTextEdit()
        self.note_input.setObjectName("InputArea")
        self.source_raw_text_input = QPlainTextEdit()
        self.source_raw_text_input.setObjectName("InputArea")
        self.source_raw_text_input.setReadOnly(True)

        form_layout.addRow("日期", self.work_date_input)
        form_layout.addRow("项目", self.project_input)
        form_layout.addRow("系统类别", self.system_category_input)
        form_layout.addRow("工作类型", self.work_type_input)
        form_layout.addRow("状态", self.status_input)
        form_layout.addRow("开始时间", self.start_time_input)
        form_layout.addRow("结束时间", self.end_time_input)
        form_layout.addRow("用时H", self.duration_input)
        form_layout.addRow("微信网名", self.wechat_nickname_input)
        form_layout.addRow("维修人员", self.worker_names_input)
        form_layout.addRow("地点", self.location_input)
        form_layout.addRow("设备/部位", self.device_or_part_input)
        form_layout.addRow("问题/工作描述", self.problem_description_input)
        form_layout.addRow("处理方法", self.solution_input)
        form_layout.addRow("结果", self.result_input)
        form_layout.addRow("备注", self.note_input)
        form_layout.addRow("原始文本", self.source_raw_text_input)

        layout.addWidget(form_widget)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("保存修改")
        self.confirm_button = QPushButton("确认为有效记录")
        self.ignore_button = QPushButton("忽略该记录")
        self.restore_button = QPushButton("恢复为待确认")
        self.refresh_button = QPushButton("刷新列表")

        for button, object_name in (
            (self.save_button, "PrimaryButton"),
            (self.confirm_button, "PrimaryButton"),
            (self.ignore_button, "SecondaryButton"),
            (self.restore_button, "SecondaryButton"),
            (self.refresh_button, "SecondaryButton"),
        ):
            button.setObjectName(object_name)
            button_row.addWidget(button)

        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)
        layout.addWidget(self.feedback_label)

        self.save_button.clicked.connect(self.save_changes)
        self.confirm_button.clicked.connect(self.confirm_record)
        self.ignore_button.clicked.connect(self.ignore_record)
        self.restore_button.clicked.connect(self.restore_pending)
        self.refresh_button.clicked.connect(self.refresh_page)
        return wrapper

    def current_filters(self) -> dict[str, Any]:
        confirm_status = self.confirm_status_filter.currentText()
        return {
            "confirm_status": "all" if confirm_status == "全部" else confirm_status,
            "project": self.project_filter.currentText(),
            "system_category": self.system_filter.currentText(),
            "work_type": self.work_type_filter.currentText(),
            "keyword": self.keyword_input.text(),
        }

    def refresh_page(self) -> None:
        selected_record_id = self.current_record_id
        rows = self.data_pool.list_parsed_records(self.current_filters())
        self.table.setRowCount(len(rows))
        selected_row_index: int | None = None
        for row_index, row in enumerate(rows):
            time_range = self._format_time_range(str(row.get("start_time", "")), str(row.get("end_time", "")))
            summary = str(row.get("source_raw_text", "")).replace("\n", " ")[:80]
            values = [
                str(row.get("id", "")),
                str(row.get("work_date", "")),
                str(row.get("project", "")),
                str(row.get("system_category", "")),
                str(row.get("work_type", "")),
                str(row.get("status", "")),
                time_range,
                str(row.get("duration_hours", "")),
                str(row.get("wechat_nickname", "")),
                str(row.get("worker_names", "")),
                "是" if bool(row.get("employee_confirm_required", 0)) else "否",
                str(row.get("location", "")),
                str(row.get("problem_description", ""))[:40],
                str(row.get("solution", ""))[:40],
                str(row.get("result", ""))[:40],
                str(row.get("confirm_status", "")),
                summary,
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
            if selected_record_id is not None and int(row.get("id", 0)) == selected_record_id:
                selected_row_index = row_index

        self.table.resizeColumnsToContents()
        if selected_row_index is not None:
            self.table.selectRow(selected_row_index)
            return

        self.table.clearSelection()
        self._clear_editor()

    def load_selected_record(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            self._clear_editor()
            return
        record_id = int(selected_items[0].text())
        record = self.data_pool.get_parsed_record(record_id)
        if record is None:
            self._clear_editor()
            return

        self.current_record_id = record_id
        self.current_record_snapshot = record
        self.work_date_input.setText(str(record.get("work_date", "")))
        self.project_input.setCurrentText(str(record.get("project", "")) or "其他")
        self.system_category_input.setCurrentText(str(record.get("system_category", "")) or "其他装置及设备")
        self.work_type_input.setCurrentText(str(record.get("work_type", "")) or "其他")
        self.status_input.setCurrentText(str(record.get("status", "")) or "待确认")
        self.start_time_input.setText(str(record.get("start_time", "")))
        self.end_time_input.setText(str(record.get("end_time", "")))
        self.duration_input.setValue(float(record.get("duration_hours", 0.0) or 0.0))
        self.wechat_nickname_input.setText(str(record.get("wechat_nickname", "")))
        self.worker_names_input.setText(str(record.get("worker_names", "")))
        self.location_input.setText(str(record.get("location", "")))
        self.device_or_part_input.setText(str(record.get("device_or_part", "")))
        self.problem_description_input.setPlainText(str(record.get("problem_description", "")))
        self.solution_input.setPlainText(str(record.get("solution", "")))
        self.result_input.setPlainText(str(record.get("result", "")))
        self.note_input.setPlainText(str(record.get("note", "")))
        self.source_raw_text_input.setPlainText(str(record.get("source_raw_text", "")))
        self.feedback_label.setText(f"已加载记录 ID: {record_id}")

    def _collect_updates(self) -> dict[str, Any]:
        worker_names = self.worker_names_input.text().strip()
        return {
            "work_date": self.work_date_input.text().strip(),
            "project": self.project_input.currentText().strip(),
            "system_category": self.system_category_input.currentText().strip(),
            "work_type": self.work_type_input.currentText().strip(),
            "status": self.status_input.currentText().strip(),
            "start_time": self.start_time_input.text().strip(),
            "end_time": self.end_time_input.text().strip(),
            "duration_hours": round(float(self.duration_input.value()), 2),
            "wechat_nickname": self.wechat_nickname_input.text().strip(),
            "worker_names": worker_names,
            "employee_confirm_required": 0 if worker_names else 1,
            "location": self.location_input.text().strip(),
            "device_or_part": self.device_or_part_input.text().strip(),
            "problem_description": self.problem_description_input.toPlainText().strip(),
            "solution": self.solution_input.toPlainText().strip(),
            "result": self.result_input.toPlainText().strip(),
            "note": self.note_input.toPlainText().strip(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def save_changes(self) -> None:
        self._apply_action("update", None)

    def confirm_record(self) -> None:
        self._apply_action("confirm", "confirmed")

    def ignore_record(self) -> None:
        self._apply_action("ignore", "ignored")

    def restore_pending(self) -> None:
        self._apply_action("restore_pending", "pending")

    def _apply_action(self, action_type: str, confirm_status: str | None) -> None:
        if self.current_record_id is None:
            self.feedback_label.setText("请先选择一条记录。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        before = self.data_pool.get_parsed_record_snapshot(self.current_record_id)
        if before is None:
            self.feedback_label.setText("记录不存在，可能已被删除。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        updates = self._collect_updates()
        if confirm_status is not None:
            updates["confirm_status"] = confirm_status
        self.data_pool.update_parsed_record(self.current_record_id, updates)

        after = self.data_pool.get_parsed_record_snapshot(self.current_record_id) or {}
        self.corrections_service.append(
            operator_name=self.default_operator_name,
            action_type=action_type,
            record_id=self.current_record_id,
            raw_input_id=int(after.get("raw_input_id", 0)),
            before=before,
            after=after,
            source_raw_text=str(after.get("source_raw_text", "")),
            note=str(after.get("note", "")),
        )

        self.feedback_label.setText(f"操作成功：{action_type}，记录 ID {self.current_record_id}")
        self.feedback_label.setStyleSheet("color: #86EFAC;")
        self.refresh_page()
        self.updated.emit()

    def _format_time_range(self, start_time: str, end_time: str) -> str:
        if start_time and end_time:
            return f"{start_time}-{end_time}"
        return ""

    def _clear_editor(self) -> None:
        self.current_record_id = None
        self.current_record_snapshot = None
        self.work_date_input.clear()
        self.project_input.setCurrentText("其他")
        self.system_category_input.setCurrentText("其他装置及设备")
        self.work_type_input.setCurrentText("其他")
        self.status_input.setCurrentText("待确认")
        self.start_time_input.clear()
        self.end_time_input.clear()
        self.duration_input.setValue(0.0)
        self.wechat_nickname_input.clear()
        self.worker_names_input.clear()
        self.location_input.clear()
        self.device_or_part_input.clear()
        self.problem_description_input.clear()
        self.solution_input.clear()
        self.result_input.clear()
        self.note_input.clear()
        self.source_raw_text_input.clear()
        self.feedback_label.setText("请选择一条记录进行人工确认。")
        self.feedback_label.setStyleSheet("")

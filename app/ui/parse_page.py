from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database import SQLiteDataPool
from app.parser_engine import ParserEngine


class ParsePage(QFrame):
    parsed = Signal()

    def __init__(self, data_pool: SQLiteDataPool, parser_engine: ParserEngine) -> None:
        super().__init__()
        self.data_pool = data_pool
        self.parser_engine = parser_engine
        self.logger = logging.getLogger("ybkj_workflow.ui.parse_page")
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title_label = QLabel("智能解析")
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel(
            "从 raw_inputs 中读取待解析文本，执行 V0.1 规则解析，并生成 parsed_records 供后续人工确认。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_toolbar())
        layout.addWidget(self._build_table(), 1)

        self.refresh_page()

    def _build_toolbar(self) -> QVBoxLayout:
        wrapper = QVBoxLayout()
        wrapper.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.pending_count_label = QLabel("待解析数量：0")
        self.pending_count_label.setObjectName("MetaText")

        parse_button = QPushButton("解析待处理文本")
        parse_button.setObjectName("PrimaryButton")
        parse_button.clicked.connect(self.parse_pending)

        refresh_button = QPushButton("刷新列表")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        top_row.addWidget(self.pending_count_label)
        top_row.addStretch(1)
        top_row.addWidget(parse_button)
        top_row.addWidget(refresh_button)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)

        wrapper.addLayout(top_row)
        wrapper.addWidget(self.feedback_label)
        return wrapper

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            [
                "日期",
                "项目",
                "系统类别",
                "工作类型",
                "状态",
                "时间段",
                "人员",
                "待确认",
                "解析提示",
                "原始文本摘要",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return self.table

    def refresh_page(self) -> None:
        self.pending_count_label.setText(
            f"待解析数量：{self.data_pool.count_pending_raw_inputs()}"
        )
        rows = self.data_pool.get_recent_parsed_records(limit=100)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            time_range = self._format_time_range(
                str(row.get("start_time", "")),
                str(row.get("end_time", "")),
            )
            summary = str(row.get("source_raw_text", "")).replace("\n", " ")[:80]
            values = [
                str(row.get("work_date", "")),
                str(row.get("project", "")),
                str(row.get("system_category", "")),
                str(row.get("work_type", "")),
                str(row.get("status", "")),
                time_range,
                str(row.get("worker_names", "")),
                "是" if bool(row.get("employee_confirm_required", 0)) else "否",
                str(row.get("note", ""))[:120],
                summary,
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def parse_pending(self) -> None:
        try:
            summary = self.parser_engine.process_pending_records()
        except Exception as exc:
            self.logger.exception("Parse pending failed: %s", exc)
            self.feedback_label.setText("解析执行失败，请查看日志。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        self.feedback_label.setText(
            "解析完成：已处理 {raw_inputs_parsed} 条原始输入，生成 {parsed_records_generated} 条解析记录，"
            "其中 {pending_confirm_records} 条待人工确认，{parse_warning_records} 条带解析提示。".format(**summary)
        )
        self.feedback_label.setStyleSheet("color: #86EFAC;")
        self.refresh_page()
        self.parsed.emit()

    def _format_time_range(self, start_time: str, end_time: str) -> str:
        if start_time and end_time:
            return f"{start_time}-{end_time}"
        return ""

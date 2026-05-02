from __future__ import annotations

import logging
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
)

from app.analytics_service import AnalyticsService
from app.config import PROJECT_OPTIONS


SYSTEM_CATEGORY_OPTIONS = ["全部", "火灾报警", "视频监控", "其他装置及设备"]
WORK_TYPE_OPTIONS = [
    "全部",
    "维修",
    "维护",
    "巡检",
    "测试",
    "会议",
    "安全交底",
    "培训",
    "施工配合",
    "其他",
]


class SummaryCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("DashboardCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")

        self.value_label = QLabel("0")
        self.value_label.setObjectName("CardValue")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class AnalyticsPage(QFrame):
    def __init__(self, analytics_service: AnalyticsService) -> None:
        super().__init__()
        self.analytics_service = analytics_service
        self.logger = logging.getLogger("ybkj_workflow.ui.analytics")
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title_label = QLabel("统计分析")
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel(
            "基于已确认记录统计人员、项目、系统类别、工作类型和明细数据。"
            "当前 V0.1 先以卡片和表格分析为主。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_filters())
        layout.addLayout(self._build_summary_cards())
        layout.addWidget(self._build_tabs(), 1)

        self.feedback_label = QLabel("请点击“刷新统计”加载 confirmed 统计结果。")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)
        layout.addWidget(self.feedback_label)

        footer_note = QLabel(
            "后续版本可在此基础上增加柱状图、饼图和趋势图，当前 V0.1 先以表格统计为主。"
        )
        footer_note.setObjectName("MetaText")
        footer_note.setWordWrap(True)
        layout.addWidget(footer_note)

        self.refresh_page()

    def _build_filters(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.start_date_input = QLineEdit()
        self.start_date_input.setObjectName("InputBox")
        self.start_date_input.setPlaceholderText("YYYY-MM-DD，可为空")

        self.end_date_input = QLineEdit()
        self.end_date_input.setObjectName("InputBox")
        self.end_date_input.setPlaceholderText("YYYY-MM-DD，可为空")

        self.project_filter = QComboBox()
        self.project_filter.setObjectName("InputBox")
        self.project_filter.addItems(["全部", *PROJECT_OPTIONS])

        self.system_filter = QComboBox()
        self.system_filter.setObjectName("InputBox")
        self.system_filter.addItems(SYSTEM_CATEGORY_OPTIONS)

        self.work_type_filter = QComboBox()
        self.work_type_filter.setObjectName("InputBox")
        self.work_type_filter.addItems(WORK_TYPE_OPTIONS)

        self.worker_keyword_input = QLineEdit()
        self.worker_keyword_input.setObjectName("InputBox")
        self.worker_keyword_input.setPlaceholderText("人员关键词")

        refresh_button = QPushButton("刷新统计")
        refresh_button.setObjectName("PrimaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        clear_button = QPushButton("清空筛选")
        clear_button.setObjectName("SecondaryButton")
        clear_button.clicked.connect(self.clear_filters)

        layout.addWidget(QLabel("开始日期"), 0, 0)
        layout.addWidget(self.start_date_input, 0, 1)
        layout.addWidget(QLabel("结束日期"), 0, 2)
        layout.addWidget(self.end_date_input, 0, 3)
        layout.addWidget(QLabel("项目"), 1, 0)
        layout.addWidget(self.project_filter, 1, 1)
        layout.addWidget(QLabel("系统类别"), 1, 2)
        layout.addWidget(self.system_filter, 1, 3)
        layout.addWidget(QLabel("工作类型"), 2, 0)
        layout.addWidget(self.work_type_filter, 2, 1)
        layout.addWidget(QLabel("人员关键词"), 2, 2)
        layout.addWidget(self.worker_keyword_input, 2, 3)
        layout.addWidget(refresh_button, 3, 2)
        layout.addWidget(clear_button, 3, 3)
        return layout

    def _build_summary_cards(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        self.summary_cards = {
            "total_records": SummaryCard("已确认记录数"),
            "total_duration_hours": SummaryCard("总工时(H)"),
            "unique_workers": SummaryCard("参与人员数"),
            "fire_alarm_count": SummaryCard("火灾报警数量"),
            "video_count": SummaryCard("视频监控数量"),
            "other_count": SummaryCard("其他装置数量"),
            "missing_worker_count": SummaryCard("未填写人员"),
            "missing_duration_count": SummaryCard("未填写工时"),
        }

        for index, key in enumerate(self.summary_cards):
            row = index // 4
            column = index % 4
            layout.addWidget(self.summary_cards[key], row, column)
        return layout

    def _build_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()
        self.tabs.setObjectName("PlaceholderCard")

        self.worker_table = self._build_table(
            ["人员", "记录数", "总工时(H)", "火灾报警", "视频监控", "其他装置及设备", "工时待补全"]
        )
        self.project_table = self._build_table(["项目/服务对象", "记录数", "总工时(H)"])
        self.system_table = self._build_table(["系统类别", "记录数", "总工时(H)"])
        self.work_type_table = self._build_table(["工作类型", "记录数", "总工时(H)"])
        self.detail_table = self._build_table(
            ["日期", "项目", "系统类别", "工作类型", "时间段", "用时(H)", "人员", "地点", "描述摘要", "结果"]
        )

        self.tabs.addTab(self.worker_table, "按人员统计")
        self.tabs.addTab(self.project_table, "按项目统计")
        self.tabs.addTab(self.system_table, "按系统类别统计")
        self.tabs.addTab(self.work_type_table, "按工作类型统计")
        self.tabs.addTab(self.detail_table, "明细记录")
        return self.tabs

    def _build_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setObjectName("InputArea")
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def current_filters(self) -> dict[str, str]:
        return {
            "start_date": self.start_date_input.text().strip(),
            "end_date": self.end_date_input.text().strip(),
            "project": self.project_filter.currentText().strip(),
            "system_category": self.system_filter.currentText().strip(),
            "work_type": self.work_type_filter.currentText().strip(),
            "worker_names": self.worker_keyword_input.text().strip(),
        }

    def clear_filters(self) -> None:
        self.start_date_input.clear()
        self.end_date_input.clear()
        self.project_filter.setCurrentText("全部")
        self.system_filter.setCurrentText("全部")
        self.work_type_filter.setCurrentText("全部")
        self.worker_keyword_input.clear()
        self.refresh_page()

    def refresh_page(self) -> None:
        filters = self.current_filters()
        try:
            overview = self.analytics_service.get_overview(filters)
            by_worker = self.analytics_service.get_by_worker(filters)
            by_project = self.analytics_service.get_by_project(filters)
            by_system = self.analytics_service.get_by_system_category(filters)
            by_work_type = self.analytics_service.get_by_work_type(filters)
            detail_records = self.analytics_service.get_detail_records(filters)

            self._update_summary_cards(overview)
            self._populate_table(
                self.worker_table,
                [
                    [
                        row["worker_name"],
                        row["record_count"],
                        row["total_duration_hours"],
                        row["fire_alarm_count"],
                        row["video_count"],
                        row["other_count"],
                        row["missing_duration_count"],
                    ]
                    for row in by_worker
                ],
            )
            self._populate_table(
                self.project_table,
                [[row["project"], row["record_count"], row["total_duration_hours"]] for row in by_project],
            )
            self._populate_table(
                self.system_table,
                [
                    [row["system_category"], row["record_count"], row["total_duration_hours"]]
                    for row in by_system
                ],
            )
            self._populate_table(
                self.work_type_table,
                [[row["work_type"], row["record_count"], row["total_duration_hours"]] for row in by_work_type],
            )
            self._populate_table(
                self.detail_table,
                [
                    [
                        str(record.get("work_date", "")),
                        str(record.get("project", "") or "其他"),
                        str(record.get("system_category", "") or "其他装置及设备"),
                        str(record.get("work_type", "") or "其他"),
                        self._format_time_range(
                            str(record.get("start_time", "")),
                            str(record.get("end_time", "")),
                        ),
                        self._format_duration(record.get("duration_hours", 0)),
                        str(record.get("worker_names", "")).strip() or "人员待确认",
                        str(record.get("location", "")).strip(),
                        self._build_summary_text(record),
                        str(record.get("result", "") or record.get("status", "")),
                    ]
                    for record in detail_records
                ],
            )

            self.logger.info(
                "Analytics refreshed: filters=%s confirmed_records=%s",
                filters,
                overview["total_records"],
            )

            if overview["total_records"] == 0:
                self.feedback_label.setText(
                    "当前筛选条件下没有已确认记录，请先完成解析和人工确认。"
                )
                self.feedback_label.setStyleSheet("color: #FCD34D;")
            else:
                self.feedback_label.setText(
                    f"统计已刷新，共载入 {overview['total_records']} 条已确认记录。"
                )
                self.feedback_label.setStyleSheet("color: #86EFAC;")
        except Exception:
            self.logger.exception("Failed to refresh analytics: filters=%s", filters)
            self.feedback_label.setText("统计刷新失败，请检查日志后重试。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")

    def _update_summary_cards(self, overview: dict[str, Any]) -> None:
        for key, card in self.summary_cards.items():
            value = overview.get(key, 0)
            if key == "total_duration_hours":
                card.set_value(f"{float(value or 0):.2f}")
            else:
                card.set_value(str(value))

    def _populate_table(self, table: QTableWidget, rows: list[list[Any]]) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()

    def _format_time_range(self, start_time: str, end_time: str) -> str:
        if start_time and end_time:
            return f"{start_time}-{end_time}"
        if start_time:
            return start_time
        if end_time:
            return end_time
        return ""

    def _format_duration(self, duration_value: Any) -> str:
        try:
            return f"{float(duration_value or 0):.2f}"
        except (TypeError, ValueError):
            return "0.00"

    def _build_summary_text(self, record: dict[str, Any]) -> str:
        for field_name in (
            "problem_description",
            "solution",
            "device_or_part",
            "note",
            "source_raw_text",
        ):
            value = str(record.get(field_name, "")).strip()
            if value:
                return value.replace("\n", " ")[:80]
        return ""

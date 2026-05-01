from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import PROJECT_OPTIONS
from app.database import SQLiteDataPool
from app.report_service import DailyReportService


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


class ReportPage(QFrame):
    def __init__(
        self,
        data_pool: SQLiteDataPool,
        report_service: DailyReportService,
    ) -> None:
        super().__init__()
        self.data_pool = data_pool
        self.report_service = report_service
        self.last_report_text = ""
        self.last_summary: dict[str, Any] = {}
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title_label = QLabel("日报生成")
        title_label.setObjectName("PlaceholderTitle")
        desc_label = QLabel(
            "基于已确认记录生成可复制到企业微信/微信的日报文本，并支持导出 TXT / Markdown 文件。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_filters())
        layout.addLayout(self._build_summary_cards())
        layout.addWidget(self._build_preview(), 1)

        footer_note = QLabel(
            "企业微信自动同步接口已预留，当前版本请使用复制文本方式发送。企业微信同步默认关闭，不主动联网。"
        )
        footer_note.setObjectName("MetaText")
        footer_note.setWordWrap(True)
        layout.addWidget(footer_note)

        self.refresh_page()

    def _build_filters(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.date_input = QComboBox()
        self.date_input.setObjectName("InputBox")
        self.date_input.setEditable(True)
        self.project_filter = QComboBox()
        self.project_filter.setObjectName("InputBox")
        self.system_filter = QComboBox()
        self.system_filter.setObjectName("InputBox")
        self.work_type_filter = QComboBox()
        self.work_type_filter.setObjectName("InputBox")
        self.worker_keyword_input = QLineEdit()
        self.worker_keyword_input.setObjectName("InputBox")
        self.worker_keyword_input.setPlaceholderText("人员关键词")

        self.generate_button = QPushButton("生成日报")
        self.generate_button.setObjectName("PrimaryButton")
        self.copy_button = QPushButton("复制到剪贴板")
        self.copy_button.setObjectName("SecondaryButton")
        self.export_txt_button = QPushButton("导出 TXT")
        self.export_txt_button.setObjectName("SecondaryButton")
        self.export_md_button = QPushButton("导出 Markdown")
        self.export_md_button.setObjectName("SecondaryButton")
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("SecondaryButton")

        self.generate_button.clicked.connect(self.generate_report)
        self.copy_button.clicked.connect(self.copy_report)
        self.export_txt_button.clicked.connect(lambda: self.export_report("txt"))
        self.export_md_button.clicked.connect(lambda: self.export_report("md"))
        self.refresh_button.clicked.connect(self.refresh_page)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.generate_button)
        action_row.addWidget(self.copy_button)
        action_row.addWidget(self.export_txt_button)
        action_row.addWidget(self.export_md_button)
        action_row.addWidget(self.refresh_button)
        action_row.addStretch(1)

        layout.addWidget(QLabel("日期"), 0, 0)
        layout.addWidget(self.date_input, 0, 1)
        layout.addWidget(QLabel("项目"), 0, 2)
        layout.addWidget(self.project_filter, 0, 3)
        layout.addWidget(QLabel("系统类别"), 1, 0)
        layout.addWidget(self.system_filter, 1, 1)
        layout.addWidget(QLabel("工作类型"), 1, 2)
        layout.addWidget(self.work_type_filter, 1, 3)
        layout.addWidget(QLabel("人员关键词"), 2, 0)
        layout.addWidget(self.worker_keyword_input, 2, 1, 1, 3)
        layout.addLayout(action_row, 3, 0, 1, 4)
        return layout

    def _build_summary_cards(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        self.summary_cards = {
            "record_count": SummaryCard("已确认记录数"),
            "fire_count": SummaryCard("火灾报警数量"),
            "video_count": SummaryCard("视频监控数量"),
            "other_count": SummaryCard("其他装置数量"),
            "total_hours": SummaryCard("总工时"),
            "worker_count": SummaryCard("参与人员数量"),
        }

        for index, key in enumerate(self.summary_cards):
            row = index // 3
            column = index % 3
            layout.addWidget(self.summary_cards[key], row, column)
        return layout

    def _build_preview(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("PlaceholderCard")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        preview_title = QLabel("日报文本预览")
        preview_title.setObjectName("PlaceholderTitle")
        self.preview_input = QPlainTextEdit()
        self.preview_input.setObjectName("InputArea")
        self.preview_input.setReadOnly(True)
        self.preview_input.setPlainText("请设置筛选条件后生成日报。")

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)

        layout.addWidget(preview_title)
        layout.addWidget(self.preview_input, 1)
        layout.addWidget(self.feedback_label)
        return wrapper

    def refresh_page(self) -> None:
        current_date = self.date_input.currentText().strip() if self.date_input.count() else ""
        current_project = self.project_filter.currentText().strip() if self.project_filter.count() else "全部"
        current_system = self.system_filter.currentText().strip() if self.system_filter.count() else "全部"
        current_work_type = self.work_type_filter.currentText().strip() if self.work_type_filter.count() else "全部"

        report_filters = self.data_pool.get_report_filter_options()
        available_dates = self.data_pool.get_available_work_dates()
        today_text = datetime.now().strftime("%Y-%m-%d")

        self._reset_combo(self.date_input, [today_text, *available_dates], current_date or today_text)
        self._reset_combo(
            self.project_filter,
            ["全部", *PROJECT_OPTIONS, *report_filters["projects"]],
            current_project or "全部",
        )
        self._reset_combo(
            self.system_filter,
            ["全部", *SYSTEM_CATEGORY_OPTIONS[1:], *report_filters["system_categories"]],
            current_system or "全部",
        )
        self._reset_combo(
            self.work_type_filter,
            ["全部", *WORK_TYPE_OPTIONS[1:], *report_filters["work_types"]],
            current_work_type or "全部",
        )
        self.feedback_label.setText("日报筛选项已刷新。")
        self.feedback_label.setStyleSheet("")

    def generate_report(self) -> None:
        work_date = self.date_input.currentText().strip() or datetime.now().strftime("%Y-%m-%d")
        filters = {
            "project": self.project_filter.currentText().strip(),
            "system_category": self.system_filter.currentText().strip(),
            "work_type": self.work_type_filter.currentText().strip(),
            "worker_names": self.worker_keyword_input.text().strip(),
        }
        report_text, summary = self.report_service.build_daily_report(work_date, filters)
        self.last_summary = summary

        if summary["record_count"] == 0:
            self.last_report_text = ""
            self.preview_input.setPlainText(
                "当前筛选条件下没有已确认记录，请先到人工确认页确认记录。"
            )
            self._update_summary_cards(summary)
            self.feedback_label.setText("当前没有可生成日报的 confirmed 记录。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        self.last_report_text = report_text
        self.preview_input.setPlainText(report_text)
        self._update_summary_cards(summary)
        self.feedback_label.setText("日报已生成，可直接复制到企业微信或导出为文本文件。")
        self.feedback_label.setStyleSheet("color: #86EFAC;")

    def copy_report(self) -> None:
        if not self.last_report_text:
            self.feedback_label.setText("请先生成日报文本。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(self.last_report_text)
        self.feedback_label.setText("日报文本已复制到剪贴板。")
        self.feedback_label.setStyleSheet("color: #86EFAC;")

    def export_report(self, suffix: str) -> None:
        if not self.last_report_text:
            self.feedback_label.setText("请先生成日报文本后再导出。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        target_path = self.report_service.export_daily_report_text(
            self.last_report_text,
            self.date_input.currentText().strip(),
            suffix=suffix,
            record_count=int(self.last_summary.get("record_count", 0)),
        )
        self.feedback_label.setText(f"导出成功：{target_path.as_posix()}")
        self.feedback_label.setStyleSheet("color: #86EFAC;")

    def _update_summary_cards(self, summary: dict[str, Any]) -> None:
        self.summary_cards["record_count"].set_value(str(summary.get("record_count", 0)))
        system_counts = summary.get("system_category_counts", {})
        self.summary_cards["fire_count"].set_value(str(system_counts.get("火灾报警", 0)))
        self.summary_cards["video_count"].set_value(str(system_counts.get("视频监控", 0)))
        self.summary_cards["other_count"].set_value(str(system_counts.get("其他装置及设备", 0)))
        self.summary_cards["total_hours"].set_value(str(summary.get("total_duration_hours", 0)))
        self.summary_cards["worker_count"].set_value(str(summary.get("worker_count", 0)))

    def _reset_combo(self, combo: QComboBox, items: list[str], current_value: str) -> None:
        unique_items: list[str] = []
        for item in items:
            normalized_item = str(item).strip()
            if normalized_item and normalized_item not in unique_items:
                unique_items.append(normalized_item)

        combo.blockSignals(True)
        combo.clear()
        combo.addItems(unique_items)
        combo.setCurrentText(current_value if current_value in unique_items else unique_items[0])
        combo.blockSignals(False)

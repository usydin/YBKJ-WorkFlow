from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import to_relative_source_path
from app.quality_service import QualityCheckService


class MetricCard(QFrame):
    def __init__(self, title: str, metric_labels: dict[str, str]) -> None:
        super().__init__()
        self.metric_labels = metric_labels
        self.value_labels: dict[str, QLabel] = {}
        self.setObjectName("DashboardCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("PlaceholderTitle")
        layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        for row_index, (key, label_text) in enumerate(metric_labels.items()):
            label = QLabel(label_text)
            label.setObjectName("MetaText")
            value_label = QLabel("0")
            value_label.setObjectName("FieldLabel")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(label, row_index, 0)
            grid.addWidget(value_label, row_index, 1)
            self.value_labels[key] = value_label

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        layout.addLayout(grid)
        layout.addStretch(1)

    def update_values(self, values: dict[str, Any]) -> None:
        for key, label in self.value_labels.items():
            label.setText(str(values.get(key, 0)))


class ConclusionCard(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("DashboardCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel("综合结论")
        title_label.setObjectName("PlaceholderTitle")

        self.level_label = QLabel("未检查")
        self.level_label.setObjectName("CardValue")

        self.summary_label = QLabel("请点击“开始检查”或“刷新”获取最新数据质量状态。")
        self.summary_label.setObjectName("PlaceholderDescription")
        self.summary_label.setWordWrap(True)

        self.score_label = QLabel("风险分值：0")
        self.score_label.setObjectName("MetaText")

        self.action_label = QLabel("建议动作：等待检查结果。")
        self.action_label.setObjectName("MetaText")
        self.action_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(self.level_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.score_label)
        layout.addWidget(self.action_label)
        layout.addStretch(1)

    def update_values(self, conclusion: dict[str, Any]) -> None:
        level = str(conclusion.get("level", "未检查"))
        level_color = {
            "正常": "#86EFAC",
            "需要关注": "#FCD34D",
            "需要处理": "#FCA5A5",
        }.get(level, "")
        self.level_label.setText(level)
        self.level_label.setStyleSheet(f"color: {level_color};" if level_color else "")
        self.summary_label.setText(str(conclusion.get("summary", "")))
        self.score_label.setText(f"风险分值：{conclusion.get('score', 0)}")
        actions = conclusion.get("recommended_actions", [])
        primary_action = actions[0] if actions else "暂无建议动作。"
        self.action_label.setText(f"建议动作：{primary_action}")


class QualityPage(QFrame):
    def __init__(self, quality_service: QualityCheckService) -> None:
        super().__init__()
        self.quality_service = quality_service
        self.logger = logging.getLogger("ybkj_workflow.ui.quality")
        self.last_result: dict[str, Any] | None = None
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        layout.addLayout(self._build_header())
        layout.addLayout(self._build_cards())
        layout.addWidget(self._build_issue_table(), 1)
        layout.addLayout(self._build_footer())

        self.feedback_label = QLabel("页面已加载，正在执行首次数据质量检查。")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)
        layout.addWidget(self.feedback_label)

        self.run_check()

    def _build_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        text_box = QVBoxLayout()
        text_box.setSpacing(6)

        title_label = QLabel("数据质量检查")
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel(
            "对原始输入、解析记录、员工映射和导出准备情况进行只读检查，"
            "用于验证当前闭环是否可稳定演示与导出。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        text_box.addWidget(title_label)
        text_box.addWidget(desc_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.start_button = QPushButton("开始检查")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.clicked.connect(self.run_check)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.clicked.connect(self.run_check)

        self.export_button = QPushButton("导出检查结果")
        self.export_button.setObjectName("SecondaryButton")
        self.export_button.clicked.connect(self.export_result)

        button_row.addWidget(self.start_button)
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.export_button)

        layout.addLayout(text_box, 1)
        layout.addLayout(button_row)
        return layout

    def _build_cards(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        self.raw_input_card = MetricCard(
            "原始输入",
            {
                "total_count": "总数",
                "unparsed_count": "未解析",
                "parsed_count": "已解析",
                "empty_text_count": "空文本",
                "duplicate_text_count": "重复文本",
            },
        )
        self.parsed_record_card = MetricCard(
            "解析记录",
            {
                "total_count": "总数",
                "pending_count": "待确认",
                "confirmed_count": "已确认",
                "missing_worker_count": "缺少维修人员",
                "worker_confirm_required_count": "人员待确认",
            },
        )
        self.employee_card = MetricCard(
            "员工映射",
            {
                "employee_total_count": "员工总数",
                "alias_total_count": "别名总数",
                "unresolved_alias_count": "未解析别名",
                "conflict_count": "疑似冲突",
                "enabled_employee_count": "已启用员工",
            },
        )
        self.export_card = MetricCard(
            "导出准备",
            {
                "report_ready_count": "日报可导出",
                "excel_ready_count": "Excel可导出",
                "today_count": "今日记录",
                "week_count": "本周记录",
                "month_count": "本月记录",
            },
        )
        self.conclusion_card = ConclusionCard()

        layout.addWidget(self.raw_input_card, 0, 0)
        layout.addWidget(self.parsed_record_card, 0, 1)
        layout.addWidget(self.employee_card, 1, 0)
        layout.addWidget(self.export_card, 1, 1)
        layout.addWidget(self.conclusion_card, 0, 2, 2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        return layout

    def _build_issue_table(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel("问题清单")
        title_label.setObjectName("PlaceholderTitle")

        self.issue_table = QTableWidget(0, 5)
        self.issue_table.setHorizontalHeaderLabels(["等级", "类型", "问题说明", "数量", "建议动作"])
        self.issue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.issue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.issue_table.verticalHeader().setVisible(False)
        self.issue_table.horizontalHeader().setStretchLastSection(True)
        self.issue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.issue_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(title_label)
        layout.addWidget(self.issue_table, 1)
        return wrapper

    def _build_footer(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(16)

        self.checked_at_label = QLabel("检查时间：未执行")
        self.checked_at_label.setObjectName("MetaText")

        self.rule_version_label = QLabel("规则版本：V0.2-flow-check")
        self.rule_version_label.setObjectName("MetaText")

        self.data_source_label = QLabel("数据来源：SQLite")
        self.data_source_label.setObjectName("MetaText")
        self.data_source_label.setWordWrap(True)

        layout.addWidget(self.checked_at_label)
        layout.addWidget(self.rule_version_label)
        layout.addWidget(self.data_source_label, 1)
        return layout

    def run_check(self) -> None:
        try:
            result = self.quality_service.run_check()
        except Exception:
            self.logger.exception("Failed to run quality check")
            self.feedback_label.setText("数据质量检查失败，请查看日志后重试。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        self.last_result = result
        self.raw_input_card.update_values(result["raw_inputs"])
        self.parsed_record_card.update_values(result["parsed_records"])
        self.employee_card.update_values(result["employee_mapping"])
        self.export_card.update_values(result["export_readiness"])
        self.conclusion_card.update_values(result["conclusion"])
        self._populate_issue_table(result["issues"])

        self.checked_at_label.setText(f"检查时间：{result['checked_at']}")
        self.rule_version_label.setText(f"规则版本：{result['rule_version']}")
        self.data_source_label.setText(f"数据来源：{result['data_source']}")
        self.feedback_label.setText(
            f"检查完成：{result['conclusion']['level']}，共识别 {len(result['issues'])} 项提示/问题。"
        )
        self.feedback_label.setStyleSheet("")

    def refresh_page(self) -> None:
        self.run_check()

    def export_result(self) -> None:
        if self.last_result is None:
            self.run_check()
        if self.last_result is None:
            return

        try:
            target_path = self.quality_service.export_markdown(self.last_result)
        except Exception:
            self.logger.exception("Failed to export quality markdown")
            self.feedback_label.setText("检查结果导出失败，请查看日志后重试。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        relative_path = to_relative_source_path(target_path)
        self.feedback_label.setText(f"导出成功：{relative_path}")
        self.feedback_label.setStyleSheet("color: #86EFAC;")

    def _populate_issue_table(self, issues: list[dict[str, Any]]) -> None:
        rows = issues or [
            {
                "level": "提示",
                "type": "综合结论",
                "description": "当前未发现明显数据质量问题。",
                "count": 0,
                "action": "可继续进行日报与 Excel 导出。",
            }
        ]
        self.issue_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                str(row.get("level", "")),
                str(row.get("type", "")),
                str(row.get("description", "")),
                str(row.get("count", "")),
                str(row.get("action", "")),
            ]
            color = self._severity_color(values[0])
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if color is not None:
                    item.setForeground(color)
                if column_index == 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.issue_table.setItem(row_index, column_index, item)

        self.issue_table.resizeColumnsToContents()
        self.issue_table.setColumnWidth(2, 280)
        self.issue_table.setColumnWidth(4, 360)

    def _severity_color(self, level: str) -> QColor | None:
        if level == "严重":
            return QColor("#FCA5A5")
        if level == "关注":
            return QColor("#FCD34D")
        if level == "提示":
            return QColor("#93C5FD")
        return None

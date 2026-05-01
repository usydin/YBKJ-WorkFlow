from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.config import PROJECT_OPTIONS
from app.database import SQLiteDataPool
from app.excel_export_service import ExcelExportService


class ExcelExportPage(QFrame):
    exported = Signal(str)

    def __init__(
        self,
        data_pool: SQLiteDataPool,
        export_service: ExcelExportService,
    ) -> None:
        super().__init__()
        self.data_pool = data_pool
        self.export_service = export_service
        self.logger = logging.getLogger("ybkj_workflow.ui.excel_export")
        
        self.setObjectName("PlaceholderCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title_label = QLabel("Excel 导出")
        title_label.setObjectName("PlaceholderTitle")
        
        desc_label = QLabel(
            "基于已确认记录生成维保台账 Excel。导出的文件将按照系统类别分 Sheet 存储，并包含自动统计。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_filters())
        layout.addLayout(self._build_stats_cards())
        layout.addWidget(self._build_preview_table(), 1)
        layout.addLayout(self._build_actions())

        self.refresh_page()

    def _build_filters(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(datetime.now().date())
        self.date_input.setObjectName("InputBox")

        self.project_filter = QComboBox()
        self.project_filter.setObjectName("InputBox")
        self.project_filter.addItems(["全部", *PROJECT_OPTIONS])

        self.system_filter = QComboBox()
        self.system_filter.setObjectName("InputBox")
        self.system_filter.addItems(["全部", "火灾报警", "视频监控", "其他装置及设备"])

        self.work_type_filter = QComboBox()
        self.work_type_filter.setObjectName("InputBox")
        self.work_type_filter.addItems(["全部", "维修", "维护", "巡检", "测试", "会议", "安全交底", "培训", "施工配合", "其他"])

        self.worker_filter = QLineEdit()
        self.worker_filter.setPlaceholderText("人员关键词")
        self.worker_filter.setObjectName("InputBox")

        refresh_button = QPushButton("刷新统计")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        layout.addWidget(QLabel("日期"), 0, 0)
        layout.addWidget(self.date_input, 0, 1)
        layout.addWidget(QLabel("项目"), 0, 2)
        layout.addWidget(self.project_filter, 0, 3)
        layout.addWidget(QLabel("系统类别"), 1, 0)
        layout.addWidget(self.system_filter, 1, 1)
        layout.addWidget(QLabel("工作类型"), 1, 2)
        layout.addWidget(self.work_type_filter, 1, 3)
        layout.addWidget(QLabel("人员"), 2, 0)
        layout.addWidget(self.worker_filter, 2, 1, 1, 2)
        layout.addWidget(refresh_button, 2, 3)

        return layout

    def _build_stats_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.stats_cards = {}
        cards_info = [
            ("total_count", "可导出记录", "0"),
            ("fire_count", "火灾报警", "0"),
            ("video_count", "视频监控", "0"),
            ("other_count", "其他设备", "0"),
            ("total_hours", "总工时(H)", "0.0"),
            ("missing_person", "人员待确认", "0"),
        ]

        for key, label, val in cards_info:
            card = QFrame()
            card.setObjectName("DashboardCard")
            card_layout = QVBoxLayout(card)
            
            title = QLabel(label)
            title.setObjectName("CardTitle")
            value = QLabel(val)
            value.setObjectName("CardValue")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            card_layout.addWidget(title)
            card_layout.addWidget(value)
            
            self.stats_cards[key] = value
            layout.addWidget(card)

        return layout

    def _build_preview_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "日期", "项目", "系统类别", "工作类型", "状态", "时间段", "人员", "描述摘要"
        ])
        self.table.setObjectName("InputArea")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return self.table

    def _build_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        
        self.export_button = QPushButton("导出 Excel 台账")
        self.export_button.setObjectName("PrimaryButton")
        self.export_button.clicked.connect(self.run_export)
        
        layout.addStretch(1)
        layout.addWidget(self.export_button)
        return layout

    def get_current_filters(self) -> dict[str, Any]:
        return {
            "project": self.project_filter.currentText(),
            "system_category": self.system_filter.currentText(),
            "work_type": self.work_type_filter.currentText(),
            "worker_names": self.worker_filter.text().strip(),
        }

    def refresh_page(self) -> None:
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        filters = self.get_current_filters()
        
        records = self.data_pool.list_confirmed_records_for_report(date_str, filters)
        
        self._update_stats(records)
        self._update_table(records)

        if not records:
            self.export_button.setEnabled(False)
            self.export_button.setToolTip("当前没有可导出的已确认记录")
        else:
            self.export_button.setEnabled(True)
            self.export_button.setToolTip("")

    def _update_stats(self, records: list[dict[str, Any]]) -> None:
        stats = self.export_service._calculate_summary(records)
        self.stats_cards["total_count"].setText(str(stats["total_count"]))
        self.stats_cards["fire_count"].setText(str(stats["fire_count"]))
        self.stats_cards["video_count"].setText(str(stats["video_count"]))
        self.stats_cards["other_count"].setText(str(stats["other_count"]))
        self.stats_cards["total_hours"].setText(str(stats["total_hours"]))
        self.stats_cards["missing_person"].setText(str(stats["missing_person_count"]))

    def _update_table(self, records: list[dict[str, Any]]) -> None:
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            time_range = f"{r.get('start_time', '')}-{r.get('end_time', '')}" if r.get('start_time') else ""
            desc = r.get("problem_description", "") or r.get("source_raw_text", "")[:40]
            
            items = [
                r.get("work_date", ""),
                r.get("project", ""),
                r.get("system_category", ""),
                r.get("work_type", ""),
                r.get("status", ""),
                time_range,
                r.get("worker_names", ""),
                desc
            ]
            for j, val in enumerate(items):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        
        self.table.resizeColumnsToContents()

    def run_export(self) -> None:
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        filters = self.get_current_filters()
        
        try:
            file_path, summary = self.export_service.export_maintenance_excel(date_str, filters)
            QMessageBox.information(
                self, 
                "导出成功", 
                f"Excel 维保台账已生成！\n\n文件路径：{file_path}\n记录条数：{summary['total_count']}"
            )
            self.exported.emit(str(file_path))
        except Exception as e:
            self.logger.exception("Export failed")
            QMessageBox.critical(self, "导出失败", f"生成 Excel 时发生错误：\n{str(e)}")

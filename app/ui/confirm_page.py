from __future__ import annotations
from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    PROJECT_OPTIONS,
    extract_wechat_sender,
    is_reserved_person_name,
    normalize_worker_names_text,
)
from app.corrections import CorrectionsLogService
from app.database import SQLiteDataPool


SYSTEM_CATEGORY_OPTIONS = ["全部", "火灾报警", "视频监控", "其他装置及设备"]
WORK_TYPE_OPTIONS = ["全部", "安全交底 / 会议类", "培训", "巡检", "测试", "维修或维护", "其他"]
STATUS_OPTIONS = ["完成", "未完成", "待确认"]


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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title_label = QLabel("人工确认")
        title_label.setObjectName("PlaceholderTitle")

        desc_label = QLabel(
            "对 parsed_records 进行人工修正、重新映射和确认处理。"
            "下方详情区适合长期录入核对使用。"
        )
        desc_label.setObjectName("PlaceholderDescription")
        desc_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(self._build_filters())
        layout.addWidget(self._build_main_splitter(), 1)

        self.refresh_page()

    def _build_filters(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(5, 1)

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
        layout.addWidget(QLabel("系统类别"), 0, 4)
        layout.addWidget(self.system_filter, 0, 5)
        layout.addWidget(QLabel("工作类型"), 1, 0)
        layout.addWidget(self.work_type_filter, 1, 1)
        layout.addWidget(QLabel("关键词"), 1, 2)
        layout.addWidget(self.keyword_input, 1, 3, 1, 2)
        layout.addWidget(refresh_button, 1, 5)
        return layout

    def _build_main_splitter(self) -> QSplitter:
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(8)
        top_panel = self._build_table()
        bottom_panel = self._build_editor()
        top_panel.setMinimumHeight(180)
        bottom_panel.setMinimumHeight(240)
        self.main_splitter.addWidget(top_panel)
        self.main_splitter.addWidget(bottom_panel)
        self.main_splitter.setStretchFactor(0, 45)
        self.main_splitter.setStretchFactor(1, 55)
        self.main_splitter.setSizes([450, 550])
        return self.main_splitter

    def _build_table(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("PlaceholderCard")
        wrapper.setMinimumHeight(180)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        table_title = QLabel("待确认记录")
        table_title.setObjectName("PlaceholderTitle")
        layout.addWidget(table_title)

        self.table = QTableWidget(0, 12)
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
                "确认状态",
                "描述摘要",
            ]
        )
        self.table.setObjectName("InputArea")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.load_selected_record)
        layout.addWidget(self.table, 1)
        return wrapper

    def _build_editor(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("PlaceholderCard")
        wrapper.setMinimumHeight(240)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        editor_title = QLabel("记录详情编辑")
        editor_title.setObjectName("PlaceholderTitle")
        layout.addWidget(editor_title)

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
        self.duration_input.setObjectName("InputBox")
        self.duration_input.setRange(0, 999.0)
        self.duration_input.setDecimals(2)
        self.wechat_nickname_input = QLineEdit()
        self.wechat_nickname_input.setObjectName("InputBox")
        self.worker_names_input = QLineEdit()
        self.worker_names_input.setObjectName("InputBox")
        self.worker_names_input.setPlaceholderText("人员待确认")
        self.location_input = QLineEdit()
        self.location_input.setObjectName("InputBox")
        self.device_or_part_input = QLineEdit()
        self.device_or_part_input.setObjectName("InputBox")

        for widget in (
            self.work_date_input,
            self.project_input,
            self.system_category_input,
            self.work_type_input,
            self.status_input,
            self.start_time_input,
            self.end_time_input,
            self.duration_input,
            self.wechat_nickname_input,
            self.worker_names_input,
            self.location_input,
            self.device_or_part_input,
        ):
            self._prepare_field_widget(widget)

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
        self.source_raw_text_input.setMinimumHeight(120)
        self.source_raw_text_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        for widget in (
            self.problem_description_input,
            self.solution_input,
            self.result_input,
            self.note_input,
        ):
            widget.setMinimumHeight(90)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("ConfirmTabs")
        self.tabs.addTab(self._build_basic_info_tab(), "基础信息")
        self.tabs.addTab(self._build_process_info_tab(), "处理信息")
        self.tabs.addTab(self._build_source_text_tab(), "原始文本")
        layout.addWidget(self.tabs, 1)

        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)

        self.save_button = QPushButton("保存修改")
        self.remap_worker_button = QPushButton("重新映射人员")
        self.confirm_button = QPushButton("确认为有效记录")
        self.ignore_button = QPushButton("忽略该记录")
        self.restore_button = QPushButton("恢复为待确认")
        self.refresh_button = QPushButton("刷新列表")

        for button, object_name in (
            (self.save_button, "PrimaryButton"),
            (self.remap_worker_button, "SecondaryButton"),
            (self.confirm_button, "PrimaryButton"),
            (self.ignore_button, "SecondaryButton"),
            (self.restore_button, "SecondaryButton"),
            (self.refresh_button, "SecondaryButton"),
        ):
            button.setObjectName(object_name)
            footer_layout.addWidget(button)

        self.remap_worker_button.setToolTip("优先使用微信网名；若为空，则尝试从原始文本识别后重新映射。")
        self.remap_worker_button.clicked.connect(self.run_worker_mapping)
        footer_layout.addStretch(1)
        layout.addWidget(footer_widget)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.feedback_label)

        self.save_button.clicked.connect(self.save_changes)
        self.confirm_button.clicked.connect(self.confirm_record)
        self.ignore_button.clicked.connect(self.ignore_record)
        self.restore_button.clicked.connect(self.restore_pending)
        self.refresh_button.clicked.connect(self.refresh_page)
        return wrapper

    def _build_basic_info_tab(self) -> QWidget:
        tab = QFrame()
        tab.setObjectName("DetailPanel")
        layout = QGridLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        left_fields = (
            ("日期", self.work_date_input),
            ("项目", self.project_input),
            ("系统类别", self.system_category_input),
            ("工作类型", self.work_type_input),
            ("状态", self.status_input),
            ("用时H", self.duration_input),
        )
        right_fields = (
            ("开始时间", self.start_time_input),
            ("结束时间", self.end_time_input),
            ("微信网名", self.wechat_nickname_input),
            ("维修人员", self.worker_names_input),
            ("地点", self.location_input),
            ("设备/部位", self.device_or_part_input),
        )

        for row, (title, widget) in enumerate(left_fields):
            layout.addWidget(self._create_form_label(title), row, 0)
            layout.addWidget(widget, row, 1)

        for row, (title, widget) in enumerate(right_fields):
            layout.addWidget(self._create_form_label(title), row, 2)
            layout.addWidget(widget, row, 3)

        layout.setRowStretch(len(left_fields), 1)
        return tab

    def _build_process_info_tab(self) -> QWidget:
        tab = QFrame()
        tab.setObjectName("DetailPanel")
        layout = QGridLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)

        layout.addWidget(self._build_text_block("问题/工作描述", self.problem_description_input), 0, 0)
        layout.addWidget(self._build_text_block("处理方法", self.solution_input), 0, 1)
        layout.addWidget(self._build_text_block("结果", self.result_input), 1, 0)
        layout.addWidget(self._build_text_block("备注", self.note_input), 1, 1)
        return tab

    def _build_source_text_tab(self) -> QWidget:
        tab = QFrame()
        tab.setObjectName("DetailPanel")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        layout.addWidget(self._build_text_block("原始文本（只读）", self.source_raw_text_input), 1)
        return tab

    def _build_text_block(self, title: str, widget: QPlainTextEdit) -> QWidget:
        block = QWidget()
        block_layout = QVBoxLayout(block)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(6)
        label = QLabel(title)
        label.setObjectName("FieldLabel")
        block_layout.addWidget(label)
        block_layout.addWidget(widget, 1)
        return block

    def _create_form_label(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("FieldLabel")
        label.setFixedWidth(86)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _prepare_field_widget(self, widget: QWidget) -> None:
        widget.setMinimumWidth(180)
        widget.setMinimumHeight(32)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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
            worker_names = self._display_worker_names(str(row.get("worker_names", "")))
            summary = self._build_summary_text(row)
            values = [
                str(row.get("id", "")),
                str(row.get("work_date", "")),
                str(row.get("project", "")),
                str(row.get("system_category", "")),
                str(row.get("work_type", "")),
                str(row.get("status", "")),
                self._format_time_range(str(row.get("start_time", "")), str(row.get("end_time", ""))),
                self._format_duration(row.get("duration_hours", 0)),
                self._sanitize_wechat_nickname(str(row.get("wechat_nickname", ""))),
                worker_names or "人员待确认",
                str(row.get("confirm_status", "")),
                summary,
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))

            if selected_record_id is not None and int(row.get("id", 0)) == selected_record_id:
                selected_row_index = row_index

        self._apply_table_widths()
        if selected_row_index is not None:
            self.table.selectRow(selected_row_index)
            return

        self.table.clearSelection()
        self._clear_editor()

    def _apply_table_widths(self) -> None:
        widths = [60, 96, 120, 110, 110, 78, 118, 76, 120, 120, 96]
        for index, width in enumerate(widths):
            self.table.setColumnWidth(index, width)

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
        self.system_category_input.setCurrentText(
            str(record.get("system_category", "")) or "其他装置及设备"
        )
        self.work_type_input.setCurrentText(str(record.get("work_type", "")) or "其他")
        self.status_input.setCurrentText(str(record.get("status", "")) or "待确认")
        self.start_time_input.setText(str(record.get("start_time", "")))
        self.end_time_input.setText(str(record.get("end_time", "")))
        self.duration_input.setValue(float(record.get("duration_hours", 0.0) or 0.0))
        self.wechat_nickname_input.setText(
            self._sanitize_wechat_nickname(str(record.get("wechat_nickname", "")))
        )
        self.worker_names_input.setText(self._display_worker_names(str(record.get("worker_names", ""))))
        self.location_input.setText(str(record.get("location", "")))
        self.device_or_part_input.setText(str(record.get("device_or_part", "")))
        self.problem_description_input.setPlainText(str(record.get("problem_description", "")))
        self.solution_input.setPlainText(str(record.get("solution", "")))
        self.result_input.setPlainText(str(record.get("result", "")))
        self.note_input.setPlainText(str(record.get("note", "")))
        self.source_raw_text_input.setPlainText(str(record.get("source_raw_text", "")))

        feedback_text = f"已加载记录 ID: {record_id}"
        feedback_color = ""
        if not self.worker_names_input.text().strip():
            if self.wechat_nickname_input.text().strip():
                feedback_text = f"已加载 ID: {record_id} | 可点击“重新映射人员”补全真实姓名。"
                feedback_color = "color: #93C5FD;"
            elif self._extract_sender_from_text(self.source_raw_text_input.toPlainText()):
                feedback_text = f"已加载 ID: {record_id} | 原始文本中检测到疑似网名，可尝试“重新映射人员”。"
                feedback_color = "color: #93C5FD;"
        self.feedback_label.setText(feedback_text)
        self.feedback_label.setStyleSheet(feedback_color)

    def run_worker_mapping(self) -> None:
        if self.current_record_id is None:
            self.feedback_label.setText("请先选择一条记录。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        mapping_source = self._sanitize_wechat_nickname(self.wechat_nickname_input.text())
        if not mapping_source:
            mapping_source = self._sanitize_wechat_nickname(
                self._extract_sender_from_text(self.source_raw_text_input.toPlainText())
            )
            if mapping_source:
                self.wechat_nickname_input.setText(mapping_source)

        if not mapping_source:
            self.worker_names_input.clear()
            self.feedback_label.setText("未找到可用于映射的微信网名，请先核对原始文本。")
            self.feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        mapping_result = self.data_pool.resolve_worker_names(mapping_source)
        mapped_names = mapping_result["mapped_names"]

        if mapped_names:
            self.worker_names_input.setText(mapped_names)
            if mapping_result["employee_confirm_required"]:
                self.feedback_label.setText("未找到实名映射，已回填原始网名，请人工核对后保存。")
                self.feedback_label.setStyleSheet("color: #FCD34D;")
            else:
                self.feedback_label.setText("人员重新映射成功，已填入真实姓名。")
                self.feedback_label.setStyleSheet("color: #86EFAC;")
            return

        self.worker_names_input.clear()
        self.feedback_label.setText("未在员工映射表中找到对应人员，已清空错误人员值。")
        self.feedback_label.setStyleSheet("color: #FCA5A5;")

    def _collect_updates(self) -> dict[str, Any]:
        wechat_nickname = self._sanitize_wechat_nickname(self.wechat_nickname_input.text())
        worker_names, employee_confirm_required = self._normalize_worker_for_save(
            self.worker_names_input.text(),
            wechat_nickname,
        )
        self.worker_names_input.setText(worker_names)

        return {
            "work_date": self.work_date_input.text().strip(),
            "project": self.project_input.currentText().strip(),
            "system_category": self.system_category_input.currentText().strip(),
            "work_type": self.work_type_input.currentText().strip(),
            "status": self.status_input.currentText().strip(),
            "start_time": self.start_time_input.text().strip(),
            "end_time": self.end_time_input.text().strip(),
            "duration_hours": round(float(self.duration_input.value()), 2),
            "wechat_nickname": wechat_nickname,
            "worker_names": worker_names,
            "employee_confirm_required": 1 if employee_confirm_required else 0,
            "location": self.location_input.text().strip(),
            "device_or_part": self.device_or_part_input.text().strip(),
            "problem_description": self.problem_description_input.toPlainText().strip(),
            "solution": self.solution_input.toPlainText().strip(),
            "result": self.result_input.toPlainText().strip(),
            "note": self.note_input.toPlainText().strip(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _normalize_worker_for_save(
        self,
        worker_names_text: str,
        wechat_nickname: str,
    ) -> tuple[str, bool]:
        worker_names = normalize_worker_names_text(worker_names_text)
        if not worker_names:
            return "", True

        mapping_result = self.data_pool.resolve_worker_names(worker_names)
        mapped_names = mapping_result["mapped_names"]
        if mapped_names and not mapping_result["employee_confirm_required"]:
            return mapped_names, False

        if wechat_nickname:
            wechat_mapping = self.data_pool.resolve_worker_names(wechat_nickname)
            if wechat_mapping["mapped_names"] and not wechat_mapping["employee_confirm_required"]:
                return wechat_mapping["mapped_names"], False

        return worker_names, True

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

    def _extract_sender_from_text(self, text: str) -> str:
        return extract_wechat_sender(text)

    def _sanitize_wechat_nickname(self, nickname: str) -> str:
        normalized_nickname = str(nickname or "").strip()
        if not normalized_nickname or is_reserved_person_name(normalized_nickname):
            return ""
        return normalized_nickname

    def _display_worker_names(self, worker_names: str) -> str:
        return normalize_worker_names_text(worker_names)

    def _build_summary_text(self, row: dict[str, Any]) -> str:
        summary_text = str(row.get("problem_description", "")).strip()
        if not summary_text:
            summary_text = str(row.get("source_raw_text", "")).replace("\n", " ").strip()
        return summary_text[:120]

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

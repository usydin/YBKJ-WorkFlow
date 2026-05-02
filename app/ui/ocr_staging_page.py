from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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

from app.ocr_staging_service import OCRStagingService


SOURCE_TYPE_OPTIONS = {
    "手动粘贴": "manual_paste",
    "截图识别结果": "screenshot",
    "微信长图识别结果": "wechat_image",
    "其他": "future_ocr",
}
STATUS_OPTIONS = {
    "全部": "",
    "draft": "draft",
    "confirmed": "confirmed",
    "imported": "imported",
    "ignored": "ignored",
}


class OCRStagingPage(QFrame):
    imported = Signal()
    updated = Signal()

    def __init__(self, staging_service: OCRStagingService) -> None:
        super().__init__()
        self.staging_service = staging_service
        self.logger = logging.getLogger("ybkj_workflow.ui.ocr_staging")
        self.current_record_id: int | None = None
        self.setObjectName("PlaceholderCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_create_card())
        layout.addWidget(self._build_list_card(), 1)
        layout.addWidget(self._build_detail_card(), 1)

        footer_label = QLabel("导入 raw_inputs 后，请进入智能解析页面继续解析。")
        footer_label.setObjectName("MetaText")
        footer_label.setWordWrap(True)
        layout.addWidget(footer_label)

        self.refresh_page()

    def _build_header(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("DashboardCard")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        title = QLabel("OCR暂存区")
        title.setObjectName("PlaceholderTitle")
        desc = QLabel(
            "本页用于暂存未来截图识别/OCR/微信长图识别得到的文本。"
            "当前版本先支持手动粘贴 OCR 结果，确认后再导入原始输入池。"
        )
        desc.setObjectName("PlaceholderDescription")
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        return wrapper

    def _build_create_card(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("DashboardCard")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("新增暂存文本")
        title.setObjectName("PlaceholderTitle")

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.source_type_input = QComboBox()
        self.source_type_input.setObjectName("InputBox")
        self.source_type_input.addItems(list(SOURCE_TYPE_OPTIONS.keys()))

        self.source_name_input = QLineEdit()
        self.source_name_input.setObjectName("InputBox")
        self.source_name_input.setPlaceholderText("例如：手动粘贴、微信截图01")

        self.create_note_input = QLineEdit()
        self.create_note_input.setObjectName("InputBox")
        self.create_note_input.setPlaceholderText("可选备注")

        self.create_text_input = QPlainTextEdit()
        self.create_text_input.setObjectName("InputArea")
        self.create_text_input.setPlaceholderText("请粘贴 OCR 结果文本或截图转写文本。")
        self.create_text_input.setMinimumHeight(140)

        save_button = QPushButton("保存到暂存区")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.create_record)

        self.create_feedback_label = QLabel("")
        self.create_feedback_label.setObjectName("FeedbackLabel")
        self.create_feedback_label.setWordWrap(True)

        form.addWidget(QLabel("来源类型"), 0, 0)
        form.addWidget(self.source_type_input, 0, 1)
        form.addWidget(QLabel("来源名称"), 0, 2)
        form.addWidget(self.source_name_input, 0, 3)
        form.addWidget(QLabel("备注"), 1, 0)
        form.addWidget(self.create_note_input, 1, 1, 1, 3)

        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(self.create_text_input)
        layout.addWidget(save_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.create_feedback_label)
        return wrapper

    def _build_list_card(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("DashboardCard")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        title = QLabel("暂存记录列表")
        title.setObjectName("PlaceholderTitle")

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("InputBox")
        self.status_filter.addItems(list(STATUS_OPTIONS.keys()))
        self.status_filter.currentTextChanged.connect(self.refresh_page)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        top_row.addWidget(title)
        top_row.addStretch(1)
        top_row.addWidget(QLabel("状态筛选"))
        top_row.addWidget(self.status_filter)
        top_row.addWidget(refresh_button)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("InputArea")
        self.table.setHorizontalHeaderLabels(
            ["ID", "状态", "来源类型", "来源名称", "文本摘要", "创建时间", "导入状态"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self.load_selected_record)

        layout.addLayout(top_row)
        layout.addWidget(self.table, 1)
        return wrapper

    def _build_detail_card(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("DashboardCard")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("详情编辑")
        title.setObjectName("PlaceholderTitle")

        self.detail_status_label = QLabel("请选择一条暂存记录。")
        self.detail_status_label.setObjectName("MetaText")
        self.detail_status_label.setWordWrap(True)

        self.raw_text_input = QPlainTextEdit()
        self.raw_text_input.setObjectName("InputArea")
        self.raw_text_input.setReadOnly(True)
        self.raw_text_input.setPlaceholderText("原始文本")
        self.raw_text_input.setMinimumHeight(120)

        self.cleaned_text_input = QPlainTextEdit()
        self.cleaned_text_input.setObjectName("InputArea")
        self.cleaned_text_input.setPlaceholderText("可在此修正 OCR 文本后再导入 raw_inputs。")
        self.cleaned_text_input.setMinimumHeight(120)

        self.detail_note_input = QPlainTextEdit()
        self.detail_note_input.setObjectName("InputArea")
        self.detail_note_input.setPlaceholderText("可记录人工修正说明或导入备注。")
        self.detail_note_input.setMaximumHeight(100)

        button_row = QHBoxLayout()
        save_button = QPushButton("保存修正")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_record)

        import_button = QPushButton("确认导入 raw_inputs")
        import_button.setObjectName("PrimaryButton")
        import_button.clicked.connect(self.import_record)

        ignore_button = QPushButton("标记忽略")
        ignore_button.setObjectName("SecondaryButton")
        ignore_button.clicked.connect(self.ignore_record)

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self.refresh_page)

        button_row.addWidget(save_button)
        button_row.addWidget(import_button)
        button_row.addWidget(ignore_button)
        button_row.addWidget(refresh_button)
        button_row.addStretch(1)

        self.detail_feedback_label = QLabel("")
        self.detail_feedback_label.setObjectName("FeedbackLabel")
        self.detail_feedback_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.detail_status_label)
        layout.addWidget(QLabel("原始文本"))
        layout.addWidget(self.raw_text_input)
        layout.addWidget(QLabel("修正文本"))
        layout.addWidget(self.cleaned_text_input)
        layout.addWidget(QLabel("备注"))
        layout.addWidget(self.detail_note_input)
        layout.addLayout(button_row)
        layout.addWidget(self.detail_feedback_label)
        return wrapper

    def create_record(self) -> None:
        try:
            record_id = self.staging_service.create_staging_record(
                raw_text=self.create_text_input.toPlainText(),
                source_type=SOURCE_TYPE_OPTIONS[self.source_type_input.currentText()],
                source_name=self.source_name_input.text().strip(),
                note=self.create_note_input.text().strip(),
            )
        except Exception as exc:
            self.create_feedback_label.setText(str(exc))
            self.create_feedback_label.setStyleSheet("color: #FCA5A5;")
            return

        self.create_feedback_label.setText(f"暂存成功，记录 ID：{record_id}")
        self.create_feedback_label.setStyleSheet("color: #86EFAC;")
        self.create_text_input.clear()
        self.source_name_input.clear()
        self.create_note_input.clear()
        self.refresh_page()
        self.updated.emit()

    def refresh_page(self) -> None:
        status_text = STATUS_OPTIONS.get(self.status_filter.currentText(), "")
        rows = self.staging_service.list_staging_records(status=status_text or None)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            text_summary = (
                str(row.get("cleaned_text", "")).strip()
                or str(row.get("raw_text", "")).strip()
            ).replace("\n", " ")[:80]
            imported_raw_input_id = row.get("imported_raw_input_id")
            values = [
                str(row.get("id", "")),
                str(row.get("status", "")),
                str(row.get("source_type", "")),
                str(row.get("source_name", "")),
                text_summary,
                str(row.get("created_at", "")),
                f"已导入: {imported_raw_input_id}" if imported_raw_input_id else "未导入",
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
        if self.current_record_id is not None:
            for row_index in range(self.table.rowCount()):
                item = self.table.item(row_index, 0)
                if item and item.text() == str(self.current_record_id):
                    self.table.selectRow(row_index)
                    break

    def load_selected_record(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.current_record_id = None
            self._clear_detail()
            return

        record_id = int(selected_items[0].text())
        record = self.staging_service.get_staging_record(record_id)
        if record is None:
            self.current_record_id = None
            self._clear_detail()
            return

        self.current_record_id = record_id
        self.raw_text_input.setPlainText(str(record.get("raw_text", "")))
        self.cleaned_text_input.setPlainText(str(record.get("cleaned_text", "")))
        self.detail_note_input.setPlainText(str(record.get("note", "")))
        imported_raw_input_id = record.get("imported_raw_input_id")
        self.detail_status_label.setText(
            f"当前记录状态：{record.get('status', '')}｜来源：{record.get('source_type', '')}"
            + (f"｜已导入 raw_input ID：{imported_raw_input_id}" if imported_raw_input_id else "")
        )
        self.detail_feedback_label.clear()

    def save_record(self) -> None:
        if self.current_record_id is None:
            self._show_detail_error("请先选择一条暂存记录。")
            return
        try:
            self.staging_service.update_staging_record(
                self.current_record_id,
                cleaned_text=self.cleaned_text_input.toPlainText(),
                note=self.detail_note_input.toPlainText(),
                status="confirmed",
            )
        except Exception as exc:
            self._show_detail_error(str(exc))
            return

        self.detail_feedback_label.setText("保存成功，当前记录已标记为 confirmed。")
        self.detail_feedback_label.setStyleSheet("color: #86EFAC;")
        self.refresh_page()
        self.updated.emit()

    def import_record(self) -> None:
        if self.current_record_id is None:
            self._show_detail_error("请先选择一条暂存记录。")
            return
        try:
            result = self.staging_service.import_to_raw_inputs(self.current_record_id)
        except Exception as exc:
            self._show_detail_error(str(exc))
            return

        self.detail_feedback_label.setText(
            f"导入成功：已写入 raw_inputs，ID {result['imported_raw_input_id']}。请继续到智能解析页处理。"
        )
        self.detail_feedback_label.setStyleSheet("color: #86EFAC;")
        self.refresh_page()
        self.imported.emit()
        self.updated.emit()

    def ignore_record(self) -> None:
        if self.current_record_id is None:
            self._show_detail_error("请先选择一条暂存记录。")
            return
        try:
            self.staging_service.mark_ignored(self.current_record_id)
        except Exception as exc:
            self._show_detail_error(str(exc))
            return

        self.detail_feedback_label.setText("已标记为 ignored。")
        self.detail_feedback_label.setStyleSheet("color: #86EFAC;")
        self.refresh_page()
        self.updated.emit()

    def _clear_detail(self) -> None:
        self.raw_text_input.clear()
        self.cleaned_text_input.clear()
        self.detail_note_input.clear()
        self.detail_status_label.setText("请选择一条暂存记录。")
        self.detail_feedback_label.clear()

    def _show_detail_error(self, message: str) -> None:
        self.detail_feedback_label.setText(message)
        self.detail_feedback_label.setStyleSheet("color: #FCA5A5;")

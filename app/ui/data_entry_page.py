from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.config import APP_INFO, PROJECT_OPTIONS
from app.intake_service import IntakeService


class DataEntryPage(QFrame):
    submitted = Signal()

    def __init__(self, intake_service: IntakeService) -> None:
        super().__init__()
        self.intake_service = intake_service
        self.logger = logging.getLogger("ybkj_workflow.ui.data_entry")
        self.current_source_type = "paste"
        self.current_source_name = "粘贴输入"
        self.current_source_path = ""
        self.setObjectName("PlaceholderCard")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 28, 28, 28)
        root_layout.setSpacing(18)

        title_label = QLabel("数据录入")
        title_label.setObjectName("PlaceholderTitle")
        desc_label = QLabel(
            "支持粘贴微信文本、导入 TXT 内容和手动补录单条记录。提交后将写入 SQLite 待解析表，并同步备份到 JSONL。"
        )
        desc_label.setWordWrap(True)
        desc_label.setObjectName("PlaceholderDescription")

        root_layout.addWidget(title_label)
        root_layout.addWidget(desc_label)
        root_layout.addLayout(self._build_form_row())
        root_layout.addLayout(self._build_manual_row())
        root_layout.addWidget(self._build_text_editor(), 1)
        root_layout.addLayout(self._build_action_row())

    def _build_form_row(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(10)

        operator_label = QLabel("操作员")
        operator_label.setObjectName("FieldLabel")
        self.operator_combo = QComboBox()
        self.operator_combo.setEditable(True)
        self.operator_combo.addItems([APP_INFO.developer, "值班员A", "值班员B"])
        self.operator_combo.setCurrentText(APP_INFO.developer)
        self.operator_combo.setObjectName("InputBox")

        project_label = QLabel("默认项目/服务对象")
        project_label.setObjectName("FieldLabel")
        self.project_combo = QComboBox()
        self.project_combo.addItems(PROJECT_OPTIONS)
        self.project_combo.setObjectName("InputBox")

        source_label = QLabel("当前来源")
        source_label.setObjectName("FieldLabel")
        self.source_type_label = QLabel("paste")
        self.source_type_label.setObjectName("MetaBadge")

        layout.addWidget(operator_label, 0, 0)
        layout.addWidget(self.operator_combo, 0, 1)
        layout.addWidget(project_label, 0, 2)
        layout.addWidget(self.project_combo, 0, 3)
        layout.addWidget(source_label, 1, 0)
        layout.addWidget(self.source_type_label, 1, 1)
        return layout

    def _build_manual_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("手动录入单条工作记录后，点击“加入文本区”")
        self.manual_input.setObjectName("InputBox")

        manual_button = QPushButton("加入文本区")
        manual_button.setObjectName("PrimaryButton")
        manual_button.clicked.connect(self.append_manual_record)

        import_button = QPushButton("导入 TXT")
        import_button.setObjectName("SecondaryButton")
        import_button.clicked.connect(self.import_txt_file)

        layout.addWidget(self.manual_input, 1)
        layout.addWidget(manual_button)
        layout.addWidget(import_button)
        return layout

    def _build_text_editor(self) -> QTextEdit:
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "请粘贴微信工作记录文本，或先导入 TXT 文件；导入后可继续人工修改后再提交。"
        )
        self.text_edit.setObjectName("InputArea")
        return self.text_edit

    def _build_action_row(self) -> QVBoxLayout:
        wrapper = QVBoxLayout()
        wrapper.setSpacing(10)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        submit_button = QPushButton("提交到待解析")
        submit_button.setObjectName("PrimaryButton")
        submit_button.clicked.connect(self.submit_input)

        clear_button = QPushButton("清空输入")
        clear_button.setObjectName("SecondaryButton")
        clear_button.clicked.connect(self.clear_inputs)

        button_row.addWidget(submit_button)
        button_row.addWidget(clear_button)
        button_row.addStretch(1)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("FeedbackLabel")
        self.feedback_label.setWordWrap(True)

        wrapper.addLayout(button_row)
        wrapper.addWidget(self.feedback_label)
        return wrapper

    def set_source_type(self, source_type: str) -> None:
        self.current_source_type = source_type
        self.source_type_label.setText(source_type)

    def set_source_context(
        self,
        source_type: str,
        source_name: str = "",
        source_path: str = "",
    ) -> None:
        self.current_source_name = source_name
        self.current_source_path = source_path
        self.set_source_type(source_type)

    def append_manual_record(self) -> None:
        manual_text = self.manual_input.text().strip()
        if not manual_text:
            self.show_feedback("手动录入内容为空，未追加。", is_error=True)
            return

        existing_text = self.text_edit.toPlainText().strip()
        merged_text = f"{existing_text}\n{manual_text}" if existing_text else manual_text
        self.text_edit.setPlainText(merged_text)
        self.manual_input.clear()
        self.set_source_context("manual", "手动录入", "")
        self.show_feedback("已加入文本区，可继续修改后再提交。")

    def import_txt_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入 TXT 文件",
            "",
            "Text Files (*.txt)",
        )
        if not file_path:
            return

        path = Path(file_path)
        if path.suffix.lower() != ".txt":
            self.logger.error("TXT import failed: unsupported file type: %s", path.name)
            self.show_feedback("仅支持导入 .txt 文件。", is_error=True)
            return

        try:
            content = self._read_txt_content(path)
        except Exception as exc:
            self.logger.error("TXT import failed: %s", exc)
            self.show_feedback("TXT 导入失败，请检查文件编码或内容。", is_error=True)
            return

        self.text_edit.setPlainText(content)
        self.set_source_context("txt", path.name, str(path))
        self.show_feedback(f"已导入 TXT 文件：{path.name}")

    def _read_txt_content(self, path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8")

    def submit_input(self) -> None:
        raw_text = self.text_edit.toPlainText().strip()
        if not raw_text:
            self.show_feedback("输入内容为空，无法提交。", is_error=True)
            return

        result = self.intake_service.submit_raw_input(
            operator_name=self.operator_combo.currentText(),
            source_type=self.current_source_type,
            source_name=self.current_source_name,
            source_path=self.current_source_path,
            default_project=self.project_combo.currentText(),
            raw_text=raw_text,
        )
        self.show_feedback(
            f"提交成功，记录已进入待解析队列。ID: {result['id']}，来源: {result['source_type']}"
        )
        self.submitted.emit()

    def clear_inputs(self) -> None:
        self.text_edit.clear()
        self.manual_input.clear()
        self.set_source_context("paste", "粘贴输入", "")
        self.show_feedback("输入内容已清空。")

    def show_feedback(self, message: str, *, is_error: bool = False) -> None:
        color = "#FCA5A5" if is_error else "#86EFAC"
        self.feedback_label.setText(message)
        self.feedback_label.setStyleSheet(f"color: {color};")

from __future__ import annotations

import logging
import signal
import sys
import traceback
from typing import Any

from PySide6.QtWidgets import QApplication

from app.backup import JSONLBackupService
from app.config import APP_INFO, ensure_runtime_directories
from app.database import SQLiteDataPool
from app.logging_setup import setup_logging
from app.parser_engine import ParserEngine
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLESHEET
from app.wecom import WeComIntegration


def install_exception_hook(logger: logging.Logger) -> None:
    def handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: Any,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "Unhandled exception\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        )

    sys.excepthook = handle_exception


def bootstrap_services(logger: logging.Logger) -> None:
    ensure_runtime_directories()

    db_path = SQLiteDataPool().initialize()
    backup_path = JSONLBackupService().initialize_backup_file()
    parser_engine = ParserEngine()
    wecom = WeComIntegration()

    logger.info("Database ready: %s", db_path)
    logger.info("JSONL backup ready: %s", backup_path)
    logger.info("Parser engine placeholder ready: %s", parser_engine.__class__.__name__)
    logger.info("WeCom enabled: %s", wecom.is_enabled())


def main() -> int:
    logger, run_log_path, error_log_path = setup_logging()
    install_exception_hook(logger)
    bootstrap_services(logger)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName(APP_INFO.project_name_en)
    qt_app.setOrganizationName(APP_INFO.developer)
    qt_app.setStyleSheet(APP_STYLESHEET)

    logger.info("Run log file: %s", run_log_path)
    logger.info("Error log file: %s", error_log_path)

    window = MainWindow()
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())

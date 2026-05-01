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
from app.intake_service import IntakeService
from app.local_config import LocalConfigService
from app.logging_setup import setup_logging
from app.parser_engine import ParserEngine
from app.ui.main_window import MainWindow
from app.ui.styles import get_stylesheet
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


def bootstrap_services(logger: logging.Logger) -> dict[str, Any]:
    ensure_runtime_directories()

    data_pool = SQLiteDataPool()
    db_path = data_pool.initialize()
    backup_service = JSONLBackupService()
    backup_path = backup_service.initialize_backup_file()
    parser_engine = ParserEngine(data_pool)
    wecom = WeComIntegration()
    intake_service = IntakeService(data_pool, backup_service)

    logger.info("Database ready: %s", db_path)
    logger.info("JSONL backup ready: %s", backup_path)
    logger.info("Parser engine ready: %s", parser_engine.__class__.__name__)
    logger.info("WeCom enabled: %s", wecom.is_enabled())
    return {
        "data_pool": data_pool,
        "backup_service": backup_service,
        "parser_engine": parser_engine,
        "wecom": wecom,
        "intake_service": intake_service,
    }


def main() -> int:
    logger, run_log_path, error_log_path = setup_logging()
    install_exception_hook(logger)
    services = bootstrap_services(logger)
    local_config_service = LocalConfigService()
    initial_theme = local_config_service.load_theme()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName(APP_INFO.project_name_en)
    qt_app.setOrganizationName(APP_INFO.developer)
    qt_app.setStyleSheet(get_stylesheet(initial_theme))

    logger.info("Initial theme: %s", initial_theme)
    logger.info("Run log file: %s", run_log_path)
    logger.info("Error log file: %s", error_log_path)

    window = MainWindow(
        data_pool=services["data_pool"],
        intake_service=services["intake_service"],
        parser_engine=services["parser_engine"],
        local_config_service=local_config_service,
        initial_theme=initial_theme,
    )
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())

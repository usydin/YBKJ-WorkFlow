from __future__ import annotations

import atexit
import logging
from datetime import datetime
from pathlib import Path

from app.config import LOGS_DIR, ensure_runtime_directories


def setup_logging() -> tuple[logging.Logger, Path, Path]:
    ensure_runtime_directories()

    timestamp = datetime.now()
    run_log_path = LOGS_DIR / f"run_{timestamp:%Y-%m-%d_%H%M%S}.log"
    error_log_path = LOGS_DIR / f"error_{timestamp:%Y-%m-%d}.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    run_handler = logging.FileHandler(run_log_path, encoding="utf-8")
    run_handler.setLevel(logging.INFO)
    run_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(error_log_path, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(run_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    app_logger = logging.getLogger("ybkj_workflow")
    app_logger.info("Application startup")

    atexit.register(logging.getLogger("ybkj_workflow").info, "Application shutdown")
    return app_logger, run_log_path, error_log_path

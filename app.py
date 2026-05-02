from __future__ import annotations

import argparse
import logging
import signal
import sys
import traceback
from typing import Any

from app import version
from app.path_utils import is_frozen, get_app_root, get_resource_path
from app.config import APP_INFO, ensure_runtime_directories, DATABASE_PATH, LOGS_DIR
from app.local_config import LocalConfigService
from app.logging_setup import setup_logging


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


def run_self_check(logger: logging.Logger) -> bool:
    """运行系统自检，返回是否通过。"""
    from app.config import ASSETS_DIR, DOCS_DIR, REPORTS_DIR, OUTPUTS_DIR, DATAPOOL_DIR
    import os

    print(f"\n{'='*20} 系统自检 {'='*20}")
    print(f"应用名称: {version.APP_NAME} ({version.APP_SHORT_NAME})")
    print(f"版本: {version.VERSION}")
    print(f"运行模式: {'打包版 (Frozen)' if is_frozen() else '源码版 (Source)'}")
    print(f"根目录: {get_app_root()}")
    
    # 1. 检查关键目录
    try:
        ensure_runtime_directories()
        print("[OK] 运行时目录检查通过")
    except Exception as e:
        print(f"[ERROR] 运行时目录创建失败: {e}")
        return False

    # 2. 检查目录可写性
    for name, path in [("数据池", DATAPOOL_DIR), ("报告", REPORTS_DIR), ("输出", OUTPUTS_DIR)]:
        if os.access(path, os.W_OK):
            print(f"[OK] {name}目录可写: {path}")
        else:
            print(f"[ERROR] {name}目录不可写: {path}")
            return False

    # 3. 检查静态资源
    for name, path in [("Assets", ASSETS_DIR), ("Docs", DOCS_DIR)]:
        if path.exists():
            print(f"[OK] {name}资源存在: {path}")
        else:
            print(f"[WARN] {name}资源缺失: {path}")

    # 4. 检查数据库
    try:
        from app.database import SQLiteDataPool
        data_pool = SQLiteDataPool()
        data_pool.initialize()
        print(f"[OK] 数据库连接正常: {DATABASE_PATH}")
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")
        return False

    # 5. 检查日志
    if LOGS_DIR.exists():
        print(f"[OK] 日志目录正常: {LOGS_DIR}")
    else:
        print("[WARN] 日志目录未创建")

    # 6. 打包建议 (仅源码模式)
    if not is_frozen():
        print(f"\n[提示] 源码开发模式，打包脚本位于: packaging/windows/")

    print(f"{'='*48}\n")
    return True


def bootstrap_services(logger: logging.Logger) -> dict[str, Any]:
    from app.backup import JSONLBackupService
    from app.analytics_service import AnalyticsService
    from app.corrections import CorrectionsLogService
    from app.database import SQLiteDataPool
    from app.intake_service import IntakeService
    from app.ocr_staging_service import OCRStagingService
    from app.parser_engine import ParserEngine
    from app.quality_service import QualityCheckService
    from app.report_service import DailyReportService
    from app.excel_export_service import ExcelExportService
    from app.wecom import WeComIntegration

    ensure_runtime_directories()

    data_pool = SQLiteDataPool()
    db_path = data_pool.initialize()
    cleaned_rows = data_pool.cleanup_reserved_person_names()
    backup_service = JSONLBackupService()
    backup_path = backup_service.initialize_backup_file()
    corrections_service = CorrectionsLogService()
    corrections_path = corrections_service.ensure_file()
    parser_engine = ParserEngine(data_pool)
    report_service = DailyReportService(data_pool)
    analytics_service = AnalyticsService(data_pool)
    quality_service = QualityCheckService(data_pool)
    excel_export_service = ExcelExportService(data_pool)
    wecom = WeComIntegration()
    intake_service = IntakeService(data_pool, backup_service)
    ocr_staging_service = OCRStagingService(data_pool, intake_service)

    logger.info("Database ready: %s", db_path)
    if cleaned_rows:
        logger.info("Reserved person fields cleaned: %s", cleaned_rows)
    logger.info("JSONL backup ready: %s", backup_path)
    logger.info("Corrections log ready: %s", corrections_path)
    logger.info("Parser engine ready: %s", parser_engine.__class__.__name__)
    logger.info("Report service ready: %s", report_service.__class__.__name__)
    logger.info("Analytics service ready: %s", analytics_service.__class__.__name__)
    logger.info("Quality service ready: %s", quality_service.__class__.__name__)
    logger.info("Excel export service ready: %s", excel_export_service.__class__.__name__)
    logger.info("OCR staging service ready: %s", ocr_staging_service.__class__.__name__)
    logger.info("WeCom enabled: %s", wecom.is_enabled())
    return {
        "data_pool": data_pool,
        "backup_service": backup_service,
        "corrections_service": corrections_service,
        "parser_engine": parser_engine,
        "report_service": report_service,
        "analytics_service": analytics_service,
        "quality_service": quality_service,
        "excel_export_service": excel_export_service,
        "ocr_staging_service": ocr_staging_service,
        "wecom": wecom,
        "intake_service": intake_service,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{version.APP_NAME} 启动程序")
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")
    parser.add_argument("--self-check", action="store_true", help="运行系统自检")
    parser.add_argument("--no-gui-diagnose", action="store_true", help="以无界面模式运行诊断")
    args = parser.parse_args()

    if args.version:
        print(f"{version.APP_NAME} {version.VERSION}")
        print(f"{version.COPYRIGHT}")
        return 0

    logger, run_log_path, error_log_path = setup_logging()
    
    if args.self_check or args.no_gui_diagnose:
        success = run_self_check(logger)
        if args.self_check:
            return 0 if success else 1
        # no-gui-diagnose 继续运行或在此停止取决于需求，目前诊断完即止
        return 0 if success else 1

    # 仅在需要启动 GUI 时才导入 GUI 相关模块
    try:
        from PySide6.QtWidgets import QApplication
        from app.ui.main_window import MainWindow
        from app.ui.styles import get_stylesheet
    except ImportError as e:
        logger.error("无法加载 GUI 模块 (PySide6)，请检查依赖安装。错误: %s", e)
        print(f"[ERROR] 无法启动 GUI: {e}")
        return 1

    install_exception_hook(logger)
    services = bootstrap_services(logger)
    local_config_service = LocalConfigService()
    initial_theme = local_config_service.load_theme()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_INFO.project_name_cn)
    app.setApplicationVersion(APP_INFO.version)

    window = MainWindow(services)
    window.setWindowTitle(f"{APP_INFO.tool_name} {APP_INFO.version}")
    
    # 应用主题
    app.setStyleSheet(get_stylesheet(initial_theme))
    
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

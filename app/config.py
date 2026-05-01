from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppInfo:
    project_name_cn: str = "友邦维保工作流系统"
    tool_name: str = "维保日报通"
    project_name_en: str = "YBKJ-WorkFlow"
    version: str = "V1.0 beta"
    developer: str = "ybkj-pL"
    copyright_text: str = "Copyright © 2026 @B‘lock10STUdio"

    @property
    def product_line(self) -> str:
        return f"{self.tool_name} · {self.project_name_en}"


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs"
DATAPOOL_DIR = BASE_DIR / "datapool"
SQLITE_DIR = DATAPOOL_DIR / "sqlite"
JSONL_DIR = DATAPOOL_DIR / "jsonl"
EXPORT_HISTORY_DIR = DATAPOOL_DIR / "exports_history"
OUTPUTS_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"
DATASET_DIR = BASE_DIR / "dataset"
MODEL_PACK_DIR = BASE_DIR / "model_pack"
LOCAL_CONFIG_PATH = BASE_DIR / "config.local.json"
LOGO_PATH = ASSETS_DIR / "logo.png"
DATABASE_PATH = SQLITE_DIR / "ybkj_workflow.db"
JSONL_BACKUP_PATH = EXPORT_HISTORY_DIR / "records_backup.jsonl"
RAW_INPUTS_JSONL_PATH = JSONL_DIR / "raw_inputs.jsonl"
WECOM_ENABLED = False

PROJECT_OPTIONS = [
    "石炼化",
    "康石",
    "沧炼",
    "人才公寓",
    "信息中心",
    "行政",
    "幼儿园",
    "其他",
]

SOURCE_TYPES = ("paste", "txt", "manual")
RECORD_STATUSES = ("pending_parse", "parsed", "confirmed", "archived")
THEMES = ("dark", "light")

APP_INFO = AppInfo()


def ensure_runtime_directories() -> None:
    directories = [
        LOGS_DIR,
        SQLITE_DIR,
        JSONL_DIR,
        EXPORT_HISTORY_DIR,
        OUTPUTS_DIR / "excel",
        OUTPUTS_DIR / "word",
        OUTPUTS_DIR / "pdf",
        OUTPUTS_DIR / "text",
        REPORTS_DIR / "daily",
        REPORTS_DIR / "statistics",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

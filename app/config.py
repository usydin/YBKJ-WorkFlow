from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


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
QUALITY_REPORTS_DIR = REPORTS_DIR / "quality"
DATASET_DIR = BASE_DIR / "dataset"
SAMPLES_DIR = DATASET_DIR / "samples"
SCREENSHOTS_RAW_DIR = SAMPLES_DIR / "screenshots_raw"
TEXT_SAMPLES_DIR = SAMPLES_DIR / "text_samples"
PARSED_EXPECTED_DIR = SAMPLES_DIR / "parsed_expected"
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

SOURCE_TYPES = ("paste", "txt", "manual", "screenshot", "batch_txt", "unknown")
RECORD_STATUSES = ("pending_parse", "parsed", "confirmed", "archived")
THEMES = ("dark", "light")

APP_INFO = AppInfo()
WORKER_NAME_SPLIT_PATTERN = re.compile(r"[、，,/\s；;]+")
SENDER_PREFIX_PATTERN = re.compile(r"^([\u4e00-\u9fffA-Za-z0-9_()（）\-·]{2,20})[:：]")
CHAT_TIMESTAMP_PATTERN = re.compile(r"^(.+?)\s*\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2}(?::\d{2})?$")
LEADING_CJK_NAME_PATTERN = re.compile(r"^([\u4e00-\u9fff]{2,12})")


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
        QUALITY_REPORTS_DIR,
        SCREENSHOTS_RAW_DIR,
        TEXT_SAMPLES_DIR,
        PARSED_EXPECTED_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def to_relative_source_path(path_value: str | Path | None) -> str:
    if not path_value:
        return ""

    path = Path(path_value)
    try:
        return path.resolve().relative_to(BASE_DIR.resolve()).as_posix()
    except ValueError:
        return path.name
    except OSError:
        return path.as_posix()


def safe_row_value(row: dict[str, Any], key: str, default: str = "") -> Any:
    value = row.get(key, default)
    return default if value is None else value


def is_reserved_person_name(name: str) -> bool:
    normalized_name = str(name or "").strip().casefold()
    if not normalized_name:
        return False
    return normalized_name == APP_INFO.developer.casefold()


def split_worker_names_text(worker_names: str) -> list[str]:
    normalized_text = str(worker_names or "").strip()
    if not normalized_text:
        return []

    values: list[str] = []
    seen: set[str] = set()
    for item in WORKER_NAME_SPLIT_PATTERN.split(normalized_text):
        normalized_item = item.strip()
        if not normalized_item or is_reserved_person_name(normalized_item):
            continue
        if normalized_item not in seen:
            values.append(normalized_item)
            seen.add(normalized_item)
    return values


def normalize_worker_names_text(worker_names: str) -> str:
    return "、".join(split_worker_names_text(worker_names))


def extract_wechat_sender(text: str) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        return ""

    first_line = lines[0]
    match = SENDER_PREFIX_PATTERN.match(first_line)
    if match:
        return _normalize_sender_candidate(match.group(1))

    timestamp_match = CHAT_TIMESTAMP_PATTERN.match(first_line)
    if timestamp_match:
        return _normalize_sender_candidate(timestamp_match.group(1))
    return ""


def _normalize_sender_candidate(candidate: str) -> str:
    normalized = str(candidate or "").strip().strip("-:：|")
    if not normalized:
        return ""

    for separator in ("（", "(", "【", "["):
        if separator in normalized:
            prefix = normalized.split(separator, 1)[0].strip()
            if len(prefix) >= 2:
                normalized = prefix
            break

    cjk_match = LEADING_CJK_NAME_PATTERN.match(normalized)
    if cjk_match:
        return cjk_match.group(1).strip()

    normalized = normalized.rstrip(".。·-_ ")
    token_match = re.match(r"^[A-Za-z0-9_\-·]{2,20}", normalized)
    if token_match:
        return token_match.group(0).strip()
    return normalized[:20].strip()

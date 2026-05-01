from __future__ import annotations

import json
import logging
from typing import Any

from app.config import LOCAL_CONFIG_PATH, THEMES


class LocalConfigService:
    def __init__(self) -> None:
        self.logger = logging.getLogger("ybkj_workflow.local_config")

    def load(self) -> dict[str, Any]:
        if not LOCAL_CONFIG_PATH.exists():
            return {}

        try:
            with LOCAL_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
                data = json.load(config_file)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError) as exc:
            self.logger.warning("Failed to load local config, fallback to defaults: %s", exc)

        return {}

    def save(self, config: dict[str, Any]) -> None:
        try:
            with LOCAL_CONFIG_PATH.open("w", encoding="utf-8") as config_file:
                json.dump(config, config_file, ensure_ascii=False, indent=2)
        except OSError as exc:
            self.logger.warning("Failed to save local config: %s", exc)

    def load_theme(self) -> str:
        theme = self.load().get("theme", "dark")
        return theme if theme in THEMES else "dark"

    def save_theme(self, theme: str) -> None:
        normalized_theme = theme if theme in THEMES else "dark"
        config = self.load()
        config["theme"] = normalized_theme
        self.save(config)

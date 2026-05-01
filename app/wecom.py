from __future__ import annotations

import logging
from typing import Any

from app.config import WECOM_ENABLED


class WeComIntegration:
    def __init__(self, enabled: bool = WECOM_ENABLED) -> None:
        self.enabled = enabled
        self.logger = logging.getLogger("ybkj_workflow.wecom")

    def is_enabled(self) -> bool:
        return self.enabled

    def sync_records(self, payload: dict[str, Any]) -> bool:
        self.logger.info("WeCom sync requested, enabled=%s", self.enabled)
        if not self.enabled:
            return False
        raise NotImplementedError("WeCom integration is reserved and disabled by default.")

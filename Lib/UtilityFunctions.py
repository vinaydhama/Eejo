
# UtilityFunctions.py
from datetime import datetime, timezone
from typing import Literal, Optional


class UtilityFunctions:
    @staticmethod
    def logScreenMsg(
        msg: str,
        *,
        tz: Literal["local", "utc"] = "local",
        prefix: Optional[str] = None
    ) -> None:
        """
        Print a timestamped message.
        - tz: 'local' or 'utc'
        - prefix: optional text like 'INFO', 'WARN', 'ERROR'
        """
        now = datetime.now(timezone.utc) if tz == "utc" else datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S') + f".{now.microsecond // 1000:03d}"
        head = f"[{timestamp}]"
        if prefix:
            head += f" [{prefix}]"
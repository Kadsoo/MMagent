from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo


class TimeService:
    def __init__(self) -> None:
        self.city_to_timezone = {
            "nanjing": "Asia/Shanghai",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "shenzhen": "Asia/Shanghai",
            "hangzhou": "Asia/Shanghai",
            "guangzhou": "Asia/Shanghai",
            "chengdu": "Asia/Shanghai",
            "tokyo": "Asia/Tokyo",
            "seoul": "Asia/Seoul",
            "singapore": "Asia/Singapore",
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "london": "Europe/London",
            "paris": "Europe/Paris",
        }

    def get_time(self, city: str | None = None, timezone_name: str | None = None) -> dict[str, str]:
        target = timezone_name or self.city_to_timezone.get((city or "").strip().lower(), "UTC")
        resolved_name, zone = self._resolve_timezone(target)
        now = datetime.now(zone)
        return {
            "city_or_timezone": city or resolved_name,
            "timezone": resolved_name,
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "iso": now.isoformat(),
            "source": "python-zoneinfo",
        }

    @staticmethod
    def _resolve_timezone(target: str) -> tuple[str, tzinfo]:
        try:
            return target, ZoneInfo(target)
        except Exception:
            fixed_offsets = {
                "UTC": timezone.utc,
                "Asia/Shanghai": timezone(timedelta(hours=8), name="Asia/Shanghai"),
                "Asia/Tokyo": timezone(timedelta(hours=9), name="Asia/Tokyo"),
                "America/New_York": timezone(timedelta(hours=-4), name="America/New_York"),
                "Europe/London": timezone(timedelta(hours=1), name="Europe/London"),
            }
            if target in fixed_offsets:
                return target, fixed_offsets[target]
            return "UTC", timezone.utc

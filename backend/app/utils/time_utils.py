"""
Time conversion utilities for ReSchedule.

Factory shift timeline:
Day starts at 06:00 (Hour 6.0 = Minute 0 from shift start).
Working shift runs 06:00 to 22:00 (16 hours = 960 minutes per day).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Tuple

SHIFT_START_HOUR = 6  # 06:00 AM
MINS_PER_HOUR = 60


def parse_time_to_shift_minutes(time_val: str | None, default_hour: float = 10.0) -> int:
    """
    Convert a time string, datetime string, or hour float into minutes from shift start (06:00).
    Examples:
      - "10:00" -> (10 - 6) * 60 = 240 minutes
      - "13:00" -> (13 - 6) * 60 = 420 minutes
      - "2026-11-07T10:00" -> 240 minutes
      - None / "Just now" -> (default_hour - 6) * 60 = 240 minutes
    """
    if not time_val or str(time_val).strip() in ("Just now", "now"):
        return max(0, int((default_hour - SHIFT_START_HOUR) * MINS_PER_HOUR))

    time_str = str(time_val).strip()

    # Case 1: Simple HH:MM or HH:MM:SS (also handles datetime strings with T)
    m_simple = re.search(r"(\d{1,2}):(\d{2})", time_str)
    if m_simple:
        h = int(m_simple.group(1))
        m = int(m_simple.group(2))
        hour_val = h + m / 60.0
        if hour_val >= SHIFT_START_HOUR:
            return max(0, int((hour_val - SHIFT_START_HOUR) * MINS_PER_HOUR))
        else:
            return max(0, int(hour_val * MINS_PER_HOUR))

    # Case 2: ISO datetime
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        hour_val = dt.hour + dt.minute / 60.0
        return max(0, int((hour_val - SHIFT_START_HOUR) * MINS_PER_HOUR))
    except Exception:
        pass

    # Fallback: float
    try:
        f_val = float(time_str)
        if f_val >= SHIFT_START_HOUR:
            return max(0, int((f_val - SHIFT_START_HOUR) * MINS_PER_HOUR))
        return max(0, int(f_val * MINS_PER_HOUR))
    except Exception:
        return max(0, int((default_hour - SHIFT_START_HOUR) * MINS_PER_HOUR))


def get_breakdown_interval_minutes(start_val: str | None, duration_hours: float | None) -> Tuple[int, int]:
    """Return (start_min, end_min) relative to shift start."""
    s_min = parse_time_to_shift_minutes(start_val, default_hour=10.0)
    dur_h = float(duration_hours or 3.0)
    if dur_h <= 0:
        dur_h = 3.0
    dur_min = int(dur_h * MINS_PER_HOUR)
    return s_min, s_min + dur_min


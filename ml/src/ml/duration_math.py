"""Apply validated ISO-8601 date durations returned by Bedrock."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo

from ml.errors import MLError, MLErrorCode


@dataclass(frozen=True)
class DurationValue:
    amount: int
    unit: str
    iso_duration: str


def parse_iso_date_duration(value: str) -> DurationValue:
    match = re.fullmatch(r"P([1-9]\d*)([DWM])", value.strip().upper())
    if not match:
        raise MLError(
            MLErrorCode.AMBIGUOUS_DATE,
            "Bedrock returned an invalid ISO-8601 date duration.",
            {"duration": value},
        )

    amount = int(match.group(1))
    designator = match.group(2)
    unit = {
        "D": "days",
        "W": "weeks",
        "M": "months",
    }[designator]
    return DurationValue(amount=amount, unit=unit, iso_duration=f"P{amount}{designator}")


def expiration_date_from_duration(
    duration: str,
    *,
    captured_at: str | None,
    timezone: str,
) -> str:
    base = _base_datetime(captured_at, timezone)
    value = parse_iso_date_duration(duration)
    return _apply_duration(base, value).date().isoformat()


def _base_datetime(captured_at: str | None, timezone: str) -> datetime:
    if captured_at:
        value = datetime.fromisoformat(captured_at)
        if value.tzinfo is None:
            value = value.replace(tzinfo=ZoneInfo(timezone))
        return value.astimezone(ZoneInfo(timezone))
    return datetime.now(ZoneInfo(timezone))


def _apply_duration(base: datetime, duration: DurationValue) -> datetime:
    if duration.unit == "days":
        return base + timedelta(days=duration.amount)
    if duration.unit == "weeks":
        return base + timedelta(days=duration.amount * 7)
    if duration.unit == "months":
        return _add_months(base, duration.amount)
    raise MLError(
        MLErrorCode.AMBIGUOUS_DATE,
        "Unsupported duration unit.",
        {"unit": duration.unit},
    )


def _add_months(base: datetime, months: int) -> datetime:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base.day, monthrange(year, month)[1])
    return base.replace(year=year, month=month, day=day)


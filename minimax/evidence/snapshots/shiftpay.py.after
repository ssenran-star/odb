"""班次工资。

正班、工作日加班、周末加班和节日加班均按 docs/spec.md 实现。
"""

from __future__ import annotations


HOLIDAY_MULTIPLIER = 3.0


def regular_pay(hourly_rate: float, regular_hours: float) -> float:
    _validate(hourly_rate, regular_hours)
    return round(hourly_rate * regular_hours, 2)


def overtime_pay(hourly_rate: float, overtime_hours: float, day_type: str) -> float:
    _validate(hourly_rate, overtime_hours)
    if day_type == "weekday":
        return round(hourly_rate * 1.5 * overtime_hours, 2)
    if day_type == "weekend":
        return round(hourly_rate * 2.0 * overtime_hours, 2)
    if day_type == "holiday":
        return round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)
    raise ValueError(f"unknown day_type: {day_type}")


def _validate(hourly_rate: float, hours: float) -> None:
    if hourly_rate < 0 or hours < 0:
        raise ValueError("rates and hours must be non-negative")

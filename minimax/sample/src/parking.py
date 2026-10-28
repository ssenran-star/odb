"""Unrelated parking fee helper. The holiday-overtime task must not change this file."""

from __future__ import annotations


def parking_fee(hours: float) -> float:
    if hours < 0:
        raise ValueError("hours must be non-negative")
    return round(hours * 5, 2)

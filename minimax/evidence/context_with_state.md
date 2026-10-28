# 开发上下文

以下规格、代码和测试正文来自 seekdb 查询结果，不是写死的答案。
collection: sdd_materials

## 任务说明（本次请求）
任务：实现节日加班工资。
规格要求 day_type 为 holiday 时，overtime_pay 按规格原文中的 HOLIDAY_MULTIPLIER 计算。
请修改符号 overtime_pay，文件是 src/shiftpay.py。
功能测试：test_holiday_overtime_uses_spec_multiplier。
回归测试必须保持通过，文件 tests/test_regression_pay.py。

## 任务状态（PowerContext）
status: ready
action: continue_edit
<!-- begin powercontext -->
SDD_TASK=holiday-overtime
saved_at=2026-10-28T01:49:56Z
nonce=3f66a2b0c2c44115a077370df0f925a2
feature_exit=1
regression_exit=0
spec_sha256=a8cb38b68c70162b734c291e4e3f351701f3b124641faaca5c374ac27cd2b45b
code_sha256=0538a1117194d2b4ebc2aa2fb02184f0f8a8e02aefaa825dc7cb129d1f424411
verification=dry_run
next_action=继续修改 overtime_pay；配置 MINIMAX_API_KEY 后执行 scripts/run_minimax_edit.py
<!-- end powercontext -->

## 需要修改的符号
- src/shiftpay.py :: overtime_pay

## 相关测试
- tests/test_regression_pay.py :: test_regular_pay (role=regression)
- tests/test_feature_holiday.py :: test_holiday_overtime_uses_spec_multiplier (role=feature)
- tests/test_unrelated_parking.py :: test_parking_fee (role=decoy)

## 选中的spec
<!-- begin spec docs/spec.md 测试要求 id=8b80cf04e373d9cb2469 -->
path: docs/spec.md
symbol: 测试要求
kind: spec
role: spec

## 测试要求

功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。
回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。
需要修改的符号是 `overtime_pay`。
<!-- end spec -->

<!-- begin spec docs/spec.md 节日加班 id=68d3884b2d8e73ac0767 -->
path: docs/spec.md
symbol: 节日加班
kind: spec
role: spec

## 节日加班

当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：

    HOLIDAY_MULTIPLIER = 3.0

加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。
示例：hourly_rate=100 且 overtime_hours=2 时结果为 600；hourly_rate=40 且 overtime_hours=1.5 时结果为 180。
未知 `day_type` 必须抛出 `ValueError`。
<!-- end spec -->

<!-- begin spec docs/spec.md 概述 id=de58a4b41848f3dccf12 -->
path: docs/spec.md
symbol: 概述
kind: spec
role: spec

# 班次工资规格

本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。
节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。
<!-- end spec -->

<!-- begin spec docs/spec.md 工作日加班 id=33b8a250c13529bf1a5e -->
path: docs/spec.md
symbol: 工作日加班
kind: spec
role: spec

## 工作日加班

`day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。
<!-- end spec -->


## 选中的code
<!-- begin code src/shiftpay.py overtime_pay id=3b5a7c275d67fcce35fa -->
path: src/shiftpay.py
symbol: overtime_pay
kind: code
role: implementation

"""班次工资。

正班、工作日加班和周末加班已按 docs/spec.md 实现。
day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。
"""

from __future__ import annotations


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
        return 0.0
    raise ValueError(f"unknown day_type: {day_type}")


def _validate(hourly_rate: float, hours: float) -> None:
    if hourly_rate < 0 or hours < 0:
        raise ValueError("rates and hours must be non-negative")
<!-- end code -->

<!-- begin code src/parking.py parking_fee id=a5642586f4972213daa2 -->
path: src/parking.py
symbol: parking_fee
kind: code
role: decoy

"""Unrelated parking fee helper. The holiday-overtime task must not change this file."""

from __future__ import annotations


def parking_fee(hours: float) -> float:
    if hours < 0:
        raise ValueError("hours must be non-negative")
    return round(hours * 5, 2)
<!-- end code -->


## 选中的test
<!-- begin test tests/test_regression_pay.py test_regular_pay id=12c9a4fa4d6eb401e3b1 -->
path: tests/test_regression_pay.py
symbol: test_regular_pay
kind: test
role: regression

import pytest

from shiftpay import overtime_pay, regular_pay


def test_regular_pay():
    """回归测试：正班工资保持不变。"""
    assert regular_pay(50, 8) == 400.0


def test_weekday_overtime():
    assert overtime_pay(100, 2, "weekday") == 300.0


def test_weekend_overtime():
    assert overtime_pay(100, 2, "weekend") == 400.0


def test_negative_hours_rejected():
    with pytest.raises(ValueError):
        regular_pay(10, -1)


def test_unknown_day_type_rejected():
    with pytest.raises(ValueError):
        overtime_pay(10, 1, "night")
<!-- end test -->

<!-- begin test tests/test_feature_holiday.py test_holiday_overtime_uses_spec_multiplier id=76651fd0ecbd92a3917a -->
path: tests/test_feature_holiday.py
symbol: test_holiday_overtime_uses_spec_multiplier
kind: test
role: feature

from shiftpay import overtime_pay


def test_holiday_overtime_uses_spec_multiplier():
    """Fails until holiday pay uses the multiplier in docs/spec.md."""
    assert overtime_pay(100, 2, "holiday") == 600.0


def test_holiday_overtime_partial_hour():
    assert overtime_pay(40, 1.5, "holiday") == 180.0
<!-- end test -->

<!-- begin test tests/test_unrelated_parking.py test_parking_fee id=5296620d454c82895fbd -->
path: tests/test_unrelated_parking.py
symbol: test_parking_fee
kind: test
role: decoy

from parking import parking_fee


def test_parking_fee():
    assert parking_fee(2) == 10.0
<!-- end test -->

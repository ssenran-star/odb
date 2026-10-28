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

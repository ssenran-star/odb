from shiftpay import overtime_pay


def test_holiday_overtime_uses_spec_multiplier():
    """Fails until holiday pay uses the multiplier in docs/spec.md."""
    assert overtime_pay(100, 2, "holiday") == 600.0


def test_holiday_overtime_partial_hour():
    assert overtime_pay(40, 1.5, "holiday") == 180.0

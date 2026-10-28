# 班次工资规格

本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。
节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。

## 正班

`regular_pay(hourly_rate, regular_hours) = round(hourly_rate * regular_hours, 2)`。
时薪或工时为负时抛出 `ValueError`。

## 工作日加班

`day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。

## 周末加班

`day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。

## 节日加班

当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：

    HOLIDAY_MULTIPLIER = 3.0

加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。
示例：hourly_rate=100 且 overtime_hours=2 时结果为 600；hourly_rate=40 且 overtime_hours=1.5 时结果为 180。
未知 `day_type` 必须抛出 `ValueError`。

## 测试要求

功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。
回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。
需要修改的符号是 `overtime_pay`。

# seekdb 查询记录

这些条目复制自同一次运行写入的 `evidence/seekdb_queries.jsonl`。
上下文模块只把这里返回的 document 放进开发上下文。

## 1. query

- ts: `2026-10-28T01:49:35.931987+00:00`
- detail: `{"route": "import_readback", "n_results": 8}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 2. get

- ts: `2026-10-28T01:49:35.933678+00:00`
- detail: `{"where": {"kind": "spec"}}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '68d3884b2d8e73ac0767', '8b80cf04e373d9cb2469']`
- hit `8667006d90bc0c7e5db5` path=`docs/parking.md` symbol=`概述`: path: docs/parking.md symbol: 概述 kind: spec role: decoy  # 停车说明 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `48ef3c86999a040f4e9e` path=`docs/spec.md` symbol=`正班`: path: docs/spec.md symbol: 正班 kind: spec role: spec  ## 正班  `regular_pay(hourly_rate, regular_hours) = round(hourly_rate * regular_hours, 2)`。 时薪或工时为负时抛出 `ValueError`。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 

## 3. import

- ts: `2026-10-28T01:49:35.934393+00:00`
- detail: `{"collection": "sdd_materials", "count": 13, "upserted": 13, "seekdb_path": "/workspace/minimax/data/seekdb"}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '68d3884b2d8e73ac0767', '8b80cf04e373d9cb2469', 'a5642586f4972213daa2', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`

## 4. query

- ts: `2026-10-28T01:49:38.755195+00:00`
- detail: `{"route": "vector_all"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 5. query

- ts: `2026-10-28T01:49:38.757095+00:00`
- detail: `{"route": "vector_spec", "where": {"kind": "spec"}}`
- ids: `['8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', 'e801622bfb95284626d0', '48ef3c86999a040f4e9e', '8667006d90bc0c7e5db5']`
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 

## 6. query

- ts: `2026-10-28T01:49:38.758655+00:00`
- detail: `{"route": "vector_code", "where": {"kind": "code"}}`
- ids: `['3b5a7c275d67fcce35fa', 'a5642586f4972213daa2']`
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `a5642586f4972213daa2` path=`src/parking.py` symbol=`parking_fee`: path: src/parking.py symbol: parking_fee kind: code role: decoy  """Unrelated parking fee helper. The holiday-overtime task must not change this file."""  from __future__ import annotations   def parking_fee(hours: float) -> float:     if h

## 7. query

- ts: `2026-10-28T01:49:38.760165+00:00`
- detail: `{"route": "vector_test", "where": {"kind": "test"}}`
- ids: `['76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `5296620d454c82895fbd` path=`tests/test_unrelated_parking.py` symbol=`test_parking_fee`: path: tests/test_unrelated_parking.py symbol: test_parking_fee kind: test role: decoy  from parking import parking_fee   def test_parking_fee():     assert parking_fee(2) == 10.0 

## 8. hybrid_search

- ts: `2026-10-28T01:49:39.650722+00:00`
- detail: `{"contains": "节日加班", "rank": "rrf"}`
- ids: `['de58a4b41848f3dccf12', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1']`
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m

## 9. hybrid_search

- ts: `2026-10-28T01:49:39.652283+00:00`
- detail: `{"contains": "overtime_pay", "rank": "rrf"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', 'de58a4b41848f3dccf12', '3b5a7c275d67fcce35fa', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim

## 10. hybrid_search

- ts: `2026-10-28T01:49:39.654046+00:00`
- detail: `{"contains": "HOLIDAY_MULTIPLIER", "rank": "rrf"}`
- ids: `['68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 11. query

- ts: `2026-10-28T01:49:43.929068+00:00`
- detail: `{"route": "import_readback", "n_results": 8}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_ra
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 12. get

- ts: `2026-10-28T01:49:43.930652+00:00`
- detail: `{"where": {"kind": "spec"}}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767']`
- hit `8667006d90bc0c7e5db5` path=`docs/parking.md` symbol=`概述`: path: docs/parking.md symbol: 概述 kind: spec role: decoy  # 停车说明 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `48ef3c86999a040f4e9e` path=`docs/spec.md` symbol=`正班`: path: docs/spec.md symbol: 正班 kind: spec role: spec  ## 正班  `regular_pay(hourly_rate, regular_hours) = round(hourly_rate * regular_hours, 2)`。 时薪或工时为负时抛出 `ValueError`。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 

## 13. import

- ts: `2026-10-28T01:49:43.931100+00:00`
- detail: `{"collection": "sdd_materials", "count": 13, "upserted": 13, "seekdb_path": "/workspace/minimax/data/seekdb"}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '68d3884b2d8e73ac0767', '8b80cf04e373d9cb2469', 'a5642586f4972213daa2', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`

## 14. query

- ts: `2026-10-28T01:49:46.758248+00:00`
- detail: `{"route": "vector_all"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_ra
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 15. query

- ts: `2026-10-28T01:49:46.759819+00:00`
- detail: `{"route": "vector_spec", "where": {"kind": "spec"}}`
- ids: `['8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', 'e801622bfb95284626d0', '48ef3c86999a040f4e9e', '8667006d90bc0c7e5db5']`
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_ra
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 

## 16. query

- ts: `2026-10-28T01:49:46.761757+00:00`
- detail: `{"route": "vector_code", "where": {"kind": "code"}}`
- ids: `['3b5a7c275d67fcce35fa', 'a5642586f4972213daa2']`
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `a5642586f4972213daa2` path=`src/parking.py` symbol=`parking_fee`: path: src/parking.py symbol: parking_fee kind: code role: decoy  """Unrelated parking fee helper. The holiday-overtime task must not change this file."""  from __future__ import annotations   def parking_fee(hours: float) -> float:     if h

## 17. query

- ts: `2026-10-28T01:49:46.763410+00:00`
- detail: `{"route": "vector_test", "where": {"kind": "test"}}`
- ids: `['76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `5296620d454c82895fbd` path=`tests/test_unrelated_parking.py` symbol=`test_parking_fee`: path: tests/test_unrelated_parking.py symbol: test_parking_fee kind: test role: decoy  from parking import parking_fee   def test_parking_fee():     assert parking_fee(2) == 10.0 

## 18. hybrid_search

- ts: `2026-10-28T01:49:47.671525+00:00`
- detail: `{"contains": "节日加班", "rank": "rrf"}`
- ids: `['de58a4b41848f3dccf12', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1']`
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_ra
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m

## 19. hybrid_search

- ts: `2026-10-28T01:49:47.673795+00:00`
- detail: `{"contains": "overtime_pay", "rank": "rrf"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', 'de58a4b41848f3dccf12', '3b5a7c275d67fcce35fa', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_ra

## 20. hybrid_search

- ts: `2026-10-28T01:49:47.675141+00:00`
- detail: `{"contains": "HOLIDAY_MULTIPLIER", "rank": "rrf"}`
- ids: `['68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_ra
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 21. query

- ts: `2026-10-28T01:49:51.768775+00:00`
- detail: `{"route": "import_readback", "n_results": 8}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 22. get

- ts: `2026-10-28T01:49:51.770719+00:00`
- detail: `{"where": {"kind": "spec"}}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767']`
- hit `8667006d90bc0c7e5db5` path=`docs/parking.md` symbol=`概述`: path: docs/parking.md symbol: 概述 kind: spec role: decoy  # 停车说明 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `48ef3c86999a040f4e9e` path=`docs/spec.md` symbol=`正班`: path: docs/spec.md symbol: 正班 kind: spec role: spec  ## 正班  `regular_pay(hourly_rate, regular_hours) = round(hourly_rate * regular_hours, 2)`。 时薪或工时为负时抛出 `ValueError`。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 

## 23. import

- ts: `2026-10-28T01:49:51.771173+00:00`
- detail: `{"collection": "sdd_materials", "count": 13, "upserted": 13, "seekdb_path": "/workspace/minimax/data/seekdb"}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '68d3884b2d8e73ac0767', '8b80cf04e373d9cb2469', 'a5642586f4972213daa2', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`

## 24. query

- ts: `2026-10-28T01:49:56.467518+00:00`
- detail: `{"route": "import_readback", "n_results": 8}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 25. get

- ts: `2026-10-28T01:49:56.469199+00:00`
- detail: `{"where": {"kind": "spec"}}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767']`
- hit `8667006d90bc0c7e5db5` path=`docs/parking.md` symbol=`概述`: path: docs/parking.md symbol: 概述 kind: spec role: decoy  # 停车说明 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `48ef3c86999a040f4e9e` path=`docs/spec.md` symbol=`正班`: path: docs/spec.md symbol: 正班 kind: spec role: spec  ## 正班  `regular_pay(hourly_rate, regular_hours) = round(hourly_rate * regular_hours, 2)`。 时薪或工时为负时抛出 `ValueError`。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 

## 26. import

- ts: `2026-10-28T01:49:56.469906+00:00`
- detail: `{"collection": "sdd_materials", "count": 13, "upserted": 13, "seekdb_path": "/workspace/minimax/data/seekdb"}`
- ids: `['8667006d90bc0c7e5db5', 'e801622bfb95284626d0', 'de58a4b41848f3dccf12', '48ef3c86999a040f4e9e', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '68d3884b2d8e73ac0767', '8b80cf04e373d9cb2469', 'a5642586f4972213daa2', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`

## 27. query

- ts: `2026-10-28T01:49:56.475402+00:00`
- detail: `{"route": "vector_all"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 28. query

- ts: `2026-10-28T01:49:56.476979+00:00`
- detail: `{"route": "vector_spec", "where": {"kind": "spec"}}`
- ids: `['8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', 'e801622bfb95284626d0', '48ef3c86999a040f4e9e', '8667006d90bc0c7e5db5']`
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 

## 29. query

- ts: `2026-10-28T01:49:56.478489+00:00`
- detail: `{"route": "vector_code", "where": {"kind": "code"}}`
- ids: `['3b5a7c275d67fcce35fa', 'a5642586f4972213daa2']`
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `a5642586f4972213daa2` path=`src/parking.py` symbol=`parking_fee`: path: src/parking.py symbol: parking_fee kind: code role: decoy  """Unrelated parking fee helper. The holiday-overtime task must not change this file."""  from __future__ import annotations   def parking_fee(hours: float) -> float:     if h

## 30. query

- ts: `2026-10-28T01:49:56.479921+00:00`
- detail: `{"route": "vector_test", "where": {"kind": "test"}}`
- ids: `['76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `5296620d454c82895fbd` path=`tests/test_unrelated_parking.py` symbol=`test_parking_fee`: path: tests/test_unrelated_parking.py symbol: test_parking_fee kind: test role: decoy  from parking import parking_fee   def test_parking_fee():     assert parking_fee(2) == 10.0 

## 31. hybrid_search

- ts: `2026-10-28T01:49:56.556732+00:00`
- detail: `{"contains": "节日加班", "rank": "rrf"}`
- ids: `['de58a4b41848f3dccf12', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1']`
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m

## 32. hybrid_search

- ts: `2026-10-28T01:49:56.558937+00:00`
- detail: `{"contains": "overtime_pay", "rank": "rrf"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', 'de58a4b41848f3dccf12', '3b5a7c275d67fcce35fa', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim

## 33. hybrid_search

- ts: `2026-10-28T01:49:56.560629+00:00`
- detail: `{"contains": "HOLIDAY_MULTIPLIER", "rank": "rrf"}`
- ids: `['68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 34. query

- ts: `2026-10-28T01:50:00.110260+00:00`
- detail: `{"route": "vector_all"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 

## 35. query

- ts: `2026-10-28T01:50:00.111887+00:00`
- detail: `{"route": "vector_spec", "where": {"kind": "spec"}}`
- ids: `['8b80cf04e373d9cb2469', '68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', 'e801622bfb95284626d0', '48ef3c86999a040f4e9e', '8667006d90bc0c7e5db5']`
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `e801622bfb95284626d0` path=`docs/parking.md` symbol=`停车`: path: docs/parking.md symbol: 停车 kind: spec role: decoy  ## 停车  PARKING-FEE-UNRELATED hourly parking fee is 5 yuan and is not part of payroll. 

## 36. query

- ts: `2026-10-28T01:50:00.113538+00:00`
- detail: `{"route": "vector_code", "where": {"kind": "code"}}`
- ids: `['3b5a7c275d67fcce35fa', 'a5642586f4972213daa2']`
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `a5642586f4972213daa2` path=`src/parking.py` symbol=`parking_fee`: path: src/parking.py symbol: parking_fee kind: code role: decoy  """Unrelated parking fee helper. The holiday-overtime task must not change this file."""  from __future__ import annotations   def parking_fee(hours: float) -> float:     if h

## 37. query

- ts: `2026-10-28T01:50:00.114846+00:00`
- detail: `{"route": "vector_test", "where": {"kind": "test"}}`
- ids: `['76651fd0ecbd92a3917a', '12c9a4fa4d6eb401e3b1', '5296620d454c82895fbd']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `5296620d454c82895fbd` path=`tests/test_unrelated_parking.py` symbol=`test_parking_fee`: path: tests/test_unrelated_parking.py symbol: test_parking_fee kind: test role: decoy  from parking import parking_fee   def test_parking_fee():     assert parking_fee(2) == 10.0 

## 38. hybrid_search

- ts: `2026-10-28T01:50:01.028384+00:00`
- detail: `{"contains": "节日加班", "rank": "rrf"}`
- ids: `['de58a4b41848f3dccf12', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8', '3b5a7c275d67fcce35fa', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1']`
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。 
- hit `f0b70d1b2b33c8192ad8` path=`docs/spec.md` symbol=`周末加班`: path: docs/spec.md symbol: 周末加班 kind: spec role: spec  ## 周末加班  `day_type == "weekend"` 时，加班工资 = `round(hourly_rate * 2.0 * overtime_hours, 2)`。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m

## 39. hybrid_search

- ts: `2026-10-28T01:50:01.030628+00:00`
- detail: `{"contains": "overtime_pay", "rank": "rrf"}`
- ids: `['76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', 'de58a4b41848f3dccf12', '3b5a7c275d67fcce35fa', '68d3884b2d8e73ac0767', '33b8a250c13529bf1a5e', 'f0b70d1b2b33c8192ad8']`
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `3b5a7c275d67fcce35fa` path=`src/shiftpay.py` symbol=`overtime_pay`: path: src/shiftpay.py symbol: overtime_pay kind: code role: implementation  """班次工资。  正班、工作日加班和周末加班已按 docs/spec.md 实现。 day_type 为 holiday 时的倍数尚未实现，当前固定返回 0。 """  from __future__ import annotations   def regular_pay(hourly_rate: float, regul
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim

## 40. hybrid_search

- ts: `2026-10-28T01:50:01.031953+00:00`
- detail: `{"contains": "HOLIDAY_MULTIPLIER", "rank": "rrf"}`
- ids: `['68d3884b2d8e73ac0767', 'de58a4b41848f3dccf12', '76651fd0ecbd92a3917a', '8b80cf04e373d9cb2469', '12c9a4fa4d6eb401e3b1', '33b8a250c13529bf1a5e', '3b5a7c275d67fcce35fa', 'f0b70d1b2b33c8192ad8']`
- hit `68d3884b2d8e73ac0767` path=`docs/spec.md` symbol=`节日加班`: path: docs/spec.md symbol: 节日加班 kind: spec role: spec  ## 节日加班  当 `day_type == "holiday"` 时，倍数取下面这一行，不要改用别的数字：      HOLIDAY_MULTIPLIER = 3.0  加班工资 = `round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)`。 示例：hourly_rate=100 且 overtim
- hit `de58a4b41848f3dccf12` path=`docs/spec.md` symbol=`概述`: path: docs/spec.md symbol: 概述 kind: spec role: spec  # 班次工资规格  本规格定义 `src/shiftpay.py` 中的 `regular_pay` 与 `overtime_pay`。 节日加班以「节日加班」一节的 `HOLIDAY_MULTIPLIER` 这一行为准。 
- hit `76651fd0ecbd92a3917a` path=`tests/test_feature_holiday.py` symbol=`test_holiday_overtime_uses_spec_multiplier`: path: tests/test_feature_holiday.py symbol: test_holiday_overtime_uses_spec_multiplier kind: test role: feature  from shiftpay import overtime_pay   def test_holiday_overtime_uses_spec_multiplier():     """Fails until holiday pay uses the m
- hit `8b80cf04e373d9cb2469` path=`docs/spec.md` symbol=`测试要求`: path: docs/spec.md symbol: 测试要求 kind: spec role: spec  ## 测试要求  功能测试是 `tests/test_feature_holiday.py` 里的 `test_holiday_overtime_uses_spec_multiplier`。 回归测试是 `tests/test_regression_pay.py`，修改后必须保持通过。 需要修改的符号是 `overtime_pay`。 
- hit `12c9a4fa4d6eb401e3b1` path=`tests/test_regression_pay.py` symbol=`test_regular_pay`: path: tests/test_regression_pay.py symbol: test_regular_pay kind: test role: regression  import pytest  from shiftpay import overtime_pay, regular_pay   def test_regular_pay():     """回归测试：正班工资保持不变。"""     assert regular_pay(50, 8) == 400.0
- hit `33b8a250c13529bf1a5e` path=`docs/spec.md` symbol=`工作日加班`: path: docs/spec.md symbol: 工作日加班 kind: spec role: spec  ## 工作日加班  `day_type == "weekday"` 时，加班工资 = `round(hourly_rate * 1.5 * overtime_hours, 2)`。

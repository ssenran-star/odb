# 验证说明

## 任务

样例项目 `sample/` 是班次工资计算器。规格 `sample/docs/spec.md` 规定 `day_type == "holiday"` 时：

```text
HOLIDAY_MULTIPLIER = 3.0
加班工资 = round(hourly_rate * HOLIDAY_MULTIPLIER * overtime_hours, 2)
```

因此 `overtime_pay(100, 2, "holiday") == 600`，`overtime_pay(40, 1.5, "holiday") == 180`。

`sample/src/shiftpay.py` 里 holiday 分支固定返回 `0.0`，所以功能测试在修改前失败。正班、工作日 1.5 倍、周末 2.0 倍、负数和未知 `day_type` 已实现，回归测试应通过。`docs/parking.md` 与工资无关，不应进入开发上下文。

任务原文是 `sample/TASK.md`。

## 有效规格与初始数据

- 规格：`sample/docs/spec.md`（另有无关文档 `sample/docs/parking.md`）
- 初始代码：`sample/src/shiftpay.py`（holiday 未实现）、`sample/src/parking.py`
- 功能测试：`sample/tests/test_feature_holiday.py`
- 回归测试：`sample/tests/test_regression_pay.py`
- 初始数据：seekdb 与 PowerContext 都从空目录开始。`python -m sddctx reset` 会删除 `data/seekdb`、`data/powercontext` 和 `data/scope.json`。

## 步骤 A：离线检查（数据库、上下文新鲜度、PowerContext、修改前测试）

在没有 `MINIMAX_API_KEY` 的机器上执行。这一步不调用 MiniMax，也不会写模型回复。

```bash
cd minimax
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv tool install --force 'powercontext[cli,server]==1.4.0'
export PATH="$HOME/.local/bin:$PATH"
.venv/bin/python -m pytest -q tests
.venv/bin/python -m sddctx verify
```

`verify` 会：

1. 重置并启动本机 PowerContext（`http://127.0.0.1:8765`）。
2. 新进程 `resume`：search/prepare 为空（退出码 2）。
3. 把样例导入 seekdb，`select` 出的规格含 `HOLIDAY_MULTIPLIER = 3.0`，含 `overtime_pay` 和功能测试名，不含 `PARKING-FEE-UNRELATED`。
4. 把规格行改成 `HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719`，重新 import 后再 select。新上下文必须出现该修订，且不再保留旧的 `HOLIDAY_MULTIPLIER = 3.0` 行。
5. 把规格改回基线并再次 import。
6. 功能测试退出码 1（断言 `0.0 == 600.0`），回归测试退出码 0。
7. `scripts/run_minimax_edit.py --dry-run` 写出将要发送的 prompt/请求体，且不改源码。
8. `state-save` 写入带随机 nonce 的进度；另一个 Python 进程 `resume` 必须打印同一个 nonce，并因为 `verification=dry_run` 且 `feature_exit=1` 决定 `continue_edit`。再 `select` 一次，上下文正文里要带上这条 PowerContext 状态。

期望产物：

| 文件 | 期望 |
|---|---|
| `evidence/summary.json` | `minimax_called` 为 false，`context_fresh` / `powercontext_reused` 为 true |
| `evidence/context_v1.md` 与 `evidence/context_v2.md` | 同一条规格，正文分别是 3.0 和 3.5 |
| `evidence/seekdb_queries.jsonl` | 含 `query`、`get`、`hybrid_search`，以及两个版本的规格片段 |
| `evidence/tests/feature_before.log` | `exit_code: 1`，断言失败 |
| `evidence/tests/regression_before.log` | `exit_code: 0` |
| `evidence/minimax_request.json` | 完整消息，无 API key |
| `evidence/powercontext_empty.json` | `hits` 为空，prepare `status=empty` |
| `evidence/powercontext_reuse.json` | 读回刚才写入的 artifact |
| `evidence/TODO_MINIMAX.md` | 标明实时调用还没做 |
| `records/seekdb_queries.md`、`records/powercontext.md` | 由上面的原始响应生成 |
| `records/minimax_development.md` | 明确写着实时调用未执行，不是模型转写 |

步骤 A 结束时 `sample/src/shiftpay.py` 和 `sample/docs/spec.md` 应与仓库基线一致。

只看将要发送的 prompt 时：

```bash
cd minimax
.venv/bin/python -m sddctx reset
.venv/bin/python scripts/run_minimax_edit.py --dry-run
```

## 步骤 B：有 MINIMAX_API_KEY 时做真实修改

不要手写模型回复。在能读到密钥的机器上：

```bash
cd minimax
export PATH="$HOME/.local/bin:$PATH"
export MINIMAX_API_KEY='your-key'
# 中国区密钥：
# export MINIMAX_BASE_URL=https://api.minimaxi.com/v1
# 账号不能调用 MiniMax-M3 时再改模型，例如：
# export MINIMAX_MODEL=MiniMax-M2.7

# 若工作区里的样例已经被改过，先回到会失败的基线：
git checkout -- sample/src/shiftpay.py sample/docs/spec.md

.venv/bin/python scripts/run_minimax_edit.py
```

脚本会重新 import、用 seekdb 组装上下文（若 PowerContext 里已有进度，会放进提示词；已通过则不再调用模型）、确认功能测试仍然失败且回归测试通过，然后请求 MiniMax。成功时：

- `sample/src/shiftpay.py` 被模型输出改写
- `evidence/snapshots/shiftpay.py.before`、`shiftpay.py.after`、`shiftpay.diff` 与 diff 一致
- `evidence/tests/feature_before.log` 退出码 1，`feature_after.log` 退出码 0
- `evidence/tests/regression_before.log` 与 `regression_after.log` 退出码都是 0
- `evidence/minimax_response_summary.json` 含 response id 和助手原文（密钥已抹掉）
- `records/minimax_development.md` 同时包含该原文和同一份 diff
- `evidence/TODO_MINIMAX.md` 被删除
- 验证结果写入 PowerContext；再跑 `.venv/bin/python -m sddctx resume --out evidence/powercontext_after_edit.json` 应打印 `action=skip_edit`

模型没有改对时，脚本退出 1，并留下真实的失败日志和响应摘要，而不是一份假装通过的记录。

## 重置

```bash
cd minimax
git checkout -- sample/src/shiftpay.py sample/docs/spec.md
.venv/bin/python -m sddctx reset
```

`reset` 只清运行时数据库，不清 `evidence/`。要重做步骤 A 的证据，直接再跑 `python -m sddctx verify`。

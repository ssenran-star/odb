# 运行说明

规有所依：把样例工程的规格、代码和测试放进 seekdb，按任务选出开发上下文，交给 MiniMax 改代码，再用 PowerContext 记住进度。入口是 Python CLI `sddctx`。

## 依赖

- Python 3.11+
- `uv`（https://docs.astral.sh/uv/）
- 能执行 `patch` 的系统（只在模型返回 unified diff 时用到）
- Linux 上的 embedded seekdb（`pyseekdb` / `pylibseekdb`）

```bash
cd minimax
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv tool install --force 'powercontext[cli,server]==1.4.0'
export PATH="$HOME/.local/bin:$PATH"
cp .env.example .env
```

`.env` 里的 `MINIMAX_API_KEY` 留空即可跑离线检查。不要把真实密钥提交进仓库。

## 配置

| 变量 | 作用 | 默认 |
|---|---|---|
| `MINIMAX_API_KEY` | MiniMax OpenAPI Bearer token | 空 |
| `MINIMAX_BASE_URL` | Chat Completions 根路径 | `https://api.minimax.io/v1` |
| `MINIMAX_MODEL` | 模型名 | `MiniMax-M3` |
| `POWERCONTEXT_URL` | PowerContext HTTP | `http://127.0.0.1:8765` |
| `POWERCONTEXT_TOKEN` | 服务器开启鉴权时的 Bearer | 空 |
| `POWERCONTEXT_SCOPE` | 已有 scope id；空则按 `POWERCONTEXT_SCOPE_KEY` 创建并缓存到 `data/scope.json` | 空 |
| `POWERCONTEXT_HOME` | 服务器数据目录 | `minimax/data/powercontext` |
| `SEEKDB_PATH` | embedded seekdb 数据目录 | `minimax/data/seekdb` |
| `SEEKDB_DATABASE` | 库名 | `test` |
| `SEEKDB_COLLECTION` | collection 名 | `sdd_materials` |

中国区密钥把 `MINIMAX_BASE_URL` 改成 `https://api.minimaxi.com/v1`。密钥若不能调用 `MiniMax-M3`，把 `MINIMAX_MODEL` 改成账号可用的模型（例如 `MiniMax-M2.7`）。

## 数据初始化与入口

本地 PowerContext 不需要生成模型。显式 `remember` / `search` / `prepare` 使用 SQLite。`reset` 会删掉 `data/seekdb`、`data/powercontext` 和 scope 缓存，然后重新拉起服务器。

```bash
cd minimax
.venv/bin/python -m sddctx reset          # 清空 seekdb + PowerContext 并启动服务
.venv/bin/python -m sddctx import         # 把 sample/{docs,src,tests} 写入 seekdb
.venv/bin/python -m sddctx select --out evidence/context.md
.venv/bin/python -m sddctx test --suite feature
.venv/bin/python -m sddctx test --suite regression
.venv/bin/python scripts/run_minimax_edit.py --dry-run
.venv/bin/python -m sddctx verify         # 步骤 A：离线验收（见 VERIFY.md）
```

`scripts/run_minimax_edit.py` 不加 `--dry-run` 时会读取 `MINIMAX_API_KEY`，把 `evidence/minimax_request.json` 里的同一份消息发给 `POST {MINIMAX_BASE_URL}/chat/completions`，把返回的完整文件或 diff 应用到 `sample/src/shiftpay.py`，再跑功能测试和回归测试。

## 测试命令

```bash
cd minimax
.venv/bin/python -m pytest -q tests
cd sample && ../.venv/bin/python -m pytest -q tests/test_regression_pay.py
cd sample && ../.venv/bin/python -m pytest -q tests/test_feature_holiday.py   # 修改前应失败
```

功能测试失败的原因是 `overtime_pay(..., "holiday")` 仍返回 `0.0`，断言期望规格中的 600 / 180，不是导入错误。

## 已知限制

- 本云端环境转发不了 `MINIMAX_API_KEY`。没有密钥时不要伪造模型回复；看 `evidence/TODO_MINIMAX.md`。
- embedded seekdb 同一数据目录不要并发打开。
- PowerContext 未配置向量模型时，`/v1/memory/search` 是全文检索。模块写入的进度文本带有固定检索词 `SDD_TASK=holiday-overtime`。
- 上下文只从 seekdb 命中的 document 拼出来。改规格后必须再执行 `import`，下一次 `select` / `edit` 才会用到新正文。
- 样例功能测试锁定的是基线倍数 3.0。规格新鲜度检查会临时改成 3.5，检查完会改回，避免和测试数字打架。
- MiniMax 若只返回无法应用的 diff，脚本会把错误记到 `evidence/minimax_apply_error.json` 并退出 1，不会编造通过的测试日志。

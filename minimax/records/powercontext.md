# PowerContext 状态记录

上下文模块进程本身不保存任务进度。下面的空状态、写入和再次读取都来自 PowerContext HTTP API。

## 空状态

```
status=empty
action=empty
```

- prepare status: `empty`
- search hits: `0`

## 写入 /v1/memory/remember

```
SDD_TASK=holiday-overtime
saved_at=2026-10-28T01:49:56Z
nonce=3f66a2b0c2c44115a077370df0f925a2
feature_exit=1
regression_exit=0
spec_sha256=a8cb38b68c70162b734c291e4e3f351701f3b124641faaca5c374ac27cd2b45b
code_sha256=0538a1117194d2b4ebc2aa2fb02184f0f8a8e02aefaa825dc7cb129d1f424411
verification=dry_run
next_action=继续修改 overtime_pay；配置 MINIMAX_API_KEY 后执行 scripts/run_minimax_edit.py
```

- artifact: `[{'artifact': {'family': 'atomic-memory', 'artifact_id': 'art_539cb14f02d749f9a349dd127e7db2f6', 'revision': 1}, 'kind': 'progress', 'text': 'SDD_TASK=holiday-overtime\nsaved_at=2026-10-28T01:49:56Z\nnonce=3f66a2b0c2c44115a077370df0f925a2\nfeature_exit=1\nregression_exit=0\nspec_sha256=a8cb38b68c70162b734c291e4e3f351701f3b124641faaca5c374ac27cd2b45b\ncode_sha256=0538a1117194d2b4ebc2aa2fb02184f0f8a8e02aefaa825dc7cb129d1f424411\nverification=dry_run\nnext_action=继续修改 overtime_pay；配置 MINIMAX_API_KEY 后执行 scripts/run_minimax_edit.py', 'state': 'active', 'state_version': 0, 'merged_into_id': None}]`

## 新进程读取并使用

第二次运行是新的 Python 进程。它只调用 `/v1/memory/search` 和 `/v1/context/prepare`，
再根据返回的 `verification` / `feature_exit` 决定下一步。

```
status=ready
action=continue_edit
artifact_id=art_539cb14f02d749f9a349dd127e7db2f6
nonce=3f66a2b0c2c44115a077370df0f925a2
feature_exit=1
regression_exit=0
spec_sha256=a8cb38b68c70162b734c291e4e3f351701f3b124641faaca5c374ac27cd2b45b
code_sha256=0538a1117194d2b4ebc2aa2fb02184f0f8a8e02aefaa825dc7cb129d1f424411
verification=dry_run
next_action=继续修改 overtime_pay；配置 MINIMAX_API_KEY 后执行 scripts/run_minimax_edit.py
use=continue holiday overtime edit using the stored spec_sha256 and next_action
```

- artifact_id: `art_539cb14f02d749f9a349dd127e7db2f6`
- action: `continue_edit`
- prepare status: `ready`

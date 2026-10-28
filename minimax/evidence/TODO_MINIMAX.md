# TODO: MiniMax live call was not run

Step A dry-run finished. The live MiniMax call still has to be run on a machine with MINIMAX_API_KEY.

This file is a marker, not a model transcript. Do not treat any prompt draft as a MiniMax reply.

## What already exists
- Prompt that would be sent: `evidence/minimax_prompt.md`
- Exact request body (no API key): `evidence/minimax_request.json`
- Context assembled from seekdb: `evidence/minimax_context.md`

## What step B must create
- `evidence/minimax_response_summary.json` (assistant text and usage; secrets redacted)
- `evidence/snapshots/shiftpay.py.after`
- `evidence/snapshots/shiftpay.diff`
- `evidence/tests/feature_after.log`
- `evidence/tests/regression_after.log`
- `records/minimax_development.md` rewritten from the real response and the diff

## Command
```bash
cd minimax
export MINIMAX_API_KEY='your-key'
# export MINIMAX_BASE_URL=https://api.minimaxi.com/v1   # if the key is issued for the China endpoint
# export MINIMAX_MODEL=MiniMax-M2.7                     # if the key cannot call MiniMax-M3
.venv/bin/python scripts/run_minimax_edit.py
```

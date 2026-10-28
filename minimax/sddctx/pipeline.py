from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sddctx.config import Config
from sddctx.context import power_view, render_context, select_hits, symbols_to_change
from sddctx.editing import materialize_model_output, unified_diff, write_sample
from sddctx.minimax_api import assistant_text, build_messages, call_minimax, request_body, response_summary
from sddctx.power import ensure_scope, ensure_server, prepare_context, remember, search_memory
from sddctx.store import import_materials, search_materials
from sddctx.testing import run_pytest, write_log
from sddctx.textutil import scrub, sha256_text


def _write_json(path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_task(cfg: Config) -> str:
    if not cfg.task_file.is_file():
        raise SystemExit(f"task file not found: {cfg.task_file}")
    return cfg.task_file.read_text(encoding="utf-8")


def read_power(cfg: Config) -> dict[str, Any]:
    ensure_server(cfg)
    scope_id = ensure_scope(cfg)
    search_payload = search_memory(cfg, scope_id)
    prepare_payload = prepare_context(cfg, scope_id)
    view = power_view(search_payload, prepare_payload)
    view["scope_id"] = scope_id
    return view


def build_context(cfg: Config) -> dict[str, Any]:
    task = load_task(cfg)
    hits = search_materials(cfg, task)
    selected = select_hits(task, hits)
    power = read_power(cfg)
    markdown = render_context(task, selected, power, cfg.collection)
    spec_documents = [hit["document"] for hit in selected["spec"]]
    return {
        "task": task,
        "markdown": markdown,
        "selected": [
            {
                "id": hit["id"],
                "score": hit["score"],
                "lexical": hit["lexical"],
                "metadata": hit.get("metadata") or {},
            }
            for hit in selected["spec"] + selected["code"] + selected["test"]
        ],
        "symbols_to_change": symbols_to_change(task, selected["code"]),
        "spec_documents": spec_documents,
        "power": {
            "status": power["status"],
            "action": power["action"],
            "fields": power["fields"],
            "artifact_id": power["artifact_id"],
            "prepare_status": power["prepare_status"],
            "scope_id": power["scope_id"],
        },
    }


def write_context(cfg: Config, bundle: dict[str, Any], out_md) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(bundle["markdown"], encoding="utf-8")
    _write_json(out_md.with_suffix(".json"), {key: value for key, value in bundle.items() if key != "markdown"})


def save_state(
    cfg: Config,
    *,
    feature_exit: int,
    regression_exit: int,
    verification: str,
    next_action: str,
    nonce: str,
) -> dict[str, Any]:
    ensure_server(cfg)
    scope_id = ensure_scope(cfg)
    spec_sha = sha256_text((cfg.project / "docs" / "spec.md").read_text(encoding="utf-8"))
    code_sha = sha256_text((cfg.project / "src" / "shiftpay.py").read_text(encoding="utf-8"))
    saved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = "\n".join(
        [
            "SDD_TASK=holiday-overtime",
            f"saved_at={saved_at}",
            f"nonce={nonce}",
            f"feature_exit={feature_exit}",
            f"regression_exit={regression_exit}",
            f"spec_sha256={spec_sha}",
            f"code_sha256={code_sha}",
            f"verification={verification}",
            f"next_action={next_action}",
        ]
    )
    response = remember(cfg, scope_id, text)
    payload = {"scope_id": scope_id, "text": text, "response": response}
    _write_json(cfg.evidence / "powercontext_remember.json", payload)
    return payload


def resume_state(cfg: Config, out_path) -> int:
    power = read_power(cfg)
    payload = {
        "status": power["status"],
        "action": power["action"],
        "fields": power["fields"],
        "artifact_id": power["artifact_id"],
        "prepare_status": power["prepare_status"],
        "prepare_text": power["prepare_text"],
        "scope_id": power["scope_id"],
        "search": power["search"],
        "prepare": power["prepare"],
        "used_state": power["status"] == "ready",
    }
    _write_json(out_path, payload)
    if power["status"] != "ready":
        print("status=empty")
        print("action=empty")
        return 2
    fields = power["fields"]
    print("status=ready")
    print(f"action={power['action']}")
    print(f"artifact_id={power['artifact_id']}")
    for key in ("nonce", "feature_exit", "regression_exit", "spec_sha256", "code_sha256", "verification", "next_action"):
        if key in fields:
            print(f"{key}={fields[key]}")
    if power["action"] == "skip_edit":
        print("use=skip further MiniMax edit because PowerContext verification already passed")
    else:
        print("use=continue holiday overtime edit using the stored spec_sha256 and next_action")
    return 0


def _write_prompt_artifacts(cfg: Config, messages: list[dict[str, str]], bundle: dict[str, Any]) -> None:
    cfg.evidence.mkdir(parents=True, exist_ok=True)
    (cfg.evidence / "minimax_context.md").write_text(bundle["markdown"], encoding="utf-8")
    prompt = "# SYSTEM\n" + messages[0]["content"] + "\n# USER\n" + messages[1]["content"]
    (cfg.evidence / "minimax_prompt.md").write_text(prompt, encoding="utf-8")
    body = request_body(cfg, messages)
    _write_json(cfg.evidence / "minimax_request.json", body)
    _write_json(
        cfg.evidence / "context_for_edit.json",
        {key: value for key, value in bundle.items() if key != "markdown"},
    )


def _development_record(cfg: Config, body: str) -> None:
    cfg.records.mkdir(parents=True, exist_ok=True)
    text = body.rstrip() + "\n"
    (cfg.records / "minimax_development.md").write_text(text, encoding="utf-8")
    (cfg.evidence / "minimax_development.md").write_text(text, encoding="utf-8")


def write_todo(cfg: Config, reason: str) -> None:
    cfg.evidence.mkdir(parents=True, exist_ok=True)
    text = f"""# TODO: MiniMax live call was not run

{reason}

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
"""
    (cfg.evidence / "TODO_MINIMAX.md").write_text(text, encoding="utf-8")
    _development_record(
        cfg,
        "\n".join(
            [
                "# MiniMax 开发记录",
                "",
                "实时调用未执行。这不是模型回复，也没有代码差异。",
                "",
                f"原因：{reason}",
                "",
                "上下文草稿：evidence/minimax_context.md",
                "将要发送的请求体：evidence/minimax_request.json",
                "待办：evidence/TODO_MINIMAX.md",
            ]
        ),
    )


def edit_project(cfg: Config, dry_run: bool) -> int:
    summary = import_materials(cfg)
    print(f"imported {summary['upserted']} chunks into {summary['collection']} (count={summary['count']})")
    bundle = build_context(cfg)
    messages = build_messages(bundle["markdown"])
    _write_prompt_artifacts(cfg, messages, bundle)
    if dry_run:
        _write_json(
            cfg.evidence / "minimax_dry_run.json",
            {"dry_run": True, "minimax_called": False, "model": cfg.minimax_model, "base_url": cfg.minimax_base},
        )
        print("dry-run: wrote evidence/minimax_prompt.md and evidence/minimax_request.json")
        return 0
    if not cfg.minimax_key:
        write_todo(cfg, "MINIMAX_API_KEY is not set, so the OpenAPI was not called.")
        print("MINIMAX_API_KEY is not set. Wrote evidence/TODO_MINIMAX.md. Re-run with the key or pass --dry-run.")
        return 2
    if bundle["power"]["action"] == "skip_edit":
        note = {
            "minimax_called": False,
            "skipped": True,
            "reason": "PowerContext state says verification already passed",
            "fields": bundle["power"]["fields"],
        }
        _write_json(cfg.evidence / "minimax_skipped.json", note)
        print("PowerContext reuse: verification already passed; MiniMax was not called again.")
        return 0

    feature_code, feature_log = run_pytest(cfg, "feature")
    write_log(cfg.evidence / "tests" / "feature_before.log", feature_log)
    regression_code, regression_log = run_pytest(cfg, "regression")
    write_log(cfg.evidence / "tests" / "regression_before.log", regression_log)
    if feature_code == 0:
        print("feature tests already pass; restore sample/src/shiftpay.py before calling MiniMax.")
        return 1
    if regression_code != 0:
        print("regression tests failed before the edit; MiniMax was not called.")
        return 1

    before_path = cfg.project / "src" / "shiftpay.py"
    before = before_path.read_text(encoding="utf-8")
    snapshot_dir = cfg.evidence / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "shiftpay.py.before").write_text(before, encoding="utf-8")
    try:
        response = call_minimax(cfg, messages)
        assistant = assistant_text(response)
    except Exception as exc:
        message = scrub(str(exc), cfg.minimax_key)
        _write_json(cfg.evidence / "minimax_call_error.json", {"minimax_called": True, "error": message})
        print(message)
        return 1
    summary_payload = response_summary(response, assistant)
    _write_json(cfg.evidence / "minimax_response_summary.json", summary_payload)
    todo = cfg.evidence / "TODO_MINIMAX.md"
    if todo.exists():
        todo.unlink()
    try:
        updated = materialize_model_output(before, assistant)
    except ValueError as exc:
        _write_json(
            cfg.evidence / "minimax_apply_error.json",
            {"minimax_called": True, "error": str(exc), "response_id": summary_payload.get("id")},
        )
        print(f"MiniMax replied but the edit could not be applied: {exc}")
        return 1
    diff = unified_diff(before, updated)
    (snapshot_dir / "shiftpay.py.after").write_text(updated, encoding="utf-8")
    (snapshot_dir / "shiftpay.diff").write_text(diff, encoding="utf-8")
    write_sample(cfg.project, updated)
    feature_after, feature_after_log = run_pytest(cfg, "feature")
    write_log(cfg.evidence / "tests" / "feature_after.log", feature_after_log)
    regression_after, regression_after_log = run_pytest(cfg, "regression")
    write_log(cfg.evidence / "tests" / "regression_after.log", regression_after_log)
    verification = "passed" if feature_after == 0 and regression_after == 0 else "failed"
    next_action = (
        "验收已通过，不要再次修改 overtime_pay"
        if verification == "passed"
        else "MiniMax 修改未通过测试，根据失败日志继续修 holiday 分支"
    )
    save_state(
        cfg,
        feature_exit=feature_after,
        regression_exit=regression_after,
        verification=verification,
        next_action=next_action,
        nonce=summary_payload["assistant_sha256"][:16],
    )
    _development_record(
        cfg,
        "\n".join(
            [
                "# MiniMax 开发记录",
                "",
                "这次记录来自一次真实的 MiniMax Chat Completions 调用。",
                "",
                f"- model: {summary_payload.get('model')}",
                f"- response_id: {summary_payload.get('id')}",
                f"- finish_reason: {summary_payload.get('finish_reason')}",
                f"- assistant_sha256: {summary_payload.get('assistant_sha256')}",
                f"- feature_before_exit: {feature_code}",
                f"- regression_before_exit: {regression_code}",
                f"- feature_after_exit: {feature_after}",
                f"- regression_after_exit: {regression_after}",
                "",
                "送给模型的上下文是 evidence/minimax_context.md，请求体是 evidence/minimax_request.json。",
                "下面的 diff 由「调用前的 src/shiftpay.py」与「从助手消息解析出的文件」比较得到，",
                "并已写入 sample/src/shiftpay.py 后跑测试。",
                "",
                "## diff",
                "",
                "```diff",
                diff.rstrip(),
                "```",
                "",
                "## assistant message",
                "",
                "```",
                assistant.rstrip(),
                "```",
            ]
        ),
    )
    print(f"MiniMax edit applied. feature_after={feature_after} regression_after={regression_after}")
    return 0 if verification == "passed" else 1

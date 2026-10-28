from __future__ import annotations

import re
from typing import Any

from sddctx.textutil import decide_action, lexical_score

_DEF = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


def select_hits(task: str, hits: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    for hit in hits:
        metadata = hit.get("metadata") or {}
        lexical = lexical_score(task, hit.get("document") or "", metadata)
        if lexical <= 0:
            continue
        scored.append({**hit, "lexical": lexical, "score": lexical + 1.0 / (hit.get("rank", 0) + 1)})
    scored.sort(key=lambda item: (-item["score"], item.get("rank", 0), item["id"]))

    def top(kind: str, limit: int) -> list[dict[str, Any]]:
        return [item for item in scored if (item.get("metadata") or {}).get("kind") == kind][:limit]

    specs = top("spec", 4)
    codes = top("code", 2)
    tests = top("test", 4)
    feature = [item for item in tests if (item.get("metadata") or {}).get("role") == "feature"]
    if not specs or not codes or not feature:
        preview = [
            {
                "id": item["id"],
                "score": item["score"],
                "path": (item.get("metadata") or {}).get("path"),
                "kind": (item.get("metadata") or {}).get("kind"),
                "role": (item.get("metadata") or {}).get("role"),
            }
            for item in scored
        ]
        raise SystemExit(f"seekdb selection missed spec/code/feature test. scored={preview}")
    return {"spec": specs, "code": codes, "test": tests, "scored": scored}


def symbols_to_change(task: str, code_hits: list[dict[str, Any]]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for hit in code_hits:
        metadata = hit.get("metadata") or {}
        path = str(metadata.get("path") or "")
        for name in _DEF.findall(hit.get("document") or ""):
            if name in task and (path, name) not in seen:
                seen.add((path, name))
                found.append({"path": path, "symbol": name})
    return found


def render_context(
    task: str,
    selected: dict[str, list[dict[str, Any]]],
    power: dict[str, Any],
    collection: str,
) -> str:
    symbols = symbols_to_change(task, selected["code"])
    lines = [
        "# 开发上下文",
        "",
        "以下规格、代码和测试正文来自 seekdb 查询结果，不是写死的答案。",
        f"collection: {collection}",
        "",
        "## 任务说明（本次请求）",
        task.strip(),
        "",
        "## 任务状态（PowerContext）",
        f"status: {power.get('status', 'empty')}",
        f"action: {power.get('action', 'empty')}",
        "<!-- begin powercontext -->",
        (power.get("text") or "status=empty").strip(),
        "<!-- end powercontext -->",
        "",
        "## 需要修改的符号",
    ]
    if symbols:
        for item in symbols:
            lines.append(f"- {item['path']} :: {item['symbol']}")
    else:
        lines.append("- （查询结果中的函数名没有出现在任务里）")
    lines.extend(["", "## 相关测试"])
    for hit in selected["test"]:
        metadata = hit.get("metadata") or {}
        lines.append(f"- {metadata.get('path')} :: {metadata.get('symbol')} (role={metadata.get('role')})")
    for kind in ("spec", "code", "test"):
        lines.extend(["", f"## 选中的{kind}"])
        for hit in selected[kind]:
            metadata = hit.get("metadata") or {}
            lines.append(
                f"<!-- begin {kind} {metadata.get('path')} {metadata.get('symbol')} id={hit['id']} -->"
            )
            lines.append((hit.get("document") or "").strip())
            lines.append(f"<!-- end {kind} -->")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def power_view(search_payload: dict[str, Any], prepare_payload: dict[str, Any]) -> dict[str, Any]:
    from sddctx.textutil import parse_kv

    newest_text = ""
    fields: dict[str, str] = {}
    artifact_id = ""
    newest_saved = ""
    for hit in search_payload.get("hits") or []:
        memory = hit.get("memory") or {}
        text = memory.get("text") or ""
        parsed = parse_kv(text)
        saved = parsed.get("saved_at", "")
        if text and (not newest_text or saved >= newest_saved):
            newest_text = text
            fields = parsed
            newest_saved = saved
            artifact_id = (memory.get("artifact") or {}).get("artifact_id") or artifact_id
    prepare_status = prepare_payload.get("status") or "empty"
    prepare_text = prepare_payload.get("content") or ""
    status = "ready" if fields or prepare_status == "ready" else "empty"
    shown = newest_text or prepare_text or "status=empty"
    return {
        "status": status,
        "action": decide_action(fields),
        "fields": fields,
        "text": shown,
        "artifact_id": artifact_id,
        "prepare_status": prepare_status,
        "prepare_text": prepare_text,
        "search": search_payload,
        "prepare": prepare_payload,
    }

from __future__ import annotations

import json

from sddctx.config import Config


def write_seekdb_record(cfg: Config) -> None:
    path = cfg.evidence / "seekdb_queries.jsonl"
    lines = [
        "# seekdb 查询记录",
        "",
        "这些条目复制自同一次运行写入的 `evidence/seekdb_queries.jsonl`。",
        "上下文模块只把这里返回的 document 放进开发上下文。",
        "",
    ]
    if not path.is_file():
        lines.append("（没有查询日志）")
    else:
        for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            record = json.loads(raw)
            lines.append(f"## {index}. {record.get('op')}")
            lines.append("")
            lines.append(f"- ts: `{record.get('ts')}`")
            lines.append(f"- detail: `{json.dumps(record.get('detail'), ensure_ascii=False)}`")
            lines.append(f"- ids: `{record.get('ids')}`")
            hits = record.get("hits") or []
            for hit in hits[:6]:
                metadata = hit.get("metadata") or {}
                preview = (hit.get("document") or "").replace("\n", " ")[:240]
                lines.append(
                    f"- hit `{hit.get('id')}` path=`{metadata.get('path')}` symbol=`{metadata.get('symbol')}`: {preview}"
                )
            lines.append("")
    cfg.records.mkdir(parents=True, exist_ok=True)
    (cfg.records / "seekdb_queries.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_power_record(cfg: Config, empty_stdout: str, reuse_stdout: str) -> None:
    empty = _read(cfg.evidence / "powercontext_empty.json")
    remembered = _read(cfg.evidence / "powercontext_remember.json")
    reused = _read(cfg.evidence / "powercontext_reuse.json")
    lines = [
        "# PowerContext 状态记录",
        "",
        "上下文模块进程本身不保存任务进度。下面的空状态、写入和再次读取都来自 PowerContext HTTP API。",
        "",
        "## 空状态",
        "",
        "```",
        empty_stdout.strip(),
        "```",
        "",
        f"- prepare status: `{empty.get('prepare_status')}`",
        f"- search hits: `{len((empty.get('search') or {}).get('hits') or [])}`",
        "",
        "## 写入 /v1/memory/remember",
        "",
        "```",
        (remembered.get("text") or "").strip(),
        "```",
        "",
        f"- artifact: `{(remembered.get('response') or {}).get('records')}`",
        "",
        "## 新进程读取并使用",
        "",
        "第二次运行是新的 Python 进程。它只调用 `/v1/memory/search` 和 `/v1/context/prepare`，",
        "再根据返回的 `verification` / `feature_exit` 决定下一步。",
        "",
        "```",
        reuse_stdout.strip(),
        "```",
        "",
        f"- artifact_id: `{reused.get('artifact_id')}`",
        f"- action: `{reused.get('action')}`",
        f"- prepare status: `{reused.get('prepare_status')}`",
        "",
    ]
    cfg.records.mkdir(parents=True, exist_ok=True)
    (cfg.records / "powercontext.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _read(path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

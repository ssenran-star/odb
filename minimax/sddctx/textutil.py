from __future__ import annotations

import hashlib
import re
from pathlib import Path

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
_CJK = re.compile(r"[\u4e00-\u9fff]+")
_KV_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_kv(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if _KV_KEY.fullmatch(key):
            fields[key] = value.strip()
    return fields


def decide_action(fields: dict[str, str]) -> str:
    if not fields or "verification" not in fields:
        return "empty"
    passed = (
        fields.get("verification") == "passed"
        and fields.get("feature_exit") == "0"
        and fields.get("regression_exit") == "0"
    )
    if passed:
        return "skip_edit"
    return "continue_edit"


def lexical_score(task: str, document: str, metadata: dict | None = None) -> float:
    """Overlap between the task and one stored document. Zero means the hit is off-task."""
    metadata = metadata or {}
    score = 0.0
    for ident in _IDENT.findall(task):
        if ident in document:
            score += 3.0
    for run in _CJK.findall(task):
        upper = min(6, len(run))
        for size in range(upper, 1, -1):
            for index in range(0, len(run) - size + 1):
                gram = run[index : index + size]
                if gram in document:
                    score += size / 2.0
    symbol = str(metadata.get("symbol") or "")
    if symbol and symbol not in {"__file__", "概述"} and symbol in task:
        score += 5.0
    return score


def scrub(text: str, secret: str) -> str:
    if secret:
        return text.replace(secret, "[REDACTED]")
    return text

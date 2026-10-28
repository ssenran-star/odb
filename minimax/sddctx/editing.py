from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_DIFF_FENCE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_python_module(text: str) -> str:
    for block in _FENCE.findall(text):
        if "def overtime_pay" in block and "def regular_pay" in block:
            return block.strip() + "\n"
    stripped = text.strip()
    if "def overtime_pay" in stripped and "def regular_pay" in stripped and "```" not in stripped:
        return stripped + "\n"
    raise ValueError("model output did not contain src/shiftpay.py")


def _extract_diff(text: str) -> str:
    match = _DIFF_FENCE.search(text)
    if match:
        return match.group(1)
    if "@@" in text and ("--- " in text or "diff --git" in text):
        start = text.find("--- ")
        if start < 0:
            start = text.find("diff --git")
        return text[start:]
    raise ValueError("model output did not contain a unified diff")


def apply_unified_diff(before: str, model_text: str) -> str:
    diff = _extract_diff(model_text)
    if not diff.endswith("\n"):
        diff += "\n"
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = root / "src" / "shiftpay.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(before, encoding="utf-8")
        patch_file = root / "edit.diff"
        patch_file.write_text(diff, encoding="utf-8")
        for strip in ("1", "0"):
            subprocess.run(["git", "checkout", "--", "src/shiftpay.py"], cwd=root, capture_output=True)
            target.write_text(before, encoding="utf-8")
            result = subprocess.run(
                ["patch", "-p", strip, "--forward", "--batch", "-i", str(patch_file)],
                cwd=root,
                text=True,
                capture_output=True,
            )
            if result.returncode == 0 and target.is_file():
                return target.read_text(encoding="utf-8")
        raise ValueError("patch could not apply the model diff")


def materialize_model_output(before: str, model_text: str) -> str:
    try:
        updated = extract_python_module(model_text)
    except ValueError:
        updated = apply_unified_diff(before, model_text)
    validate_source(updated)
    return updated


def validate_source(text: str) -> None:
    required = ("def regular_pay", "def overtime_pay", "weekday", "weekend", "holiday", "ValueError")
    missing = [token for token in required if token not in text]
    if missing:
        raise ValueError(f"updated shiftpay.py is missing {missing}")
    if len(text.splitlines()) > 250:
        raise ValueError("updated shiftpay.py is unexpectedly large")


def unified_diff(before: str, after: str, path: str = "sample/src/shiftpay.py") -> str:
    import difflib

    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def write_sample(project: Path, source: str) -> Path:
    target = (project / "src" / "shiftpay.py").resolve()
    root = (project / "src").resolve()
    if target.parent != root:
        raise ValueError(f"refusing to write outside {root}")
    target.write_text(source, encoding="utf-8")
    return target

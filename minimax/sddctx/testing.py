from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sddctx.config import Config
from sddctx.textutil import sha256_file

SUITES = {
    "feature": ["tests/test_feature_holiday.py"],
    "regression": ["tests/test_regression_pay.py"],
    "decoy": ["tests/test_unrelated_parking.py"],
}


def run_pytest(cfg: Config, suite: str) -> tuple[int, str]:
    if suite not in SUITES:
        raise SystemExit(f"unknown suite {suite}")
    code_path = cfg.project / "src" / "shiftpay.py"
    command = [sys.executable, "-m", "pytest", "-q", "--tb=short", *SUITES[suite]]
    completed = subprocess.run(
        command,
        cwd=cfg.project,
        text=True,
        capture_output=True,
    )
    git_head = ""
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cfg.root,
        text=True,
        capture_output=True,
    )
    if git.returncode == 0:
        git_head = git.stdout.strip()
    header = "\n".join(
        [
            f"command: {' '.join(command)}",
            f"cwd: {cfg.project}",
            f"exit_code: {completed.returncode}",
            f"code_path: src/shiftpay.py",
            f"code_sha256: {sha256_file(code_path)}",
            f"python: {sys.version.split()[0]}",
            f"git_head: {git_head}",
        ]
    )
    body = (
        header
        + "\n--- pytest stdout ---\n"
        + completed.stdout
        + "\n--- pytest stderr ---\n"
        + completed.stderr
    )
    return completed.returncode, body


def write_log(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")

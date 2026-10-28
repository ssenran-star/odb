from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _under_root(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


@dataclass(frozen=True)
class Config:
    root: Path
    project: Path
    task_file: Path
    seekdb_path: Path
    seekdb_database: str
    collection: str
    power_url: str
    power_token: str
    power_home: Path
    power_port: int
    scope_key: str
    scope_title: str
    scope_cache: Path
    pid_file: Path
    server_log: Path
    minimax_key: str
    minimax_base: str
    minimax_model: str
    minimax_temperature: float
    minimax_max_tokens: int
    minimax_timeout: float
    evidence: Path
    records: Path


def load_config(project: str | None = None, task: str | None = None) -> Config:
    load_dotenv(ROOT / ".env")
    data = ROOT / "data"
    project_path = _under_root(project or os.environ.get("SDD_PROJECT"), ROOT / "sample")
    task_path = _under_root(task or os.environ.get("SDD_TASK_FILE"), ROOT / "sample" / "TASK.md")
    power_url = os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8765").rstrip("/")
    parsed = urlparse(power_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return Config(
        root=ROOT,
        project=project_path,
        task_file=task_path,
        seekdb_path=_under_root(os.environ.get("SEEKDB_PATH"), data / "seekdb"),
        seekdb_database=os.environ.get("SEEKDB_DATABASE", "test"),
        collection=os.environ.get("SEEKDB_COLLECTION", "sdd_materials"),
        power_url=power_url,
        power_token=os.environ.get("POWERCONTEXT_TOKEN", ""),
        power_home=_under_root(os.environ.get("POWERCONTEXT_HOME"), data / "powercontext"),
        power_port=port,
        scope_key=os.environ.get("POWERCONTEXT_SCOPE_KEY", "sdd-holiday-overtime"),
        scope_title=os.environ.get("POWERCONTEXT_SCOPE_TITLE", "SDD holiday overtime"),
        scope_cache=data / "scope.json",
        pid_file=data / "powercontext.pid",
        server_log=data / "powercontext-server.log",
        minimax_key=os.environ.get("MINIMAX_API_KEY", "").strip(),
        minimax_base=os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1").rstrip("/"),
        minimax_model=os.environ.get("MINIMAX_MODEL", "MiniMax-M3"),
        minimax_temperature=float(os.environ.get("MINIMAX_TEMPERATURE", "1")),
        minimax_max_tokens=int(os.environ.get("MINIMAX_MAX_TOKENS", "8192")),
        minimax_timeout=float(os.environ.get("MINIMAX_TIMEOUT", "180")),
        evidence=ROOT / "evidence",
        records=ROOT / "records",
    )

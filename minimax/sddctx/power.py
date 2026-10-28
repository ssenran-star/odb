from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sddctx.config import Config
from sddctx.textutil import scrub


class PowerContextError(RuntimeError):
    pass


def _request(cfg: Config, method: str, path: str, payload: dict[str, Any] | None, timeout: float = 20) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if cfg.power_token:
        headers["Authorization"] = f"Bearer {cfg.power_token}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(cfg.power_url + path, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        detail = scrub(exc.read().decode("utf-8", errors="replace"), cfg.power_token)
        raise PowerContextError(f"PowerContext {method} {path} failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise PowerContextError(f"PowerContext {method} {path} unreachable: {exc}") from exc


def health_ready(cfg: Config) -> bool:
    try:
        body = _request(cfg, "GET", "/health/ready", None, timeout=3)
    except PowerContextError:
        return False
    return body.get("status") in {"ready", "ok", "degraded"}


def powercontext_bin() -> str:
    found = shutil.which("powercontext")
    if found:
        return found
    candidate = Path.home() / ".local" / "bin" / "powercontext"
    if candidate.is_file():
        return str(candidate)
    raise SystemExit(
        "powercontext CLI not found. Install with: "
        "uv tool install --force 'powercontext[cli,server]==1.4.0'"
    )


def _local(cfg: Config) -> bool:
    host = urlparse(cfg.power_url).hostname
    return host in {"127.0.0.1", "localhost"}


def stop_server(cfg: Config) -> None:
    if not cfg.pid_file.is_file():
        return
    raw = cfg.pid_file.read_text(encoding="utf-8").strip()
    cfg.pid_file.unlink(missing_ok=True)
    try:
        pid = int(raw)
    except ValueError:
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(20):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.25)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def start_server(cfg: Config) -> None:
    if not _local(cfg):
        raise SystemExit(f"refusing to launch a server for non-local POWERCONTEXT_URL={cfg.power_url}")
    cfg.power_home.mkdir(parents=True, exist_ok=True)
    cfg.server_log.parent.mkdir(parents=True, exist_ok=True)
    log = open(cfg.server_log, "a", encoding="utf-8")
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": str(Path.home() / ".local" / "bin") + os.pathsep + os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "POWERCONTEXT_HOME": str(cfg.power_home),
    }
    process = subprocess.Popen(
        [powercontext_bin(), "server", "run", "--host", "127.0.0.1", "--port", str(cfg.power_port)],
        cwd=str(cfg.power_home),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    cfg.pid_file.write_text(str(process.pid), encoding="utf-8")
    for _ in range(40):
        if health_ready(cfg):
            return
        if process.poll() is not None:
            raise SystemExit(f"PowerContext exited early. See {cfg.server_log}")
        time.sleep(0.5)
    raise SystemExit(f"PowerContext did not become ready. See {cfg.server_log}")


def ensure_server(cfg: Config) -> None:
    if health_ready(cfg):
        return
    if not _local(cfg):
        raise SystemExit(f"PowerContext is not reachable at {cfg.power_url}")
    start_server(cfg)


def reset_runtime(cfg: Config) -> None:
    stop_server(cfg)
    shutil.rmtree(cfg.power_home, ignore_errors=True)
    shutil.rmtree(cfg.seekdb_path, ignore_errors=True)
    cfg.scope_cache.unlink(missing_ok=True)
    start_server(cfg)


def ensure_scope(cfg: Config) -> str:
    env_scope = os.environ.get("POWERCONTEXT_SCOPE", "").strip()
    if env_scope:
        return env_scope
    if cfg.scope_cache.is_file():
        cached = json.loads(cfg.scope_cache.read_text(encoding="utf-8"))
        if cached.get("scope_id"):
            return str(cached["scope_id"])
    created = _request(
        cfg,
        "POST",
        "/v1/scopes",
        {
            "title": cfg.scope_title,
            "summary": "shiftpay holiday overtime task progress",
            "idempotency_key": cfg.scope_key,
        },
    )
    cfg.scope_cache.parent.mkdir(parents=True, exist_ok=True)
    cfg.scope_cache.write_text(json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(created["scope_id"])


def search_memory(cfg: Config, scope_id: str) -> dict[str, Any]:
    return _request(
        cfg,
        "POST",
        "/v1/memory/search",
        {"scope_id": scope_id, "query": "SDD_TASK holiday-overtime", "limit": 10},
    )


def prepare_context(cfg: Config, scope_id: str) -> dict[str, Any]:
    return _request(
        cfg,
        "POST",
        "/v1/context/prepare",
        {"scope_id": scope_id, "query": "SDD_TASK holiday-overtime", "max_bytes": 4000},
    )


def remember(cfg: Config, scope_id: str, text: str) -> dict[str, Any]:
    return _request(
        cfg,
        "POST",
        "/v1/memory/remember",
        {
            "scope_id": scope_id,
            "kind": "progress",
            "text": text,
            "reason": "sdd context module saved task progress and verification",
        },
    )

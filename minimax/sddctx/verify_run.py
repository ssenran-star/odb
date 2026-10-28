from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from sddctx.config import ROOT, Config
from sddctx.reporting import write_power_record, write_seekdb_record
from sddctx.textutil import sha256_file


def _env() -> dict[str, str]:
    env = os.environ.copy()
    local_bin = str(Path.home() / ".local" / "bin")
    env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sddctx", *args],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
    )


def _check(name: str, completed: subprocess.CompletedProcess[str], expect: int | None = 0) -> None:
    if expect is not None and completed.returncode != expect:
        raise SystemExit(
            f"{name} exited {completed.returncode}, expected {expect}\n"
            f"--- stdout ---\n{completed.stdout}\n--- stderr ---\n{completed.stderr}"
        )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _spec_text(payload: dict) -> str:
    return "\n".join(payload.get("spec_documents") or [])


def run_verify(cfg: Config) -> int:
    spec_path = cfg.project / "docs" / "spec.md"
    code_path = cfg.project / "src" / "shiftpay.py"
    spec_orig = spec_path.read_bytes()
    code_orig = code_path.read_bytes()
    log_dir = cfg.evidence / "verify_steps"
    log_dir.mkdir(parents=True, exist_ok=True)
    query_log = cfg.evidence / "seekdb_queries.jsonl"
    if query_log.exists():
        query_log.unlink()
    nonce = uuid.uuid4().hex
    empty_stdout = ""
    reuse_stdout = ""
    try:
        reset = _run(["reset"])
        _check("reset", reset)
        (log_dir / "reset.log").write_text(reset.stdout + reset.stderr, encoding="utf-8")

        empty = _run(["resume", "--out", "evidence/powercontext_empty.json"])
        _check("resume-empty", empty, expect=2)
        empty_stdout = empty.stdout
        empty_payload = _load(cfg.evidence / "powercontext_empty.json")
        if empty_payload.get("prepare_status") != "empty":
            raise SystemExit(f"expected empty prepare, got {empty_payload.get('prepare_status')}")
        if (empty_payload.get("search") or {}).get("hits"):
            raise SystemExit("expected PowerContext search hits to be empty")

        imported = _run(["import"])
        _check("import", imported)
        selected = _run(["select", "--out", "evidence/context_v1.md"])
        _check("select-v1", selected)
        context_v1 = _load(cfg.evidence / "context_v1.json")
        spec_v1 = _spec_text(context_v1)
        if "HOLIDAY_MULTIPLIER = 3.0" not in spec_v1:
            raise SystemExit("context v1 spec did not contain the stored multiplier 3.0")
        if "SDD-REV-7719" in spec_v1:
            raise SystemExit("context v1 unexpectedly contained the revision token")
        if "PARKING-FEE-UNRELATED" in (cfg.evidence / "context_v1.md").read_text(encoding="utf-8"):
            raise SystemExit("context v1 included the unrelated parking document")
        symbols = {item["symbol"] for item in context_v1["symbols_to_change"]}
        if "overtime_pay" not in symbols:
            raise SystemExit(f"symbols_to_change missing overtime_pay: {context_v1['symbols_to_change']}")
        markdown_v1 = (cfg.evidence / "context_v1.md").read_text(encoding="utf-8")
        for needle in ("src/shiftpay.py", "test_holiday_overtime_uses_spec_multiplier", "docs/spec.md"):
            if needle not in markdown_v1:
                raise SystemExit(f"context v1 missing {needle}")

        spec_path.write_text(
            spec_orig.decode("utf-8").replace(
                "HOLIDAY_MULTIPLIER = 3.0",
                "HOLIDAY_MULTIPLIER = 3.5  # SDD-REV-7719",
                1,
            ),
            encoding="utf-8",
        )
        _check("reimport", _run(["import"]))
        _check("select-v2", _run(["select", "--out", "evidence/context_v2.md"]))
        spec_v2 = _spec_text(_load(cfg.evidence / "context_v2.json"))
        if "SDD-REV-7719" not in spec_v2 or "HOLIDAY_MULTIPLIER = 3.5" not in spec_v2:
            raise SystemExit("context v2 did not use the updated spec text")
        if "HOLIDAY_MULTIPLIER = 3.0" in spec_v2:
            raise SystemExit("context v2 still contains the old multiplier line")

        spec_path.write_bytes(spec_orig)
        _check("restore-import", _run(["import"]))

        feature = _run(["test", "--suite", "feature", "--log", "evidence/tests/feature_before.log"])
        _check("feature-before", feature, expect=1)
        feature_log = (cfg.evidence / "tests" / "feature_before.log").read_text(encoding="utf-8")
        if "AssertionError" not in feature_log and "assert 0.0" not in feature_log:
            raise SystemExit("feature failure was not an assertion about missing behavior")
        if "ModuleNotFoundError" in feature_log or "ImportError" in feature_log:
            raise SystemExit("feature test failed because of an import/env error")
        regression = _run(["test", "--suite", "regression", "--log", "evidence/tests/regression_before.log"])
        _check("regression-before", regression, expect=0)
        decoy = _run(["test", "--suite", "decoy", "--log", "evidence/tests/decoy_before.log"])
        _check("decoy-before", decoy, expect=0)

        code_before_edit = code_path.read_bytes()
        dry = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_minimax_edit.py"), "--dry-run"],
            cwd=ROOT,
            env=_env(),
            text=True,
            capture_output=True,
        )
        _check("dry-run", dry, expect=0)
        if code_path.read_bytes() != code_before_edit:
            raise SystemExit("dry-run modified the sample")
        prompt = (cfg.evidence / "minimax_prompt.md").read_text(encoding="utf-8")
        request = _load(cfg.evidence / "minimax_request.json")
        if prompt != "# SYSTEM\n" + request["messages"][0]["content"] + "\n# USER\n" + request["messages"][1]["content"]:
            raise SystemExit("dry-run prompt does not match the request body")
        if "HOLIDAY_MULTIPLIER = 3.0" not in request["messages"][1]["content"]:
            raise SystemExit("prompt context lost the restored spec")
        if "SDD-REV-7719" in request["messages"][1]["content"]:
            raise SystemExit("prompt context still contains the temporary spec revision")
        if "Authorization" in json.dumps(request):
            raise SystemExit("request body unexpectedly contains an authorization header")

        remembered = _run(
            [
                "state-save",
                "--feature-exit",
                "1",
                "--regression-exit",
                "0",
                "--verification",
                "dry_run",
                "--next-action",
                "继续修改 overtime_pay；配置 MINIMAX_API_KEY 后执行 scripts/run_minimax_edit.py",
                "--nonce",
                nonce,
            ]
        )
        _check("state-save", remembered)
        reuse = _run(["resume", "--out", "evidence/powercontext_reuse.json"])
        _check("resume-reuse", reuse, expect=0)
        reuse_stdout = reuse.stdout
        if f"nonce={nonce}" not in reuse.stdout:
            raise SystemExit("restarted module did not read the PowerContext nonce")
        if "action=continue_edit" not in reuse.stdout:
            raise SystemExit("restarted module did not use the saved verification to choose continue_edit")
        reuse_payload = _load(cfg.evidence / "powercontext_reuse.json")
        remember_payload = _load(cfg.evidence / "powercontext_remember.json")
        remembered_artifact = remember_payload["response"]["records"][0]["artifact"]["artifact_id"]
        if reuse_payload.get("artifact_id") != remembered_artifact:
            raise SystemExit("resume artifact id does not match the remember response")
        if nonce not in (reuse_payload.get("prepare_text") or ""):
            raise SystemExit("prepare context did not contain the saved nonce")

        _check("select-state", _run(["select", "--out", "evidence/context_with_state.md"]))
        state_md = (cfg.evidence / "context_with_state.md").read_text(encoding="utf-8")
        if nonce not in state_md:
            raise SystemExit("context built by a new process did not include PowerContext state")
        state_spec = _spec_text(_load(cfg.evidence / "context_with_state.json"))
        if "HOLIDAY_MULTIPLIER = 3.0" not in state_spec or "SDD-REV-7719" in state_spec:
            raise SystemExit("stateful context is not using the restored spec")

        logged_ids: set[str] = set()
        for raw in query_log.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                record = json.loads(raw)
                logged_ids.update(record.get("ids") or [])
        missing = [item["id"] for item in context_v1["selected"] if item["id"] not in logged_ids]
        if missing:
            raise SystemExit(f"selected ids were not returned by seekdb queries: {missing}")
        query_text = query_log.read_text(encoding="utf-8")
        if "SDD-REV-7719" not in query_text or "HOLIDAY_MULTIPLIER = 3.0" not in query_text:
            raise SystemExit("seekdb query log does not show both spec versions")
        if "hybrid_search" not in query_text:
            raise SystemExit("seekdb query log has no hybrid_search call")

        snapshot = cfg.evidence / "snapshots"
        snapshot.mkdir(parents=True, exist_ok=True)
        (snapshot / "shiftpay.py.before").write_bytes(code_orig)

        write_seekdb_record(cfg)
        write_power_record(cfg, empty_stdout, reuse_stdout)
        todo = cfg.evidence / "TODO_MINIMAX.md"
        if not todo.is_file():
            from sddctx.pipeline import write_todo

            write_todo(cfg, "Step A dry-run finished. The live MiniMax call still has to be run on a machine with MINIMAX_API_KEY.")
        summary = {
            "step": "A",
            "minimax_called": False,
            "todo": "evidence/TODO_MINIMAX.md",
            "feature_before_exit": 1,
            "regression_before_exit": 0,
            "decoy_before_exit": 0,
            "context_fresh": True,
            "seekdb_queries": True,
            "powercontext_empty": True,
            "powercontext_reused": True,
            "nonce": nonce,
            "code_sha256": sha256_file(code_path),
            "spec_sha256": sha256_file(spec_path),
        }
        (cfg.evidence / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("verify step A passed; MiniMax was not called")
        return 0
    finally:
        spec_path.write_bytes(spec_orig)
        code_path.write_bytes(code_orig)

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from sddctx.config import load_config
from sddctx.pipeline import (
    build_context,
    edit_project,
    import_materials,
    resume_state,
    save_state,
    write_context,
)
from sddctx.power import reset_runtime, start_server
from sddctx.testing import run_pytest, write_log


def _config(args: argparse.Namespace):
    return load_config(getattr(args, "project", None), getattr(args, "task", None))


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", default=None, help="sample project directory (default: sample)")
    parser.add_argument("--task", default=None, help="task markdown (default: sample/TASK.md)")


def cmd_import(args: argparse.Namespace) -> int:
    summary = import_materials(_config(args))
    print(
        f"imported {summary['upserted']} chunks into seekdb collection {summary['collection']} "
        f"(count={summary['count']})"
    )
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    cfg = _config(args)
    bundle = build_context(cfg)
    out = Path(args.out)
    if not out.is_absolute():
        out = cfg.root / out
    write_context(cfg, bundle, out)
    print(f"wrote {out}")
    print(f"power_status={bundle['power']['status']} action={bundle['power']['action']}")
    for item in bundle["symbols_to_change"]:
        print(f"symbol {item['path']} :: {item['symbol']}")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    cfg = _config(args)
    code, body = run_pytest(cfg, args.suite)
    if args.log:
        path = Path(args.log)
        if not path.is_absolute():
            path = cfg.root / path
        write_log(path, body)
    sys.stdout.write(body)
    return code


def cmd_state_save(args: argparse.Namespace) -> int:
    cfg = _config(args)
    payload = save_state(
        cfg,
        feature_exit=args.feature_exit,
        regression_exit=args.regression_exit,
        verification=args.verification,
        next_action=args.next_action,
        nonce=args.nonce or uuid.uuid4().hex,
    )
    print(f"remembered nonce={(payload['text'].split('nonce=', 1)[1].splitlines()[0])}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    cfg = _config(args)
    out = Path(args.out)
    if not out.is_absolute():
        out = cfg.root / out
    return resume_state(cfg, out)


def cmd_edit(args: argparse.Namespace) -> int:
    return edit_project(_config(args), dry_run=args.dry_run)


def cmd_serve(args: argparse.Namespace) -> int:
    start_server(_config(args))
    print("PowerContext is ready")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    reset_runtime(_config(args))
    print("reset seekdb and PowerContext, server is ready")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from sddctx.verify_run import run_verify

    return run_verify(_config(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sddctx", description="SDD context module for the MiniMax contest track")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add(name: str, func) -> argparse.ArgumentParser:
        command = sub.add_parser(name)
        _add_common(command)
        command.set_defaults(func=func)
        return command

    add("import", cmd_import)
    select = add("select", cmd_select)
    select.add_argument("--out", required=True)
    test = add("test", cmd_test)
    test.add_argument("--suite", required=True, choices=("feature", "regression", "decoy"))
    test.add_argument("--log")
    state = add("state-save", cmd_state_save)
    state.add_argument("--feature-exit", type=int, required=True)
    state.add_argument("--regression-exit", type=int, required=True)
    state.add_argument("--verification", required=True)
    state.add_argument("--next-action", required=True)
    state.add_argument("--nonce", default=None)
    resume = add("resume", cmd_resume)
    resume.add_argument("--out", required=True)
    edit = add("edit", cmd_edit)
    edit.add_argument("--dry-run", action="store_true")
    add("serve", cmd_serve)
    add("reset", cmd_reset)
    add("verify", cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))

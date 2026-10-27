"""Load the tavern Chatflow DSL and exec its Code nodes.

The contract dry-run calls these functions so the HTTP bodies match the
graph a reviewer imports, instead of a second copy of the request builder.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
DSL_PATH = ROOT / "dsl" / "rust-anchor-tavern-keeper.chatflow.yml"

CodeFn = Callable[..., dict[str, Any]]


def load_workflow(path: Path | None = None) -> dict[str, Any]:
    dsl_path = path or DSL_PATH
    with dsl_path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{dsl_path} did not parse as a YAML mapping")
    return document


def code_functions(workflow: dict[str, Any]) -> dict[str, CodeFn]:
    functions: dict[str, CodeFn] = {}
    nodes = workflow["workflow"]["graph"]["nodes"]
    for node in nodes:
        data = node.get("data") or {}
        if data.get("type") != "code":
            continue
        namespace: dict[str, Any] = {}
        exec(compile(data["code"], f"<dsl:{node['id']}>", "exec"), namespace, namespace)
        main = namespace.get("main")
        if not callable(main):
            raise ValueError(f"code node {node['id']} has no main()")
        functions[str(node["id"])] = main
    return functions


def node_by_title(workflow: dict[str, Any], title: str) -> dict[str, Any]:
    for node in workflow["workflow"]["graph"]["nodes"]:
        if (node.get("data") or {}).get("title") == title:
            return node
    raise KeyError(title)

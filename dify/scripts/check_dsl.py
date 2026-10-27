#!/usr/bin/env python3
"""Offline checks for the tavern-keeper Chatflow DSL.

Does not start Dify or PowerContext. It parses the YAML, checks the graph
points at the published PowerContext paths, and executes the Code nodes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dsl_nodes import code_functions, load_workflow

SEARCH_ID = "1003"
PREPARE_ID = "1005"
REMEMBER_ID = "1010"
BUILD_ID = "1002"
LEDGER_ID = "1004"
PACK_ID = "1006"
DECIDE_ID = "1008"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    workflow = load_workflow()
    raw = (Path(__file__).resolve().parents[1] / "dsl" / "rust-anchor-tavern-keeper.chatflow.yml").read_text(
        encoding="utf-8"
    )
    app = workflow["app"]
    if app.get("mode") != "advanced-chat":
        fail(f"app.mode is {app.get('mode')!r}, expected advanced-chat")
    if app.get("name") != "记仇的酒馆老板":
        fail("unexpected app name")
    if workflow.get("kind") != "app":
        fail("kind must be app")
    if str(workflow.get("version")) != "0.3.0":
        fail("DSL version must stay 0.3.0 so current Dify imports it as an older compatible file")
    if "expected_revision" in raw:
        fail("remember requests must not send expected_revision; the legacy field is rejected")
    if "sk-" in raw or "Authorization: Bearer" in raw:
        fail("DSL contains something that looks like a credential")

    env = {item["name"]: item for item in workflow["workflow"]["environment_variables"]}
    for name in ("POWERCONTEXT_URL", "POWERCONTEXT_SCOPE_ID", "POWERCONTEXT_TOKEN"):
        if name not in env:
            fail(f"missing env {name}")
    if env["POWERCONTEXT_SCOPE_ID"]["value"] != "REPLACE_WITH_SCOPE_ID":
        fail("scope id placeholder was replaced with a real id")
    if env["POWERCONTEXT_TOKEN"]["value"] not in ("", None):
        fail("token placeholder must stay empty")
    if env["POWERCONTEXT_URL"]["value"].rstrip("/") != "http://127.0.0.1:8000":
        fail("default PowerContext URL must be the loopback placeholder")

    nodes = {node["id"]: node for node in workflow["workflow"]["graph"]["nodes"]}
    edges = workflow["workflow"]["graph"]["edges"]
    http_nodes = [node for node in nodes.values() if node["data"]["type"] == "http-request"]
    if len(http_nodes) != 3:
        fail(f"expected 3 HTTP nodes, found {len(http_nodes)}")

    expected_paths = {
        SEARCH_ID: "/v1/memory/search",
        PREPARE_ID: "/v1/context/prepare",
        REMEMBER_ID: "/v1/memory/remember",
    }
    for node_id, suffix in expected_paths.items():
        data = nodes[node_id]["data"]
        if data["type"] != "http-request" or data["method"] != "post":
            fail(f"node {node_id} must be POST http-request")
        if not str(data["url"]).endswith(suffix):
            fail(f"node {node_id} URL does not end with {suffix}: {data['url']}")
        if data["authorization"]["type"] != "no-auth":
            fail(f"node {node_id} must default to no-auth")
        if "{{#env.POWERCONTEXT_URL#}}" not in data["url"]:
            fail(f"node {node_id} URL is not bound to the env placeholder")

    model = nodes["1007"]["data"]["model"]
    if model["provider"] != "langgenius/openai/openai" or model["name"] != "gpt-4o-mini":
        fail("model placeholder changed; keep the documented stand-in and rebind after import")

    outgoing: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        outgoing.setdefault(edge["source"], []).append((edge["sourceHandle"], edge["target"]))

    def reachable(start: str, handle: str | None = None) -> set[str]:
        seen: set[str] = set()
        stack = [start]
        first = True
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            for source_handle, target in outgoing.get(current, []):
                if first and handle is not None and source_handle != handle:
                    continue
                stack.append(target)
            first = False
        return seen

    # Walk only the remember branch by following the true handle first, then any handle.
    true_targets = [target for handle, target in outgoing.get("1009", []) if handle == "true"]
    false_targets = [target for handle, target in outgoing.get("1009", []) if handle == "false"]
    if true_targets != [REMEMBER_ID]:
        fail(f"true branch should remember, got {true_targets}")
    if false_targets != ["1012"]:
        fail(f"false branch should answer without writing, got {false_targets}")
    if "1011" not in {target for _, target in outgoing.get(REMEMBER_ID, [])}:
        fail("remember node must reach an answer")

    functions = code_functions(workflow)
    for node_id, function in functions.items():
        data = nodes[node_id]["data"]
        declared = set(data["outputs"])
        arg_names = [item["variable"] for item in data["variables"]]
        sample = {
            "scope_id": "scp_example",
            "body": "{}",
            "text": '{"reply":"好。","should_remember":false,"memory_kind":"","memory_summary":"","reason":""}',
        }
        result = function(**{name: sample[name] for name in arg_names})
        if set(result) != declared:
            fail(f"node {node_id} returns {sorted(result)} but declares {sorted(declared)}")

    built = functions[BUILD_ID]("scp_example")
    search_body = json.loads(built["search_body"])
    prepare_body = json.loads(built["prepare_body"])
    if search_body != {"scope_id": "scp_example", "query": "仇账", "limit": 10, "mode": "fts"}:
        fail(f"unexpected search body {search_body}")
    if prepare_body != {"scope_id": "scp_example", "query": "仇账", "max_bytes": 4000}:
        fail(f"unexpected prepare body {prepare_body}")
    for payload in (search_body, prepare_body):
        if set(payload) - {"scope_id", "query", "limit", "mode", "max_bytes"}:
            fail("recall body has fields outside the published schema")

    empty = functions[LEDGER_ID]('{"mode":"text","hits":[]}')
    if empty["hit_count"] != "0" or "空" not in empty["ledger"]:
        fail("empty search should produce an explicit empty ledger")
    hit = {
        "mode": "text",
        "hits": [
            {
                "memory": {
                    "artifact": {"family": "atomic-memory", "artifact_id": "art_1", "revision": 1},
                    "kind": "grudge",
                    "text": "仇账：玩家把盐罐换成糖，毁了炖菜。",
                    "state": "active",
                    "state_version": 0,
                    "merged_into_id": None,
                },
                "score": 0.01,
                "matched_by": ["text"],
            },
            {
                "memory": {
                    "artifact": {"family": "atomic-memory", "artifact_id": "art_old", "revision": 1},
                    "kind": "grudge",
                    "text": "仇账：这条已经忘掉。",
                    "state": "forgotten",
                    "state_version": 1,
                    "merged_into_id": None,
                },
                "score": 0.01,
                "matched_by": ["text"],
            },
        ],
    }
    ledger = functions[LEDGER_ID](json.dumps(hit, ensure_ascii=False))
    if ledger["hit_count"] != "1" or "盐罐" not in ledger["ledger"] or "忘掉" in ledger["ledger"]:
        fail(f"ledger parser dropped or kept the wrong hit: {ledger}")

    ready = functions[PACK_ID](
        json.dumps(
            {
                "schema": "powercontext.prepared-context.v1",
                "status": "ready",
                "content": "BEGIN 炖菜 END",
                "content_bytes": 12,
            },
            ensure_ascii=False,
        )
    )
    if ready["prepare_status"] != "ready" or "炖菜" not in ready["prepared"]:
        fail("prepare parser missed ready content")
    empty_prepare = functions[PACK_ID](
        '{"schema":"powercontext.prepared-context.v1","status":"empty","content":null,"content_bytes":0}'
    )
    if empty_prepare["prepare_status"] != "empty" or empty_prepare["prepared"].strip() == "":
        fail("empty prepare should stay explicit")

    grudge_json = json.dumps(
        {
            "reply": "盐换成糖？今晚的麦酒三倍铜子。",
            "should_remember": True,
            "memory_kind": "grudge",
            "memory_summary": "把盐罐换成糖，毁了当晚的炖菜还当众取笑",
            "reason": "玩家当众恶作剧",
        },
        ensure_ascii=False,
    )
    decided = functions[DECIDE_ID](grudge_json, "scp_example")
    if decided["should_remember"] != "yes" or decided["memory_kind"] != "grudge":
        fail(f"grudge decision failed: {decided}")
    remembered = json.loads(decided["remember_body"])
    if set(remembered) != {"scope_id", "kind", "text", "reason"}:
        fail(f"remember body keys {set(remembered)}")
    if remembered["kind"] != "grudge" or "仇账：" not in remembered["text"] or "盐罐" not in remembered["text"]:
        fail("remember text lost the ledger marker or the prank")
    if len(remembered["text"].encode("utf-8")) > 8192 or len(remembered["reason"]) > 512:
        fail("remember body exceeds the published limits")

    order_json = json.dumps(
        {
            "reply": "麦酒一杯一个铜子。",
            "should_remember": False,
            "memory_kind": "",
            "memory_summary": "",
            "reason": "只是点单",
        },
        ensure_ascii=False,
    )
    order = functions[DECIDE_ID](order_json, "scp_example")
    if order["should_remember"] != "no" or order["remember_body"] != "":
        fail("an ordinary order must not write memory")

    amends = functions[DECIDE_ID](
        json.dumps(
            {
                "reply": "铜子我收下了。",
                "should_remember": True,
                "memory_kind": "atonement",
                "memory_summary": "当面道歉并赔了炖菜的铜子",
                "reason": "玩家赔罪",
            },
            ensure_ascii=False,
        ),
        "scp_example",
    )
    amends_body = json.loads(amends["remember_body"])
    if amends_body["kind"] != "atonement" or "赔罪" not in amends_body["text"]:
        fail("atonement memory was not built")

    broken = functions[DECIDE_ID]("老疤今天不想说话", "scp_example")
    if broken["should_remember"] != "no" or "没听清" not in broken["reply"]:
        fail("unparseable model output should not write memory")

    print("DSL offline checks passed")
    print(f"app={app['name']} mode={app['mode']} version={workflow['version']}")
    print("http=" + ", ".join(expected_paths[node_id] for node_id in (SEARCH_ID, PREPARE_ID, REMEMBER_ID)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dry-run the PowerContext HTTP contract used by the tavern Chatflow.

Verified against a local Server started from GitHub master
(package 1.4.2.dev4, OpenAPI info.version 1.4.1):

  GET  /health/live
  GET  /health/ready
  GET  /v1/server-info
  POST /v1/scopes
  POST /v1/memory/remember
  POST /v1/memory/search
  POST /v1/context/prepare

Request bodies for search, prepare, and remember are built by the Code
nodes in the DSL. This script does not send expected_revision.

Authentication is off on the default loopback Server. When POWERCONTEXT_TOKEN
is set, requests send Authorization: Bearer. The token is never written to
the evidence file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dsl_nodes import code_functions, load_workflow

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "evidence" / "powercontext-contract.json"

DEMO_KEY = "rust-anchor-traveler-demo"
CONTRACT_KEY = "rust-anchor-contract-sample"
DEMO_TITLE = "锈锚酒馆-旅人演示"
DEMO_SUMMARY = "记仇的酒馆老板演示 scope，保存玩家对老疤的仇账。"

GRUDGE_SUMMARY = "把盐罐换成糖，毁了当晚的炖菜还当众取笑"
ATONEMENT_SUMMARY = "当面道歉并赔了炖菜的铜子"


def post_json(base: str, path: str, payload: dict[str, Any], token: str) -> tuple[int, dict[str, Any]]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"PowerContext {path} failed with HTTP {error.code}: {detail}") from error


def get_json(base: str, path: str, token: str) -> dict[str, Any]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(base.rstrip("/") + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise SystemExit(f"{path} returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise SystemExit(
            "PowerContext is not reachable at "
            f"{base}. Start it with the steps in dify/RUN.md and retry.\n{error}"
        ) from error


def create_scope(base: str, token: str, idempotency_key: str, title: str) -> dict[str, Any]:
    status, body = post_json(
        base,
        "/v1/scopes",
        {"title": title, "summary": DEMO_SUMMARY, "idempotency_key": idempotency_key},
        token,
    )
    if status != 201 or not body.get("scope_id"):
        raise SystemExit(f"create scope returned HTTP {status}: {body}")
    return body


def search(functions: dict[str, Any], base: str, token: str, scope_id: str, query: str, limit: int = 10) -> dict[str, Any]:
    body = json.loads(functions["1002"](scope_id)["search_body"])
    body["query"] = query
    body["limit"] = limit
    status, response = post_json(base, "/v1/memory/search", body, token)
    if status != 200:
        raise SystemExit(f"search returned HTTP {status}")
    return {"request": body, "response": response}


def prepare(functions: dict[str, Any], base: str, token: str, scope_id: str, query: str) -> dict[str, Any]:
    body = json.loads(functions["1002"](scope_id)["prepare_body"])
    body["query"] = query
    status, response = post_json(base, "/v1/context/prepare", body, token)
    if status != 200:
        raise SystemExit(f"prepare returned HTTP {status}")
    return {"request": body, "response": response}


def remember_from_model(
    functions: dict[str, Any],
    base: str,
    token: str,
    scope_id: str,
    model_json: dict[str, Any],
) -> dict[str, Any]:
    decision = functions["1008"](json.dumps(model_json, ensure_ascii=False), scope_id)
    if decision["should_remember"] != "yes":
        raise SystemExit(f"DSL declined to remember: {decision}")
    payload = json.loads(decision["remember_body"])
    status, response = post_json(base, "/v1/memory/remember", payload, token)
    if status != 200:
        raise SystemExit(f"remember returned HTTP {status}")
    return {"decision": decision, "request": payload, "response": response}


def hit_texts(response: dict[str, Any]) -> list[str]:
    texts = []
    for hit in response.get("hits") or []:
        memory = hit.get("memory") or {}
        if memory.get("state") not in (None, "", "active"):
            continue
        text = memory.get("text") or ""
        if text:
            texts.append(text)
    return texts


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def init_scope(base: str, token: str) -> None:
    scope = create_scope(base, token, DEMO_KEY, DEMO_TITLE)
    print("Created or reused the playthrough scope. It does not write a grudge.")
    print(f"POWERCONTEXT_SCOPE_ID={scope['scope_id']}")
    print("Paste that id into the Dify environment variable POWERCONTEXT_SCOPE_ID.")
    print(f"idempotency_key={DEMO_KEY}")


def run_contract(base: str, token: str, idempotency_key: str, expect_empty_before: bool, evidence_path: Path) -> None:
    functions = code_functions(load_workflow())
    live = get_json(base, "/health/live", token)
    ready = get_json(base, "/health/ready", token)
    info = get_json(base, "/v1/server-info", token)
    require(live.get("status") == "ok", f"liveness is {live}")
    require(ready.get("status") in ("ready", "degraded"), f"readiness is {ready}")

    scope = create_scope(base, token, idempotency_key, "锈锚酒馆-契约样例")
    scope_id = scope["scope_id"]

    before = search(functions, base, token, scope_id, "仇账")
    if expect_empty_before:
        require(before["response"].get("hits") == [], "expected an empty ledger before the first write")

    grudge = remember_from_model(
        functions,
        base,
        token,
        scope_id,
        {
            "reply": "盐换成糖？炖菜毁了你还笑。这一杯麦酒三倍铜子，赊账免谈。",
            "should_remember": True,
            "memory_kind": "grudge",
            "memory_summary": GRUDGE_SUMMARY,
            "reason": "玩家当众把盐换成糖",
        },
    )
    record = (grudge["response"].get("records") or [None])[0]
    require(isinstance(record, dict), "remember response has no records")
    require(record.get("state") == "active", record)
    require(record.get("kind") == "grudge", record)
    artifact = record.get("artifact") or {}
    require(artifact.get("family") == "atomic-memory", artifact)
    require(int(artifact.get("revision") or 0) >= 1, artifact)
    require("仇账：" in record.get("text", "") and "炖菜" in record.get("text", ""), record.get("text"))
    require("expected_revision" not in grudge["request"], "remember request included expected_revision")

    ledger_search = search(functions, base, token, scope_id, "仇账")
    stew_search = search(functions, base, token, scope_id, "炖菜")
    jar_search = search(functions, base, token, scope_id, "盐罐")
    salt_char_search = search(functions, base, token, scope_id, "盐")
    ale_search = search(functions, base, token, scope_id, "麦酒")
    for name, item in (("仇账", ledger_search), ("炖菜", stew_search), ("盐罐", jar_search)):
        require(item["response"].get("mode") == "text", f"{name} search mode was {item['response'].get('mode')}")
        require(any("炖菜" in text for text in hit_texts(item["response"])), f"{name} search did not return the grudge")
    require(ale_search["response"].get("hits") == [], "麦酒 must not match a ledger that never mentions ale")

    prepared = prepare(functions, base, token, scope_id, "仇账")
    ale_context = prepare(functions, base, token, scope_id, "麦酒")
    prepared_body = prepared["response"]
    require(prepared_body.get("schema") == "powercontext.prepared-context.v1", prepared_body)
    require(prepared_body.get("status") == "ready", prepared_body)
    require(isinstance(prepared_body.get("content"), str) and "炖菜" in prepared_body["content"], "prepare missed the grudge")
    require(prepared_body.get("content_bytes", 0) > 0, prepared_body)
    require(ale_context["response"].get("status") == "empty", ale_context["response"])
    require(ale_context["response"].get("content") is None, ale_context["response"])

    packed = functions["1006"](json.dumps(prepared_body, ensure_ascii=False))
    ledger = functions["1004"](json.dumps(ledger_search["response"], ensure_ascii=False))
    require(ledger["hit_count"] != "0", ledger)
    require("炖菜" in ledger["ledger"], ledger)
    require(packed["prepare_status"] == "ready" and "炖菜" in packed["prepared"], packed)

    order = functions["1008"](
        json.dumps(
            {
                "reply": "麦酒一杯一个铜子。新面孔，手老实点。",
                "should_remember": False,
                "memory_kind": "",
                "memory_summary": "",
                "reason": "只是点单",
            },
            ensure_ascii=False,
        ),
        scope_id,
    )
    require(order["should_remember"] == "no" and order["remember_body"] == "", order)

    atonement = remember_from_model(
        functions,
        base,
        token,
        scope_id,
        {
            "reply": "铜子我收下了。炖菜的事先翻篇，罐子再碰一下，仇账重开。",
            "should_remember": True,
            "memory_kind": "atonement",
            "memory_summary": ATONEMENT_SUMMARY,
            "reason": "玩家赔罪",
        },
    )
    both = search(functions, base, token, scope_id, "仇账")
    texts = hit_texts(both["response"])
    require(any("恶作剧" in text for text in texts), texts)
    require(any("赔罪" in text for text in texts), texts)

    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "No bearer token is stored. Scope ids exist only on the Server that produced this file.",
        "server": {
            "base_url": base,
            "health_live": live,
            "health_ready": ready,
            "package_version": info.get("package_version"),
            "api_contract_version": info.get("api_contract_version"),
            "product": info.get("product"),
        },
        "scope": scope,
        "idempotency_key": idempotency_key,
        "steps": {
            "search_before_write": before,
            "remember_grudge": {
                "request": grudge["request"],
                "response": grudge["response"],
            },
            "search_ledger_marker": ledger_search,
            "search_stew": stew_search,
            "search_salt_jar": jar_search,
            "search_single_character_salt": salt_char_search,
            "search_ale_word_absent_from_memory": ale_search,
            "prepare_ledger_marker": prepared,
            "prepare_ale_word": ale_context,
            "ledger_text_passed_to_model": ledger,
            "prepared_text_passed_to_model": packed,
            "ordinary_order_does_not_write": order,
            "remember_atonement": {
                "request": atonement["request"],
                "response": atonement["response"],
            },
            "search_after_atonement": both,
        },
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PowerContext contract dry-run passed")
    print(f"scope_id={scope_id}")
    print(f"evidence={evidence_path}")
    print(
        "Observed: request mode fts returns response mode text; "
        f"single-character 盐 hits={len(salt_char_search['response'].get('hits') or [])}; "
        "炖菜 and 仇账 hit; 麦酒 search and prepare stay empty."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--token", default=os.environ.get("POWERCONTEXT_TOKEN", ""))
    parser.add_argument("--init-scope", action="store_true", help="create the empty playthrough scope and print its id")
    parser.add_argument("--idempotency-key", default=CONTRACT_KEY)
    parser.add_argument("--expect-empty-before", action="store_true")
    parser.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
    args = parser.parse_args()
    if args.init_scope:
        init_scope(args.url, args.token)
        return
    run_contract(args.url, args.token, args.idempotency_key, args.expect_empty_before, args.evidence)


if __name__ == "__main__":
    main()

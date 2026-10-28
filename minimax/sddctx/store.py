from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sddctx.config import Config
from sddctx.embeddings import DIM, embed_text

_DEF = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_query_log(cfg: Config, record: dict[str, Any]) -> None:
    cfg.evidence.mkdir(parents=True, exist_ok=True)
    record = {"ts": _now(), **record}
    path = cfg.evidence / "seekdb_queries.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _client(cfg: Config):
    import pyseekdb

    cfg.seekdb_path.mkdir(parents=True, exist_ok=True)
    return pyseekdb.Client(path=str(cfg.seekdb_path), database=cfg.seekdb_database)


def _collection(cfg: Config, client):
    from pyseekdb import HNSWConfiguration

    configuration = HNSWConfiguration(dimension=DIM, distance="cosine")
    if client.has_collection(cfg.collection):
        return client.get_collection(cfg.collection, embedding_function=None)
    return client.get_or_create_collection(
        cfg.collection,
        embedding_function=None,
        configuration=configuration,
    )


def _chunk_id(kind: str, path: str, symbol: str) -> str:
    raw = f"{kind}\n{path}\n{symbol}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


def _pack(path: str, symbol: str, kind: str, role: str, body: str) -> str:
    header = f"path: {path}\nsymbol: {symbol}\nkind: {kind}\nrole: {role}\n"
    return header + "\n" + body.strip() + "\n"


def _split_spec(text: str) -> list[tuple[str, str]]:
    chunks: list[tuple[str, list[str]]] = []
    title = "概述"
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if buffer:
                chunks.append((title, buffer))
            title = line[3:].strip() or "概述"
            buffer = [line]
        else:
            buffer.append(line)
    if buffer:
        chunks.append((title, buffer))
    return [(title, "\n".join(body).strip() + "\n") for title, body in chunks]


def _role(kind: str, path: Path) -> str:
    name = path.name
    if kind == "test":
        if "test_feature_" in name:
            return "feature"
        if "test_regression_" in name:
            return "regression"
        return "decoy"
    if "parking" in name:
        return "decoy"
    if kind == "code":
        return "implementation"
    return "spec"


def _code_symbol(text: str, fallback: str) -> str:
    names = _DEF.findall(text)
    if "overtime_pay" in names:
        return "overtime_pay"
    return names[0] if names else fallback


def _test_symbol(text: str, fallback: str) -> str:
    names = _DEF.findall(text)
    tests = [name for name in names if name.startswith("test_")]
    return tests[0] if tests else fallback


def iter_chunks(project: Path) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    mapping = (("docs", "spec", "*.md"), ("src", "code", "*.py"), ("tests", "test", "*.py"))
    for folder, kind, pattern in mapping:
        directory = project / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob(pattern)):
            relative = path.relative_to(project).as_posix()
            text = path.read_text(encoding="utf-8")
            role = _role(kind, path)
            if kind == "spec":
                for symbol, body in _split_spec(text):
                    chunks.append(
                        {
                            "id": _chunk_id(kind, relative, symbol),
                            "path": relative,
                            "symbol": symbol,
                            "kind": kind,
                            "role": role,
                            "document": _pack(relative, symbol, kind, role, body),
                        }
                    )
                continue
            symbol = _code_symbol(text, path.stem) if kind == "code" else _test_symbol(text, path.stem)
            chunks.append(
                {
                    "id": _chunk_id(kind, relative, symbol),
                    "path": relative,
                    "symbol": symbol,
                    "kind": kind,
                    "role": role,
                    "document": _pack(relative, symbol, kind, role, text),
                }
            )
    return chunks


def _flatten(results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = results.get("ids") or []
    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    distances = results.get("distances") or []
    if ids and isinstance(ids[0], list):
        ids = ids[0]
        documents = documents[0] if documents else []
        metadatas = metadatas[0] if metadatas else []
        distances = distances[0] if distances else []
    rows = []
    for index, item_id in enumerate(ids):
        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        distance = distances[index] if index < len(distances) else None
        rows.append(
            {
                "id": item_id,
                "document": documents[index] if index < len(documents) else "",
                "metadata": dict(metadata),
                "distance": None if distance is None else float(distance),
            }
        )
    return rows


def _log_rows(cfg: Config, op: str, detail: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    append_query_log(
        cfg,
        {
            "op": op,
            "detail": detail,
            "ids": [row["id"] for row in rows],
            "hits": [
                {
                    "id": row["id"],
                    "distance": row["distance"],
                    "metadata": row["metadata"],
                    "document": row["document"][:2000],
                }
                for row in rows
            ],
        },
    )


def import_materials(cfg: Config) -> dict[str, Any]:
    if not cfg.project.is_dir():
        raise SystemExit(f"project not found: {cfg.project}")
    chunks = iter_chunks(cfg.project)
    if not chunks:
        raise SystemExit(f"no materials under {cfg.project}")
    client = _client(cfg)
    collection = _collection(cfg, client)
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["document"] for chunk in chunks]
    metadatas = [
        {"path": chunk["path"], "symbol": chunk["symbol"], "kind": chunk["kind"], "role": chunk["role"]}
        for chunk in chunks
    ]
    embeddings = [embed_text(document) for document in documents]
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    count = int(collection.count())
    if count:
        existing = collection.get(limit=count, include=[])
        old_ids = existing.get("ids") or []
        stale = [item_id for item_id in old_ids if item_id not in set(ids)]
        if stale:
            collection.delete(ids=stale)
    collection.refresh_index()
    task = cfg.task_file.read_text(encoding="utf-8") if cfg.task_file.is_file() else "节日加班 overtime_pay"
    probe = collection.query(
        query_embeddings=[embed_text(task)],
        n_results=min(8, max(int(collection.count()), 1)),
        include=["documents", "metadatas", "distances"],
    )
    rows = _flatten(probe)
    _log_rows(cfg, "query", {"route": "import_readback", "n_results": len(rows)}, rows)
    spec_rows = _flatten(
        collection.get(where={"kind": "spec"}, include=["documents", "metadatas"], limit=50)
    )
    _log_rows(cfg, "get", {"where": {"kind": "spec"}}, spec_rows)
    summary = {
        "collection": cfg.collection,
        "count": int(collection.count()),
        "upserted": len(ids),
        "seekdb_path": str(cfg.seekdb_path),
    }
    append_query_log(cfg, {"op": "import", "detail": summary, "ids": ids, "hits": []})
    return summary


def search_materials(cfg: Config, task: str) -> list[dict[str, Any]]:
    client = _client(cfg)
    if not client.has_collection(cfg.collection):
        raise SystemExit("seekdb collection is missing; run import first")
    collection = _collection(cfg, client)
    count = int(collection.count())
    if count == 0:
        raise SystemExit("seekdb collection is empty; run import first")
    embedding = embed_text(task)
    limit = min(8, count)
    merged: dict[str, dict[str, Any]] = {}

    def absorb(op: str, detail: dict[str, Any], rows: list[dict[str, Any]]) -> None:
        _log_rows(cfg, op, detail, rows)
        for rank, row in enumerate(rows):
            current = merged.get(row["id"])
            if current is None or rank < current["rank"]:
                merged[row["id"]] = {**row, "rank": rank}

    absorb(
        "query",
        {"route": "vector_all"},
        _flatten(
            collection.query(
                query_embeddings=[embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
        ),
    )
    for kind in ("spec", "code", "test"):
        try:
            rows = _flatten(
                collection.query(
                    query_embeddings=[embedding],
                    n_results=limit,
                    where={"kind": kind},
                    include=["documents", "metadatas", "distances"],
                )
            )
        except Exception as exc:  # seekdb filter errors should not hide the vector route
            append_query_log(cfg, {"op": "query", "detail": {"route": kind, "error": str(exc)}, "ids": [], "hits": []})
            continue
        absorb("query", {"route": f"vector_{kind}", "where": {"kind": kind}}, rows)

    for phrase in ("节日加班", "overtime_pay", "HOLIDAY_MULTIPLIER"):
        try:
            hybrid = collection.hybrid_search(
                query={"where_document": {"$contains": phrase}, "n_results": limit},
                knn={"query_embeddings": [embedding], "n_results": limit},
                rank={"rrf": {}},
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            append_query_log(
                cfg,
                {"op": "hybrid_search", "detail": {"contains": phrase, "error": str(exc)}, "ids": [], "hits": []},
            )
            continue
        absorb("hybrid_search", {"contains": phrase, "rank": "rrf"}, _flatten(hybrid))
    return list(merged.values())

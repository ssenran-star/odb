# Copyright (c) 2026 OceanBase.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Propagate source availability through a per-scope dependency graph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from powercontext.artifacts import ArtifactRef
from powercontext.builtin.artifacts.memory.models import MemoryCitation
from powercontext.builtin.persistence.tables import (
    SOURCE_LIFECYCLE_EVENTS_TABLE,
    SOURCE_LIFECYCLE_NODES_TABLE,
)
from powercontext.sources.models import SourceRef

Purpose = Literal["generation", "audit"]


class SourceLifecycleError(ValueError):
    """A lifecycle registration, event, or resolution violated the scope graph."""


class SourceLifecycleEvent(BaseModel):
    """One ordered availability change for a registered source node."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    revision: int
    sequence: int
    available: bool
    reason: str

    @field_validator("node_id", "reason")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not isinstance(value, str) or value == "" or value.strip() == "" or value != value.strip():
            raise ValueError("must be a non-blank trimmed string")  # noqa: TRY003
        return value

    @field_validator("revision", "sequence", mode="before")
    @classmethod
    def validate_positive(cls, value: Any) -> Any:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("must be a positive integer")  # noqa: TRY003
        return value

    @field_validator("available", mode="before")
    @classmethod
    def validate_bool(cls, value: Any) -> Any:
        if not isinstance(value, bool):
            raise ValueError("available must be a boolean")  # noqa: TRY003
        return value


@dataclass
class _Node:
    node_id: str
    kind: str
    revision: int
    policy: str | None
    reference: SourceRef | MemoryCitation | ArtifactRef
    parents: tuple[str, ...]
    available: bool
    ordinal: int


class SourceLifecycleApplication:
    """Expose one lifecycle graph for each scope."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime

    def for_scope(self, scope_id: str, /) -> ScopedSourceLifecycle:
        return ScopedSourceLifecycle(self._runtime, scope_id)


class ScopedSourceLifecycle:
    """Register dependencies and apply source availability inside one scope."""

    def __init__(self, runtime: Any, scope_id: str) -> None:
        self._runtime = runtime
        self.scope_id = scope_id

    async def register_source(self, node_id: str, reference: SourceRef, /, *, revision: int) -> None:
        _positive(revision, "revision")
        await self._register(node_id, "source", revision, None, reference, ())

    async def register_memory(
        self,
        node_id: str,
        citation: MemoryCitation,
        /,
        *,
        parents: tuple[str, ...],
        policy: str,
    ) -> None:
        await self._register(node_id, "memory", 1, policy, citation, parents)

    async def register_topic(
        self,
        node_id: str,
        reference: ArtifactRef,
        /,
        *,
        parents: tuple[str, ...],
        policy: str,
    ) -> None:
        await self._register(node_id, "topic", 1, policy, reference, parents)

    async def apply(self, event: SourceLifecycleEvent, /) -> list[str]:
        if not isinstance(event, SourceLifecycleEvent):
            raise SourceLifecycleError("lifecycle event is invalid")
        async with _database(self._runtime).transaction() as connection:
            nodes = await _load_nodes(connection, self.scope_id)
        by_id = {node.node_id: node for node in nodes}
        node = by_id.get(event.node_id)
        if node is None or node.kind != "source":
            raise SourceLifecycleError("lifecycle event does not name a registered source")
        if event.revision != node.revision:
            raise SourceLifecycleError("lifecycle event revision does not match the source")
        latest = await self._latest_event(event.node_id)
        if latest is not None:
            if event.sequence < latest.sequence or (
                event.sequence == latest.sequence and not _same_event(event, latest)
            ):
                raise SourceLifecycleError("lifecycle event sequence is stale or conflicting")
            if event.sequence == latest.sequence:
                return _active_ids(nodes)
        node.available = event.available
        _recompute(nodes)
        await self._sync_memory(nodes, event.reason)
        async with _database(self._runtime).transaction() as connection:
            await _store_availability(connection, self.scope_id, nodes)
            await connection.execute(
                insert(SOURCE_LIFECYCLE_EVENTS_TABLE).values(
                    scope_id=self.scope_id,
                    node_id=event.node_id,
                    sequence=event.sequence,
                    revision=event.revision,
                    available=event.available,
                    reason=event.reason,
                )
            )
        return _active_ids(nodes)

    async def resolve(self, node_id: str, /, *, purpose: Purpose) -> SourceRef | MemoryCitation | ArtifactRef:
        if purpose not in {"generation", "audit"}:
            raise SourceLifecycleError("lifecycle purpose is invalid")
        async with _database(self._runtime).transaction() as connection:
            nodes = await _load_nodes(connection, self.scope_id)
        match = next((node for node in nodes if node.node_id == node_id), None)
        if match is None:
            raise SourceLifecycleError("lifecycle node was not found")
        if purpose == "generation" and not match.available:
            raise SourceLifecycleError("lifecycle node is unavailable for generation")
        return match.reference

    async def _register(
        self,
        node_id: str,
        kind: str,
        revision: int,
        policy: str | None,
        reference: SourceRef | MemoryCitation | ArtifactRef,
        parents: tuple[str, ...],
    ) -> None:
        node_id = _node_id(node_id)
        parent_ids = _parents(node_id, parents, required=kind != "source")
        if kind != "source":
            if policy not in {"all", "any"}:
                raise SourceLifecycleError("lifecycle policy must be all or any")
        async with _database(self._runtime).transaction() as connection:
            nodes = await _load_nodes(connection, self.scope_id)
            by_id = {node.node_id: node for node in nodes}
            if any(parent not in by_id for parent in parent_ids):
                raise SourceLifecycleError("lifecycle parent was not found")
            encoded = _dump_reference(reference)
            existing = by_id.get(node_id)
            if existing is not None:
                if (
                    existing.kind != kind
                    or existing.revision != revision
                    or existing.policy != policy
                    or existing.parents != parent_ids
                    or _dump_reference(existing.reference) != encoded
                ):
                    raise SourceLifecycleError("lifecycle node is already bound")
            else:
                available = True if kind == "source" else _supported(parent_ids, policy or "all", by_id)
                ordinal = (nodes[-1].ordinal + 1) if nodes else 1
                await connection.execute(
                    insert(SOURCE_LIFECYCLE_NODES_TABLE).values(
                        scope_id=self.scope_id,
                        node_id=node_id,
                        kind=kind,
                        revision=revision,
                        policy=policy,
                        reference_json=encoded,
                        parents_json=json.dumps(list(parent_ids)),
                        available=available,
                        ordinal=ordinal,
                    )
                )
                nodes.append(
                    _Node(node_id, kind, revision, policy, reference, parent_ids, available, ordinal)
                )
        await self._sync_memory(nodes, "source lifecycle")

    async def _latest_event(self, node_id: str) -> SourceLifecycleEvent | None:
        table = SOURCE_LIFECYCLE_EVENTS_TABLE
        async with _database(self._runtime).transaction() as connection:
            row = (
                await connection.execute(
                    select(table)
                    .where(table.c.scope_id == self.scope_id, table.c.node_id == node_id)
                    .order_by(table.c.sequence.desc())
                    .limit(1)
                )
            ).mappings().one_or_none()
        if row is None:
            return None
        return SourceLifecycleEvent(
            node_id=str(row["node_id"]),
            revision=int(row["revision"]),
            sequence=int(row["sequence"]),
            available=bool(row["available"]),
            reason=str(row["reason"]),
        )

    async def _sync_memory(self, nodes: list[_Node], reason: str) -> None:
        memories = [node for node in nodes if node.kind == "memory"]
        if not memories:
            return
        async with self._runtime._context(self.scope_id) as context:
            service = context.artifacts.memory
            for node in memories:
                citation = node.reference
                if not isinstance(citation, MemoryCitation):
                    continue
                head = await service.head(citation.memory_ref.artifact_id)
                current = next(
                    (entry for entry in await service.entries(head) if entry.entry_id == citation.entry_id),
                    None,
                )
                if current is None:
                    raise SourceLifecycleError("lifecycle memory entry was not found")
                if node.available:
                    await service.reactivate(head, entries=(current,), reason=reason)
                else:
                    await service.forget(head, entries=(current,), reason=reason)


def _database(runtime: Any):
    database = getattr(getattr(runtime, "_provider", None), "database", None)
    if database is None:
        raise SourceLifecycleError("lifecycle storage is unavailable")
    return database


async def unavailable_topic_artifact_ids(runtime: Any, scope_id: str) -> frozenset[str]:
    """Return topic artifact ids hidden from generation in one scope."""

    database = getattr(getattr(runtime, "_provider", None), "database", None)
    if database is None:
        return frozenset()
    table = SOURCE_LIFECYCLE_NODES_TABLE
    async with database.transaction() as connection:
        rows = (
            await connection.execute(
                select(table.c.reference_json).where(
                    table.c.scope_id == scope_id,
                    table.c.kind == "topic",
                    table.c.available.is_(False),
                )
            )
        ).scalars()
    hidden: set[str] = set()
    for payload in rows:
        reference = json.loads(payload)
        artifact_id = reference.get("artifact_id")
        if isinstance(artifact_id, str):
            hidden.add(artifact_id)
    return frozenset(hidden)


async def _load_nodes(connection: AsyncConnection, scope_id: str) -> list[_Node]:
    table = SOURCE_LIFECYCLE_NODES_TABLE
    rows = (
        await connection.execute(
            select(table).where(table.c.scope_id == scope_id).order_by(table.c.ordinal, table.c.node_id)
        )
    ).mappings()
    return [_decode_node(row) for row in rows]


def _decode_node(row: Any) -> _Node:
    kind = str(row["kind"])
    payload = json.loads(row["reference_json"])
    if kind == "source":
        reference: SourceRef | MemoryCitation | ArtifactRef = SourceRef.model_validate(payload)
    elif kind == "memory":
        reference = MemoryCitation.model_validate(payload)
    else:
        reference = ArtifactRef.model_validate(payload)
    parents = tuple(json.loads(row["parents_json"]))
    return _Node(
        node_id=str(row["node_id"]),
        kind=kind,
        revision=int(row["revision"]),
        policy=None if row["policy"] is None else str(row["policy"]),
        reference=reference,
        parents=parents,
        available=bool(row["available"]),
        ordinal=int(row["ordinal"]),
    )


async def _store_availability(connection: AsyncConnection, scope_id: str, nodes: list[_Node]) -> None:
    table = SOURCE_LIFECYCLE_NODES_TABLE
    for node in nodes:
        await connection.execute(
            update(table)
            .where(table.c.scope_id == scope_id, table.c.node_id == node.node_id)
            .values(available=node.available)
        )


def _recompute(nodes: list[_Node]) -> None:
    available = {node.node_id: node.available for node in nodes if node.kind == "source"}
    for node in nodes:
        if node.kind == "source":
            continue
        flags = [available[parent] for parent in node.parents]
        node.available = all(flags) if node.policy == "all" else any(flags)
        available[node.node_id] = node.available


def _supported(parents: tuple[str, ...], policy: str, nodes: dict[str, _Node]) -> bool:
    flags = [nodes[parent].available for parent in parents]
    return all(flags) if policy == "all" else any(flags)


def _active_ids(nodes: list[_Node]) -> list[str]:
    return sorted(node.node_id for node in nodes if node.available)


def _same_event(event: SourceLifecycleEvent, latest: SourceLifecycleEvent) -> bool:
    return (
        event.revision == latest.revision
        and event.available == latest.available
        and event.reason == latest.reason
        and event.node_id == latest.node_id
    )


def _dump_reference(reference: SourceRef | MemoryCitation | ArtifactRef) -> str:
    return json.dumps(reference.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def _node_id(value: str) -> str:
    if not isinstance(value, str) or value == "" or value.strip() == "" or value != value.strip():
        raise SourceLifecycleError("lifecycle node id must be a non-blank trimmed string")
    return value


def _parents(node_id: str, parents: tuple[str, ...], *, required: bool) -> tuple[str, ...]:
    if not isinstance(parents, tuple):
        raise SourceLifecycleError("lifecycle parents must be a tuple")
    if required and not parents:
        raise SourceLifecycleError("lifecycle node requires a parent")
    if not required and parents:
        raise SourceLifecycleError("lifecycle source cannot declare parents")
    normalized: list[str] = []
    for parent in parents:
        parent_id = _node_id(parent)
        if parent_id == node_id or parent_id in normalized:
            raise SourceLifecycleError("lifecycle parents must form a simple dependency")
        normalized.append(parent_id)
    return tuple(normalized)


def _positive(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SourceLifecycleError(f"lifecycle {label} must be a positive integer")


__all__ = [
    "SourceLifecycleApplication",
    "SourceLifecycleError",
    "SourceLifecycleEvent",
    "unavailable_topic_artifact_ids",
]

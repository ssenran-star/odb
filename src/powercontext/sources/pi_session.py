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

"""Capture one selected Pi session branch as immutable text evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict

from powercontext.limits import MAX_SOURCE_ID_LENGTH
from powercontext.sources.connectors import ConnectorRunCompletion, ConnectorRunSession, ConnectorRunStatus
from powercontext.sources.definitions import AdapterSourceDefinition, SourceDefinition
from powercontext.sources.models import Source, SourceMaterialization
from powercontext.sources.projections import TEXT_EVIDENCE_PROJECTION_KEY, TextEvidence

PI_EVENT_SOURCE_NAME = "pi-event"
PI_EVENT_SOURCE_VERSION = "1"
PI_SESSION_CONNECTOR_NAME = "pi-session-history"
PI_SESSION_CONNECTOR_VERSION = "1"


class PiSessionInput(BaseModel):
    """One complete Pi v3 JSONL session and the branch leaf to capture."""

    model_config = ConfigDict(extra="forbid")

    content: bytes
    leaf_id: str | None = None


class PiEventInput(BaseModel):
    """One visible event on the selected branch, with its original record."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    event_id: str
    parent_id: str | None
    event_type: str
    role: str
    content: str
    record: dict[str, Any]


class PiEventSource(Source):
    """Captured Pi event whose identity is the session id and event id."""

    source_id: str
    session_id: str
    event_id: str
    parent_id: str | None
    event_type: str
    role: str
    content: str
    record: dict[str, Any]


def parse_pi_session(value: PiSessionInput) -> tuple[PiEventInput, ...]:
    """Return visible events from the root to the selected leaf, or fail with no partial result."""

    return _parse_archive(value.content, value.leaf_id).branch


def pi_event_source_id(session_id: str, event_id: str) -> str:
    """Return a stable identity derived only from the session id and event id."""

    _require_identity(session_id, "session id")
    _require_identity(event_id, "event id")
    source_id = f"pi:{quote(session_id, safe='')}:{quote(event_id, safe='')}"
    if len(source_id) <= MAX_SOURCE_ID_LENGTH:
        return source_id
    digest = hashlib.sha256(f"{session_id}\0{event_id}".encode()).hexdigest()
    return f"pi:{digest}"


class PiEventSourceAdapter:
    """Resolve and read one captured Pi event."""

    input_class = PiEventInput
    name = PI_EVENT_SOURCE_NAME
    source_class = PiEventSource

    async def resolve(self, value: PiEventInput, /) -> PiEventSource:
        source_id = pi_event_source_id(value.session_id, value.event_id)
        return PiEventSource(
            name=source_id,
            definition_version=PI_EVENT_SOURCE_VERSION,
            materialization=SourceMaterialization.CAPTURED,
            source_id=source_id,
            session_id=value.session_id,
            event_id=value.event_id,
            parent_id=value.parent_id,
            event_type=value.event_type,
            role=value.role,
            content=value.content,
            record=value.record,
        )

    async def read(self, source: PiEventSource, /) -> PiEventInput:
        return PiEventInput(
            session_id=source.session_id,
            event_id=source.event_id,
            parent_id=source.parent_id,
            event_type=source.event_type,
            role=source.role,
            content=source.content,
            record=dict(source.record),
        )


class PiEventTextEvidenceProjection:
    """Project one captured Pi event as standard text evidence."""

    name = TEXT_EVIDENCE_PROJECTION_KEY.name
    version = TEXT_EVIDENCE_PROJECTION_KEY.version
    source_class = PiEventSource
    output_class: type[BaseModel] = TextEvidence

    def project(self, source: PiEventSource, /) -> TextEvidence:
        return TextEvidence(
            source_type=PI_EVENT_SOURCE_NAME,
            source_id=source.source_id,
            content=source.content,
            metadata={
                "session_id": source.session_id,
                "event_id": source.event_id,
                "parent_id": source.parent_id,
                "event_type": source.event_type,
                "role": source.role,
            },
        )


PI_EVENT_SOURCE_DEFINITION: SourceDefinition[PiEventInput, PiEventSource, PiEventInput] = AdapterSourceDefinition(
    PiEventSourceAdapter(),
    version=PI_EVENT_SOURCE_VERSION,
    projections=(PiEventTextEvidenceProjection(),),
)


class _ParsedSession:
    def __init__(self, branch: tuple[PiEventInput, ...], visible: tuple[PiEventInput, ...]) -> None:
        self.branch = branch
        self.visible = visible


class PiSessionConnector:
    """Import newly observed visible events on one selected Pi branch."""

    name = PI_SESSION_CONNECTOR_NAME
    version = PI_SESSION_CONNECTOR_VERSION
    source_definitions = frozenset({PI_EVENT_SOURCE_NAME})

    def __init__(self, path: str | Path, leaf_id: str | None = None) -> None:
        self._path = Path(path)
        self._leaf_id = leaf_id

    async def run(self, session: ConnectorRunSession, /) -> ConnectorRunCompletion:
        parsed = _parse_archive(self._path.read_bytes(), self._leaf_id)
        stored = _checkpoint_events(session.checkpoint)
        digests = { _event_key(event): _record_digest(event.record) for event in parsed.visible }
        for key, digest in digests.items():
            if key in stored and stored[key] != digest:
                raise ValueError("imported Pi event was rewritten")  # noqa: TRY003
        pending = [event for event in parsed.branch if _event_key(event) not in stored]
        for event in pending:
            await session.submit(pi_event_source_id(event.session_id, event.event_id), PI_EVENT_SOURCE_NAME, event)
        if not pending:
            checkpoint = session.checkpoint
        else:
            events = dict(stored)
            for event in pending:
                events[_event_key(event)] = digests[_event_key(event)]
            checkpoint = {"v": 1, "events": events}
        return ConnectorRunCompletion(status=ConnectorRunStatus.COMPLETE, checkpoint=checkpoint)


def _parse_archive(content: bytes, leaf_id: str | None) -> _ParsedSession:
    records = _decode_records(content)
    if not records:
        raise ValueError("Pi session archive is empty")  # noqa: TRY003
    session_id = _session_id(records[0])
    nodes: dict[str, dict[str, Any]] = {}
    parents: dict[str, str | None] = {}
    order: list[str] = []
    for record in records[1:]:
        event_id, parent_id = _graph_identity(record, nodes)
        nodes[event_id] = record
        parents[event_id] = parent_id
        order.append(event_id)
    if leaf_id is None:
        if not order:
            raise ValueError("Pi session does not contain a leaf")  # noqa: TRY003
        leaf_id = order[-1]
    elif leaf_id not in nodes:
        raise ValueError("Pi session leaf was not found")  # noqa: TRY003
    branch_ids = _ancestor_chain(leaf_id, parents)
    visible_by_id = {
        event_id: event
        for event_id in order
        if (event := _visible_event(session_id, nodes[event_id])) is not None
    }
    return _ParsedSession(
        branch=tuple(visible_by_id[event_id] for event_id in branch_ids if event_id in visible_by_id),
        visible=tuple(visible_by_id[event_id] for event_id in order if event_id in visible_by_id),
    )


def _decode_records(content: bytes) -> list[dict[str, Any]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("Pi session must be valid UTF-8") from error  # noqa: TRY003
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError("Pi session JSONL is malformed") from error  # noqa: TRY003
        if not isinstance(value, dict):
            raise ValueError("Pi session records must be JSON objects")  # noqa: TRY003
        records.append(value)
    return records


def _session_id(record: Mapping[str, Any]) -> str:
    if record.get("type") != "session" or type(record.get("version")) is not int or record.get("version") != 3:
        raise ValueError("Pi session header must be version 3")  # noqa: TRY003
    session_id = record.get("id")
    if not isinstance(session_id, str) or session_id.strip() == "":
        raise ValueError("Pi session id must be a non-empty string")  # noqa: TRY003
    return session_id


def _graph_identity(record: Mapping[str, Any], seen: Mapping[str, object]) -> tuple[str, str | None]:
    event_id = record.get("id")
    if not isinstance(event_id, str) or event_id.strip() == "":
        raise ValueError("Pi event id must be a non-empty string")  # noqa: TRY003
    if event_id in seen:
        raise ValueError("Pi event id must be unique")  # noqa: TRY003
    if "parentId" not in record:
        raise ValueError("Pi event parent is missing")  # noqa: TRY003
    parent_id = record.get("parentId")
    if parent_id is not None and not isinstance(parent_id, str):
        raise ValueError("Pi event parent is invalid")  # noqa: TRY003
    if parent_id == event_id or (parent_id is not None and parent_id not in seen):
        raise ValueError("Pi event parent was not found")  # noqa: TRY003
    if not isinstance(record.get("type"), str) or record.get("type") == "":
        raise ValueError("Pi event type is missing")  # noqa: TRY003
    return event_id, parent_id


def _ancestor_chain(leaf_id: str, parents: Mapping[str, str | None]) -> tuple[str, ...]:
    chain: list[str] = []
    seen: set[str] = set()
    current: str | None = leaf_id
    while current is not None:
        if current in seen:
            raise ValueError("Pi session branch contains a cycle")  # noqa: TRY003
        seen.add(current)
        chain.append(current)
        current = parents[current]
    chain.reverse()
    return tuple(chain)


def _visible_event(session_id: str, record: dict[str, Any]) -> PiEventInput | None:
    rendered = _render_record(record)
    if rendered is None:
        return None
    role, body = rendered
    if body == "":
        return None
    parent_id = record.get("parentId")
    return PiEventInput(
        session_id=session_id,
        event_id=str(record["id"]),
        parent_id=parent_id if isinstance(parent_id, str) else None,
        event_type=str(record["type"]),
        role=role,
        content=f"{role}: {body}",
        record=record,
    )


def _render_record(record: Mapping[str, Any]) -> tuple[str, str] | None:
    event_type = record.get("type")
    if event_type in {"compaction", "branch_summary"}:
        summary = record.get("summary")
        if not isinstance(summary, str) or summary == "":
            return None
        return str(event_type), summary
    if event_type == "custom_message":
        body = "\n".join(_visible_pieces(record.get("content")))
        if body == "":
            return None
        return "custom", body
    if event_type != "message":
        return None
    message = record.get("message")
    if not isinstance(message, Mapping):
        return None
    role = message.get("role")
    if not isinstance(role, str) or role == "":
        return None
    if role == "bashExecution":
        command = message.get("command", "")
        output = message.get("output", "")
        return role, f"$ {'' if not isinstance(command, str) else command}\n{'' if not isinstance(output, str) else output}"
    if role == "toolResult":
        text = "\n".join(_visible_pieces(message.get("content")))
        tool_name = message.get("toolName", "")
        tool_call_id = message.get("toolCallId", "")
        return role, f"[tool_result {tool_name} {tool_call_id}] {text}"
    body = "\n".join(_visible_pieces(message.get("content")))
    if body == "":
        return None
    return role, body


def _visible_pieces(content: object) -> list[str]:
    if isinstance(content, str):
        return [content] if content else []
    if not isinstance(content, list):
        return []
    pieces: list[str] = []
    for block in content:
        if isinstance(block, str):
            if block:
                pieces.append(block)
            continue
        if not isinstance(block, Mapping):
            continue
        kind = block.get("type")
        if kind == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                pieces.append(text)
        elif kind == "toolCall":
            arguments = block.get("arguments", {})
            payload = json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            pieces.append(f"[tool_call {block.get('name', '')} {block.get('id', '')}] {payload}")
    return pieces


def _checkpoint_events(checkpoint: object) -> dict[str, str]:
    if not isinstance(checkpoint, dict):
        return {}
    events = checkpoint.get("events")
    if not isinstance(events, dict):
        return {}
    return {str(key): str(value) for key, value in events.items() if isinstance(key, str) and isinstance(value, str)}


def _event_key(event: PiEventInput) -> str:
    return f"{event.session_id}\n{event.event_id}"


def _record_digest(record: Mapping[str, Any]) -> str:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _require_identity(value: str, label: str) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"Pi {label} must be a non-empty string")  # noqa: TRY003


__all__ = [
    "PI_EVENT_SOURCE_DEFINITION",
    "PiEventInput",
    "PiEventSource",
    "PiSessionConnector",
    "PiSessionInput",
    "parse_pi_session",
    "pi_event_source_id",
]

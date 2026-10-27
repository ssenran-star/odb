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

"""Self-describing context packs and prefix deltas."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping, Sequence

PACK_SCHEMA = "powercontext.context-pack.v1"
DELTA_SCHEMA = "powercontext.context-pack-delta.v1"
_DIGEST_PREFIX = "sha256:"


class ContextPackError(Exception):
    """A context pack or delta failed its public wire contract."""


class ContextPack:
    """One canonical, digest-addressed sequence of context chunks."""

    def __init__(self, items: tuple[bytes, ...], digest: str, byte_count: int) -> None:
        self.items = items
        self.digest = digest
        self.byte_count = byte_count

    @classmethod
    def build(cls, items: Sequence[bytes]) -> ContextPack:
        normalized = tuple(items)
        digest = _digest(PACK_SCHEMA, normalized)
        raw = _encode_pack({"schema": PACK_SCHEMA, "items": [_encode_item(item) for item in normalized], "digest": digest})
        return cls(normalized, digest, len(raw))

    @classmethod
    def from_content(cls, content: str, chunk_bytes: int = 512) -> ContextPack:
        return cls.build(_chunk_utf8(content, chunk_bytes))

    def to_bytes(self) -> bytes:
        return _encode_pack(
            {
                "schema": PACK_SCHEMA,
                "items": [_encode_item(item) for item in self.items],
                "digest": self.digest,
                "byte_count": self.byte_count,
            }
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> ContextPack:
        payload = _object(raw)
        if set(payload) != {"schema", "items", "digest", "byte_count"}:
            raise ContextPackError("context pack fields are incomplete")
        if payload["schema"] != PACK_SCHEMA or type(payload["byte_count"]) is not int:
            raise ContextPackError("context pack schema is invalid")
        if payload["byte_count"] != len(raw):
            raise ContextPackError("context pack byte_count does not match the payload")
        items = _decode_items(payload["items"])
        digest = payload["digest"]
        if digest != _digest(PACK_SCHEMA, items):
            raise ContextPackError("context pack digest does not match its items")
        pack = cls(items, digest, payload["byte_count"])
        if pack.to_bytes() != raw:
            raise ContextPackError("context pack payload is not canonical")
        return pack

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ContextPack)
            and self.items == other.items
            and self.digest == other.digest
            and self.byte_count == other.byte_count
        )


class ContextPackDelta:
    """A prefix-preserving change from one context pack digest to another."""

    def __init__(
        self,
        base_digest: str,
        target_digest: str,
        prefix_items: int,
        appended: tuple[bytes, ...],
    ) -> None:
        if type(prefix_items) is not int or prefix_items < 0:
            raise ContextPackError("prefix_items must be a non-negative integer")
        self.base_digest = base_digest
        self.target_digest = target_digest
        self.prefix_items = prefix_items
        self.appended = tuple(appended)

    @classmethod
    def between(cls, base: ContextPack, target: ContextPack) -> ContextPackDelta:
        prefix = 0
        for left, right in zip(base.items, target.items, strict=False):
            if left != right:
                break
            prefix += 1
        return cls(base.digest, target.digest, prefix, target.items[prefix:])

    @property
    def byte_count(self) -> int:
        return len(self.to_bytes())

    def to_bytes(self) -> bytes:
        payload = {
            "schema": DELTA_SCHEMA,
            "base_digest": self.base_digest,
            "target_digest": self.target_digest,
            "prefix_items": self.prefix_items,
            "appended": [_encode_item(item) for item in self.appended],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    @classmethod
    def from_bytes(cls, raw: bytes) -> ContextPackDelta:
        payload = _object(raw)
        if set(payload) != {"schema", "base_digest", "target_digest", "prefix_items", "appended"}:
            raise ContextPackError("context pack delta fields are incomplete")
        if payload["schema"] != DELTA_SCHEMA:
            raise ContextPackError("context pack delta schema is invalid")
        prefix = payload["prefix_items"]
        if type(prefix) is not int or prefix < 0:
            raise ContextPackError("prefix_items must be a non-negative integer")
        if not isinstance(payload["base_digest"], str) or not isinstance(payload["target_digest"], str):
            raise ContextPackError("context pack delta digests are invalid")
        return cls(payload["base_digest"], payload["target_digest"], prefix, _decode_items(payload["appended"]))


def apply_context_pack_delta(base: ContextPack, delta: ContextPackDelta) -> ContextPack:
    """Rebuild the target pack when the delta names this base and its exact digest."""

    if not isinstance(base, ContextPack) or not isinstance(delta, ContextPackDelta):
        raise ContextPackError("context pack delta inputs are invalid")
    if base.digest != delta.base_digest or delta.prefix_items > len(base.items):
        raise ContextPackError("context pack delta does not apply to this base")
    rebuilt = ContextPack.build(base.items[: delta.prefix_items] + delta.appended)
    if rebuilt.digest != delta.target_digest:
        raise ContextPackError("context pack delta target digest does not match")
    return rebuilt


def _chunk_utf8(content: str, chunk_bytes: int) -> tuple[bytes, ...]:
    if type(chunk_bytes) is not int or chunk_bytes < 1:
        raise ContextPackError("chunk_bytes must be a positive integer")
    if not isinstance(content, str):
        raise ContextPackError("content must be text")
    data = content.encode("utf-8")
    if not data:
        return ()
    chunks: list[bytes] = []
    start = 0
    boundaries = [0]
    for character in content:
        size = len(character.encode("utf-8"))
        if size > chunk_bytes:
            raise ContextPackError("a character does not fit in chunk_bytes")
        boundaries.append(boundaries[-1] + size)
    while start < len(data):
        limit = min(start + chunk_bytes, len(data))
        end = start
        for boundary in boundaries:
            if start < boundary <= limit:
                end = boundary
        if end == start:
            raise ContextPackError("a character does not fit in chunk_bytes")
        chunks.append(data[start:end])
        start = end
    return tuple(chunks)


def _digest(schema: str, items: tuple[bytes, ...]) -> str:
    unsigned = {"schema": schema, "items": [_encode_item(item) for item in items]}
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return _DIGEST_PREFIX + hashlib.sha256(canonical).hexdigest()


def _encode_pack(payload: Mapping[str, object]) -> bytes:
    if "byte_count" in payload:
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    guess = len(json.dumps({**payload, "byte_count": 0}, sort_keys=True, separators=(",", ":")).encode())
    for _ in range(6):
        encoded = json.dumps({**payload, "byte_count": guess}, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) == guess:
            return encoded
        guess = len(encoded)
    raise ContextPackError("context pack byte_count could not be resolved")


def _encode_item(item: bytes) -> str:
    if not isinstance(item, bytes):
        raise ContextPackError("context pack items must be bytes")
    return base64.b64encode(item).decode("ascii")


def _decode_items(value: object) -> tuple[bytes, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContextPackError("context pack items must be base64 strings")
    try:
        return tuple(base64.b64decode(item, validate=True) for item in value)
    except ValueError as error:
        raise ContextPackError("context pack items must be standard base64") from error


def _object(raw: bytes) -> dict[str, object]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContextPackError("context pack payload is not JSON") from error
    if not isinstance(payload, dict):
        raise ContextPackError("context pack payload must be an object")
    return payload


__all__ = [
    "ContextPack",
    "ContextPackDelta",
    "ContextPackError",
    "apply_context_pack_delta",
]

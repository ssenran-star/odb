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

"""Select query-specific evidence spans inside the prepared-context byte budget."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from powercontext.artifacts import ArtifactRef
from powercontext.builtin.artifacts.memory.models import MemoryHit
from powercontext.builtin.runtime.prepared_text import TRUST_POLICY

_BEGIN = "BEGIN_POWERCONTEXT_PREPARED_CONTEXT_V1"
_END = "END_POWERCONTEXT_PREPARED_CONTEXT_V1"
_TOKEN = re.compile(r"[a-z]+|\d+|[\u4e00-\u9fff]+")
_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+")
_STOP = frozenset(
    """
    a an the and or of to for in on at by from with without into over after before about as is are was were be been
    being that this these those it its their his her they them we our you your not no nor if then than so such what
    which who whom how when where why do does did done can may might should would will just than within between per
    """.split()
)


@dataclass(frozen=True)
class EvidenceFragment:
    """One half-open character span of a current Memory entry."""

    scope_id: str
    memory_ref: ArtifactRef
    entry_id: str
    entry_version_id: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class _Candidate:
    scope_id: str
    hit: MemoryHit
    start: int
    end: int
    score: float


def select_evidence(
    query: str,
    groups: Sequence[tuple[str, tuple[MemoryHit, ...]]],
    max_bytes: int,
) -> tuple[str | None, tuple[EvidenceFragment, ...]]:
    """Pack the highest-overlap literal spans that fit in the rendered envelope."""

    candidates = _candidates(query, groups)
    selected: list[_Candidate] = []
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.end - item.start)):
        if candidate.score <= 0 or any(_overlaps(candidate, current) for current in selected):
            continue
        trial = (*selected, candidate)
        if _rendered_size(trial) <= max_bytes:
            selected.append(candidate)
    if not selected:
        return None, ()
    ordered = sorted(selected, key=lambda item: (item.scope_id, item.hit.entry_id, item.start))
    fragments = tuple(
        EvidenceFragment(
            scope_id=item.scope_id,
            memory_ref=item.hit.memory_ref,
            entry_id=item.hit.entry_id,
            entry_version_id=item.hit.entry_version_id,
            start=item.start,
            end=item.end,
            text=item.hit.text[item.start : item.end],
        )
        for item in ordered
    )
    return _render(fragments), fragments


def _candidates(query: str, groups: Sequence[tuple[str, tuple[MemoryHit, ...]]]) -> list[_Candidate]:
    weights = _weights(query)
    found: list[_Candidate] = []
    for scope_id, hits in groups:
        for hit in hits:
            spans = _sentences(hit.text)
            for width in (1, 2, 3):
                for index in range(0, len(spans) - width + 1):
                    start = spans[index][0]
                    end = spans[index + width - 1][1]
                    if start >= end:
                        continue
                    found.append(
                        _Candidate(
                            scope_id=scope_id,
                            hit=hit,
                            start=start,
                            end=end,
                            score=_score(weights, hit.text[start:end]),
                        )
                    )
    return found


def _sentences(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in _SPLIT.finditer(text):
        if match.start() > start and text[start : match.start()].strip():
            spans.append((start, match.start()))
        start = match.end()
    if start < len(text) and text[start:].strip():
        spans.append((start, len(text)))
    if not spans and text:
        spans.append((0, len(text)))
    return spans


def _weights(query: str) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    for token in _TOKEN.findall(query.casefold()):
        if token.isdigit():
            weights[token] += 4
        elif token not in _STOP:
            weights[token] += 2
        else:
            weights[token] += 0.15
    return weights


def _score(weights: dict[str, float], text: str) -> float:
    if not weights:
        return 0.0
    counts: dict[str, int] = defaultdict(int)
    for token in _TOKEN.findall(text.casefold()):
        counts[token] += 1
    score = 0.0
    matched = 0
    for token, weight in weights.items():
        if counts[token]:
            matched += 1
            score += weight * min(counts[token], 2)
    if matched == 0:
        return 0.0
    return score + matched / len(weights)


def _overlaps(left: _Candidate, right: _Candidate) -> bool:
    return (
        left.scope_id == right.scope_id
        and left.hit.entry_id == right.hit.entry_id
        and left.start < right.end
        and right.start < left.end
    )


def _rendered_size(candidates: Sequence[_Candidate]) -> int:
    fragments = tuple(
        EvidenceFragment(
            scope_id=item.scope_id,
            memory_ref=item.hit.memory_ref,
            entry_id=item.hit.entry_id,
            entry_version_id=item.hit.entry_version_id,
            start=item.start,
            end=item.end,
            text=item.hit.text[item.start : item.end],
        )
        for item in candidates
    )
    return len(_render(fragments).encode("utf-8"))


def _render(fragments: Sequence[EvidenceFragment]) -> str:
    envelope = {
        "trust": "untrusted_history",
        "items": [
            {
                "citation": {
                    "scope_id": fragment.scope_id,
                    "memory_ref": fragment.memory_ref.model_dump(mode="json"),
                    "entry_id": fragment.entry_id,
                    "entry_version_id": fragment.entry_version_id,
                },
                "content": fragment.text,
                "start": fragment.start,
                "end": fragment.end,
            }
            for fragment in fragments
        ],
    }
    encoded = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
    return "\n\n".join((TRUST_POLICY, f"{_BEGIN}\n{encoded}\n{_END}"))


__all__ = ["EvidenceFragment", "select_evidence"]

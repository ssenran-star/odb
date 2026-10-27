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

"""Score Memory candidates with one caller-supplied HTTP reranking service."""

from __future__ import annotations

import json
import math

import httpx

from powercontext.builtin.artifacts.memory.models import MemoryHit
from powercontext.builtin.artifacts.memory.reranking import MemoryRerankDecision, _validate_bounds
from powercontext.builtin.inference.models import InferenceUsage


class HTTPMemoryReranker:
    """Select original candidate ranks from cross-batch HTTP scores."""

    def __init__(
        self,
        endpoint: str,
        *,
        client: httpx.AsyncClient,
        batch_size: int = 32,
        policy_id: str = "http-cross-encoder-v1",
    ) -> None:
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size must be a positive integer")  # noqa: TRY003
        self._endpoint = endpoint
        self._client = client
        self._batch_size = batch_size
        self.policy_id = policy_id

    async def rerank(
        self,
        query: str,
        candidates: tuple[MemoryHit, ...],
        limit: int,
        /,
    ) -> MemoryRerankDecision:
        _validate_bounds(len(candidates), limit)
        scores: dict[int, float] = {}
        requests = 0
        for start in range(0, len(candidates), self._batch_size):
            batch = tuple(range(start + 1, min(start + self._batch_size, len(candidates)) + 1))
            body = {
                "query": query,
                "candidates": [{"rank": rank, "text": candidates[rank - 1].text} for rank in batch],
            }
            response = await self._client.post(self._endpoint, json=body)
            response.raise_for_status()
            requests += 1
            scores.update(_parse_scores(response, batch))
        selected = tuple(sorted(scores, key=lambda rank: (-scores[rank], rank))[:limit])
        return MemoryRerankDecision(
            selected_ranks=selected,
            usage=InferenceUsage(requests=requests),
            discarded_rank_count=len(candidates) - len(selected),
        )


def _parse_scores(response: httpx.Response, expected: tuple[int, ...]) -> dict[int, float]:
    try:
        payload = response.json()
    except json.JSONDecodeError as error:
        raise ValueError("rerank response must be JSON") from error  # noqa: TRY003
    if not isinstance(payload, dict) or set(payload) != {"scores"} or not isinstance(payload["scores"], list):
        raise ValueError("rerank response must contain only scores")  # noqa: TRY003
    found: dict[int, float] = {}
    for item in payload["scores"]:
        if not isinstance(item, dict) or set(item) != {"rank", "score"}:
            raise ValueError("rerank score records must contain only rank and score")  # noqa: TRY003
        rank = item["rank"]
        score = item["score"]
        if type(rank) is not int or rank not in expected or rank in found:
            raise ValueError("rerank response must cover each batch rank once")  # noqa: TRY003
        if isinstance(score, bool) or not isinstance(score, int | float) or not math.isfinite(float(score)):
            raise ValueError("rerank score must be a finite number")  # noqa: TRY003
        found[rank] = float(score)
    if set(found) != set(expected):
        raise ValueError("rerank response must cover each batch rank once")  # noqa: TRY003
    return found


__all__ = ["HTTPMemoryReranker"]

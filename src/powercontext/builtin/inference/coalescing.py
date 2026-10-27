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

"""Share identical embedding work across concurrent callers and cache successes."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from typing import Any

from powercontext.builtin.inference.models import EmbeddingResult, InferenceUsage
from powercontext.builtin.inference.protocols import EmbeddingModel


class CoalescingEmbeddingModel:
    """Batch identical texts, share in-flight work, and reuse a bounded success cache."""

    def __init__(
        self,
        model: EmbeddingModel,
        *,
        max_batch_size: int = 64,
        coalesce_ms: float = 5.0,
        cache_size: int = 1024,
    ) -> None:
        if isinstance(max_batch_size, bool) or not isinstance(max_batch_size, int) or max_batch_size < 1:
            raise ValueError("max_batch_size must be a positive integer")  # noqa: TRY003
        if isinstance(cache_size, bool) or not isinstance(cache_size, int) or cache_size < 0:
            raise ValueError("cache_size must be a non-negative integer")  # noqa: TRY003
        self._model = model
        self._max_batch_size = max_batch_size
        self._coalesce_ms = coalesce_ms
        self._cache_size = cache_size
        self._cache: OrderedDict[str, tuple[float, ...]] = OrderedDict()
        self._pending: dict[str, list[asyncio.Future[tuple[Any, int | None, InferenceUsage | None]]]] = {}
        self._inflight: dict[str, list[asyncio.Future[tuple[Any, int | None, InferenceUsage | None]]]] = {}
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._next_batch = 0

    @property
    def profile(self):
        return self._model.profile

    async def embed(self, texts: tuple[str, ...], /) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(vectors=(), usage=InferenceUsage(requests=0))
        loop = asyncio.get_running_loop()
        async with self._lock:
            futures = [self._reserve(text, loop) for text in texts]
            if self._pending and self._flush_task is None:
                self._flush_task = asyncio.create_task(self._flush())
        vectors = []
        usages: dict[int, InferenceUsage] = {}
        for future in futures:
            vector, batch_id, usage = await asyncio.shield(future)
            vectors.append(vector)
            if batch_id is not None and usage is not None and batch_id not in usages:
                usages[batch_id] = usage
        return EmbeddingResult(vectors=tuple(vectors), usage=_combine_usage(usages))

    def _reserve(self, text: str, loop: asyncio.AbstractEventLoop):
        cached = self._cache.get(text) if self._cache_size else None
        future: asyncio.Future[tuple[Any, int | None, InferenceUsage | None]] = loop.create_future()
        if cached is not None:
            self._cache.move_to_end(text)
            future.set_result((cached, None, None))
            return future
        if text in self._inflight:
            self._inflight[text].append(future)
            return future
        self._pending.setdefault(text, []).append(future)
        return future

    async def _flush(self) -> None:
        await asyncio.sleep(self._coalesce_ms / 1000 if self._coalesce_ms else 0)
        while True:
            async with self._lock:
                if not self._pending:
                    self._flush_task = None
                    return
                texts: list[str] = []
                waiters: list[list[asyncio.Future[tuple[Any, int | None, InferenceUsage | None]]]] = []
                for text in list(self._pending):
                    if len(texts) == self._max_batch_size:
                        break
                    texts.append(text)
                    waiters.append(self._pending.pop(text))
                    self._inflight[text] = waiters[-1]
                self._next_batch += 1
                batch_id = self._next_batch
            await self._complete_batch(tuple(texts), waiters, batch_id)

    async def _complete_batch(
        self,
        texts: tuple[str, ...],
        waiters: list[list[asyncio.Future[tuple[Any, int | None, InferenceUsage | None]]]],
        batch_id: int,
    ) -> None:
        try:
            result = await self._model.embed(texts)
        except Exception as error:
            self._fail(texts, waiters, error)
            return
        if len(result.vectors) != len(texts):
            self._fail(texts, waiters, ValueError("embedding provider returned the wrong vector count"))
            return
        async with self._lock:
            for text, vector, futures in zip(texts, result.vectors, waiters, strict=True):
                self._inflight.pop(text, None)
                normalized = tuple(vector)
                if self._cache_size:
                    self._cache[text] = normalized
                    self._cache.move_to_end(text)
                    while len(self._cache) > self._cache_size:
                        self._cache.popitem(last=False)
                for future in futures:
                    if not future.done():
                        future.set_result((normalized, batch_id, result.usage))

    def _fail(
        self,
        texts: tuple[str, ...],
        waiters: list[list[asyncio.Future[tuple[Any, int | None, InferenceUsage | None]]]],
        error: BaseException,
    ) -> None:
        for text, futures in zip(texts, waiters, strict=True):
            self._inflight.pop(text, None)
            for future in futures:
                if not future.done():
                    future.set_exception(error)


def _combine_usage(usages: dict[int, InferenceUsage]) -> InferenceUsage:
    if not usages:
        return InferenceUsage(requests=0)
    requests = sum(usage.requests for usage in usages.values())
    return InferenceUsage(
        requests=requests,
        input_tokens=_sum_tokens(usage.input_tokens for usage in usages.values()),
        output_tokens=_sum_tokens(usage.output_tokens for usage in usages.values()),
    )


def _sum_tokens(values) -> int | None:
    observed = tuple(values)
    if not observed or all(value is None for value in observed):
        return None
    return sum(0 if value is None else value for value in observed)


__all__ = ["CoalescingEmbeddingModel"]

from __future__ import annotations

import hashlib
import math
import re

DIM = 128
_TOKEN = re.compile(r"[a-z0-9_]{2,}|[\u4e00-\u9fff]{2,}")


def embed_text(text: str, dim: int = DIM) -> list[float]:
    """Deterministic hashed character-and-token embedding. No network and no model download."""
    vector = [0.0] * dim
    folded = text.lower()
    grams = [folded[i : i + 2] for i in range(max(len(folded) - 1, 0))] or [folded or " "]
    for gram in grams:
        digest = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
        vector[digest % dim] += 1.0
        vector[(digest // 17) % dim] += 0.5
    for token in _TOKEN.findall(folded):
        digest = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        vector[digest % dim] += 2.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]

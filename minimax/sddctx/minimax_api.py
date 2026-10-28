from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sddctx.config import Config
from sddctx.textutil import scrub

SYSTEM_PROMPT = """你是 SDD 工作流中的代码修改器。只根据用户消息里的开发上下文修改 src/shiftpay.py。
规则：
1. 返回完整的 src/shiftpay.py，且只放在一个 python 代码块中。也可以额外给出 unified diff，但完整文件是必须的。
2. 实现 day_type == "holiday" 的加班工资。倍数必须等于上下文规格原文中的 HOLIDAY_MULTIPLIER，不要沿用对话外的旧倍数。
3. 保持 regular_pay、weekday（1.5）和 weekend（2.0）的既有行为。
4. 负数工时或时薪、未知 day_type 继续抛出 ValueError。
5. 不要修改测试文件，不要解释代码块以外的任务。
"""


def build_messages(context_markdown: str) -> list[dict[str, str]]:
    user = (
        context_markdown.rstrip()
        + "\n\n请只根据上面的开发上下文修改代码。\n"
        + "返回完整的 src/shiftpay.py，放在一个 python 代码块中。\n"
        + "节日加班倍数必须使用上下文里规格原文中的 HOLIDAY_MULTIPLIER。\n"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def request_body(cfg: Config, messages: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "model": cfg.minimax_model,
        "messages": messages,
        "temperature": cfg.minimax_temperature,
        "max_completion_tokens": cfg.minimax_max_tokens,
    }


def call_minimax(cfg: Config, messages: list[dict[str, str]]) -> dict[str, Any]:
    if not cfg.minimax_key:
        raise RuntimeError("MINIMAX_API_KEY is not set")
    payload = request_body(cfg, messages)
    raw = json.dumps(payload).encode("utf-8")
    request = Request(
        cfg.minimax_base + "/chat/completions",
        data=raw,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.minimax_key}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=cfg.minimax_timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = scrub(exc.read().decode("utf-8", errors="replace"), cfg.minimax_key)
        raise RuntimeError(f"MiniMax HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"MiniMax unreachable: {exc}") from exc
    parsed = json.loads(scrub(body, cfg.minimax_key))
    base = parsed.get("base_resp") or {}
    if base.get("status_code") not in (None, 0):
        raise RuntimeError(f"MiniMax base_resp: {base}")
    return parsed


def assistant_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError(f"MiniMax response had no choices: {response.get('base_resp') or response}")
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    reasoning = message.get("reasoning_content") or ""
    if "def overtime_pay" in content or "```" in content or "@@" in content:
        return content
    if reasoning:
        return content + "\n" + reasoning
    return content


def response_summary(response: dict[str, Any], assistant: str) -> dict[str, Any]:
    choice = (response.get("choices") or [{}])[0]
    return {
        "id": response.get("id"),
        "model": response.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": response.get("usage"),
        "base_resp": response.get("base_resp"),
        "assistant_sha256": __import__("hashlib").sha256(assistant.encode("utf-8")).hexdigest(),
        "assistant_text": assistant,
    }

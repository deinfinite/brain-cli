"""Brain CLI v2 — httpx-based adapter for OpenCode Go reasoning API."""

from __future__ import annotations

import time
from typing import cast

import httpx

from ..errors import APIError, BadResponseError, RetryableError
from ..retry import retry_with_backoff
from ..stats import Stats


class ReasoningAdapter:
    """Adapter for the OpenCode Go reasoning endpoint.

    Uses raw httpx (no OpenAI SDK dependency).
    Follows the OpenAI chat completions wire format.
    """

    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def complete(
        self,
        messages: list[dict],
        model: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        reasoning_effort: str | None = None,
        retries: int = 3,
    ) -> tuple[str, Stats]:
        body: dict = {
            "model": model,
            "messages": messages,
        }

        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        if temperature is not None:
            body["temperature"] = temperature

        if reasoning_effort is not None:
            body["reasoning_effort"] = reasoning_effort

        stats = Stats(model=model)
        start_time = time.monotonic()

        def _make_call():
            try:
                with httpx.Client(timeout=120.0) as hclient:
                    resp = hclient.post(
                        f"{self._base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=body,
                    )

                stats.latency_ms = (time.monotonic() - start_time) * 1000

                if resp.status_code >= 500:
                    stats.retries_used += 1
                    raise RetryableError(
                        f"Server error: {resp.status_code}",
                        status_code=resp.status_code,
                    )

                if resp.status_code == 429:
                    stats.retries_used += 1
                    raise RetryableError("Rate limited", status_code=resp.status_code)

                if resp.status_code != 200:
                    raise APIError(
                        f"API error: {resp.status_code} {resp.text}",
                        status_code=resp.status_code,
                    )

                data = resp.json()

                usage = data.get("usage", {})
                stats.prompt_tokens = usage.get("prompt_tokens", 0) or 0
                stats.completion_tokens = usage.get("completion_tokens", 0) or 0
                stats.total_tokens = usage.get("total_tokens", 0) or 0
                stats.model = data.get("model", model)

                choices = data.get("choices", [])
                if not choices:
                    raise BadResponseError("Empty choices from reasoning API")

                content = choices[0].get("message", {}).get("content", "")
                if not content or not content.strip():
                    raise BadResponseError("Empty response from model")

                return content.strip()

            except (BadResponseError, APIError):
                raise
            except RetryableError:
                raise
            except Exception as e:
                raise APIError(str(e)) from e

        result = cast(str, retry_with_backoff(_make_call, max_retries=retries))
        return result, stats

    def supports_model(self, model: str) -> bool:
        from ..keys import get_adapter_name

        return get_adapter_name("opencode_go", model) == "reasoning"

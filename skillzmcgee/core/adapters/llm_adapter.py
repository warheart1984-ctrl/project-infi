from __future__ import annotations

from collections.abc import Callable
import json
import os
from typing import Any
import urllib.request

from skillzmcgee.core.receipts import build_receipt
from skillzmcgee.governance.continuity_ledger import ValidatedLedger
from skillzmcgee.governance.state_accumulator import StateAccumulator


DEFAULT_AAIS_ENDPOINT = "/legacy_api/api/text/generate"
DEFAULT_NOVA_ENDPOINT = "/api/text/generate"


class NovaAAISClient:
    def __init__(
        self,
        *,
        base_url: str,
        endpoint: str = DEFAULT_AAIS_ENDPOINT,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        self.timeout = timeout

    def __call__(self, prompt: str) -> str:
        payload = json.dumps({"prompt": prompt, "text": prompt}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{self.endpoint}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
        return _extract_text(json.loads(body))


def build_llm_from_env(
    *,
    provider: str | None = None,
    base_url: str | None = None,
    endpoint: str | None = None,
    timeout: float = 30.0,
) -> Callable[[str], str] | None:
    selected_provider = (provider or os.getenv("SKILLZMCGEE_LLM_PROVIDER") or "").lower()
    selected_base_url = (
        base_url
        or os.getenv("SKILLZMCGEE_LLM_URL")
        or os.getenv("AAIS_BASE_URL")
        or os.getenv("NOVA_BASE_URL")
    )
    if selected_provider in {"", "placeholder", "none"} and selected_base_url is None:
        return None
    if selected_provider not in {"", "aais", "nova", "skillz", "skillzmcgee"}:
        raise ValueError(f"unsupported SkillzMcGee LLM provider: {selected_provider}")
    if selected_base_url is None:
        raise ValueError("SkillzMcGee LLM provider selected but no base URL was configured")

    default_endpoint = DEFAULT_NOVA_ENDPOINT if selected_provider == "nova" else DEFAULT_AAIS_ENDPOINT
    return NovaAAISClient(
        base_url=selected_base_url,
        endpoint=endpoint or os.getenv("SKILLZMCGEE_LLM_ENDPOINT") or default_endpoint,
        timeout=timeout,
    )


def _extract_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object or string")

    for key in ("text", "output", "response", "generated_text", "completion"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            for key in ("text", "message", "content"):
                value = first.get(key)
                if isinstance(value, str):
                    return value
                if isinstance(value, dict) and isinstance(value.get("content"), str):
                    return value["content"]

    raise ValueError("LLM response did not include a supported text field")


class LawfulLLMAdapter:
    def __init__(
        self,
        llm: Callable[[str], str] | None,
        ledger: ValidatedLedger,
        accumulator: StateAccumulator,
        actor: str = "skillz",
    ) -> None:
        self.llm = llm or (lambda prompt: prompt)
        self.ledger = ledger
        self.accumulator = accumulator
        self.actor = actor

    def ask(self, prompt: str, context_slice: str | None = None) -> str:
        context: dict[str, Any] = {}
        if context_slice:
            context = self.accumulator.get_slice_state(context_slice) or {}

        full_prompt = f"Context[{context_slice or 'global'}]: {context}\n\nQuestion: {prompt}"
        output = self.llm(full_prompt)
        receipt = build_receipt(
            actor=self.actor,
            slice_id=f"llm:{context_slice}" if context_slice else "llm",
            input_data=prompt,
            output_data=output,
            status="ok",
        )
        self.ledger.append(receipt)
        self.accumulator.apply_entry(receipt)
        return output

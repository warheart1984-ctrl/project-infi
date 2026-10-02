"""Groq and NVIDIA NIM providers (OpenAI-compatible chat completions)."""

from __future__ import annotations

import os

from src.providers.openrouter_provider import OpenRouterProvider

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_NVIDIA_MODEL = "nvidia/nemotron-3-super-120b-a12b"
DEFAULT_NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


class _CompatProvider(OpenRouterProvider):
    send_openrouter_extras = False
    # Reasoning models spend tokens thinking; tiny budgets return empty text.
    min_output_tokens = 256
    key_env = ""
    model_env = ""
    url_env = ""
    default_model = ""
    default_url = ""

    def __init__(self, api_key=None, *, model=None, endpoint=None, client=None) -> None:
        super().__init__(
            api_key or os.getenv(self.key_env),
            model=model or os.getenv(self.model_env) or self.default_model,
            endpoint=endpoint or os.getenv(self.url_env) or self.default_url,
            client=client,
        )


class GroqProvider(_CompatProvider):
    provider_name = "groq"
    display_name = "Groq"
    key_env = "GROQ_API_KEY"
    model_env = "AAIS_GROQ_MODEL"
    url_env = "AAIS_GROQ_BASE_URL"
    default_model = DEFAULT_GROQ_MODEL
    default_url = DEFAULT_GROQ_URL

    def extra_payload(self, model):
        return {"reasoning_effort": "low"} if model.startswith("openai/gpt-oss") else {}


class NvidiaProvider(_CompatProvider):
    provider_name = "nvidia"
    display_name = "NVIDIA"
    key_env = "NVIDIA_API_KEY"
    model_env = "AAIS_NVIDIA_MODEL"
    url_env = "AAIS_NVIDIA_BASE_URL"
    default_model = DEFAULT_NVIDIA_MODEL
    default_url = DEFAULT_NVIDIA_URL

    def extra_payload(self, model):
        if "nemotron" in model:
            return {"chat_template_kwargs": {"enable_thinking": False}}
        return {}

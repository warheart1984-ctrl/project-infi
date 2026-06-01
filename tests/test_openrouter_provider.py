"""Tests for the OpenRouter provider adapter."""

import asyncio
import unittest

from src.jarvis_protocol import JarvisMessage
from src.providers.openrouter_provider import OpenRouterProvider


class _FakeOpenRouterClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, payload, headers):
        self.calls.append((payload, headers))
        return self.response


class TestOpenRouterProvider(unittest.TestCase):
    """Verify the OpenRouter adapter stays inside the Jarvis protocol."""

    def test_invoke_normalizes_openai_compatible_response(self):
        """OpenRouterProvider should send Jarvis messages and normalize tool calls back."""
        fake_client = _FakeOpenRouterClient(
            {
                "model": "openrouter/free",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {
                            "content": "Free model answered cleanly.",
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "type": "function",
                                    "function": {
                                        "name": "workspace_search",
                                        "arguments": "{\"query\": \"api.py\"}",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 111,
                    "completion_tokens": 54,
                },
            }
        )
        provider = OpenRouterProvider(
            api_key="test-key",
            model="openrouter/free",
            client=fake_client,
            app_name="AAIS Test",
            site_url="https://example.com",
        )

        result = asyncio.run(
            provider.invoke(
                [
                    JarvisMessage(role="system", content="Stay grounded."),
                    JarvisMessage(role="user", content="Help me debug api.py."),
                ],
                tools=[{"type": "function", "function": {"name": "workspace_search"}}],
                max_tokens=512,
                temperature=0.2,
            )
        )

        self.assertEqual(result.provider, "openrouter")
        self.assertEqual(result.model, "openrouter/free")
        self.assertEqual(result.content, "Free model answered cleanly.")
        self.assertEqual(result.stop_reason, "length")
        self.assertEqual(result.finish_reason, "length")
        self.assertEqual(result.input_tokens, 111)
        self.assertEqual(result.output_tokens, 54)
        self.assertEqual(result.tool_calls[0].name, "workspace_search")
        self.assertEqual(result.tool_calls[0].arguments["query"], "api.py")

        payload, headers = fake_client.calls[0]
        self.assertEqual(payload["model"], "openrouter/free")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(payload["max_completion_tokens"], 512)
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(headers["X-Title"], "AAIS Test")
        self.assertEqual(headers["HTTP-Referer"], "https://example.com")

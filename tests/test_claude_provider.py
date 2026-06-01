"""Tests for the Claude provider adapter."""

import asyncio
import os
import unittest
from unittest.mock import patch

from src.jarvis_protocol import JarvisMessage
from src.providers.claude_provider import ClaudeProvider


class _FakeContentBlock:
    def __init__(self, block_type, text=None, block_id=None, name=None, tool_input=None):
        self.type = block_type
        self.text = text
        self.id = block_id
        self.name = name
        self.input = tool_input


class _FakeUsage:
    def __init__(self, input_tokens=0, output_tokens=0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeResponse:
    def __init__(self, content, *, stop_reason=None, usage=None):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage


class _FakeMessagesApi:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class _FakeClaudeClient:
    def __init__(self, response):
        self.messages = _FakeMessagesApi(response)


class TestClaudeProvider(unittest.TestCase):
    """Verify the Anthropic adapter stays inside the Jarvis protocol."""

    def test_invoke_merges_system_messages_and_normalizes_tool_calls(self):
        """ClaudeProvider should turn Jarvis messages into Anthropic calls and back."""
        fake_response = _FakeResponse(
            [
                _FakeContentBlock("text", text="Calm answer."),
                _FakeContentBlock(
                    "tool_use",
                    block_id="toolu_123",
                    name="workspace_search",
                    tool_input={"query": "api.py"},
                ),
            ],
            stop_reason="max_tokens",
            usage=_FakeUsage(input_tokens=240, output_tokens=87),
        )
        fake_client = _FakeClaudeClient(fake_response)
        provider = ClaudeProvider(client=fake_client, model="claude-test")

        result = asyncio.run(
            provider.invoke(
                [
                    JarvisMessage(role="system", content="Stay grounded in local evidence."),
                    JarvisMessage(role="user", content="Help me debug api.py."),
                ],
                tools=[{"name": "workspace_search"}],
                system="Base system prompt.",
                max_tokens=512,
                temperature=0.3,
            )
        )

        self.assertEqual(result.content, "Calm answer.")
        self.assertEqual(result.provider, "claude")
        self.assertEqual(result.model, "claude-test")
        self.assertEqual(result.stop_reason, "max_tokens")
        self.assertEqual(result.finish_reason, "length")
        self.assertEqual(result.input_tokens, 240)
        self.assertEqual(result.output_tokens, 87)
        self.assertEqual(result.tool_calls[0].name, "workspace_search")
        self.assertEqual(result.tool_calls[0].arguments["query"], "api.py")

        request_payload = fake_client.messages.calls[0]
        self.assertEqual(request_payload["model"], "claude-test")
        self.assertIn("Base system prompt.", request_payload["system"])
        self.assertIn("Stay grounded in local evidence.", request_payload["system"])
        self.assertEqual(request_payload["messages"][0]["role"], "user")
        self.assertEqual(request_payload["messages"][0]["content"], "Help me debug api.py.")

    def test_invoke_maps_end_turn_to_stop_finish_reason(self):
        """Anthropic end_turn should be recorded as a natural stop, not a length stop."""
        fake_response = _FakeResponse(
            [_FakeContentBlock("text", text="Calm answer.")],
            stop_reason="end_turn",
            usage=_FakeUsage(input_tokens=32, output_tokens=14),
        )
        provider = ClaudeProvider(client=_FakeClaudeClient(fake_response), model="claude-test")

        result = asyncio.run(
            provider.invoke(
                [JarvisMessage(role="user", content="Keep this answer complete.")],
                max_tokens=128,
            )
        )

        self.assertEqual(result.stop_reason, "end_turn")
        self.assertEqual(result.finish_reason, "stop")

    @patch("src.providers.claude_provider.load_dotenv")
    @patch("src.providers.claude_provider.anthropic")
    def test_provider_loads_dotenv_before_resolving_api_key(self, mock_anthropic, mock_load_dotenv):
        mock_anthropic.Anthropic.return_value = object()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False):
            provider = ClaudeProvider(model="claude-test-model")

        mock_load_dotenv.assert_called_once()
        mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")
        self.assertEqual(provider.model, "claude-test-model")

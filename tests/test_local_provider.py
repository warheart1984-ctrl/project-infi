"""Tests for the local protocol-compatible provider adapter."""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from src.jarvis_protocol import JarvisMessage
from src.providers.local_provider import LocalProvider


class TestLocalProvider(unittest.TestCase):
    """Verify the local provider speaks the same protocol as remote sisters."""

    @patch("src.api.init_ai")
    def test_invoke_routes_through_existing_local_runtime(self, mock_init_ai):
        """LocalProvider should delegate to AAIS generate_chat without changing the contract."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Local Jarvis answer."
        fake_model.text_model_name = "local-test-model"
        fake_model.last_generation_metadata = {
            "stop_reason": "eos_token",
            "finish_reason": "stop",
            "input_tokens": 120,
            "output_tokens": 18,
        }
        mock_init_ai.return_value = (fake_model, object())

        provider = LocalProvider()
        result = asyncio.run(
            provider.invoke(
                [
                    JarvisMessage(role="system", content="Stay grounded."),
                    JarvisMessage(role="user", content="Help me debug api.py."),
                ],
                max_tokens=320,
                temperature=0.25,
                response_mode="debug",
                routing_profile={"id": "bug_hunter"},
            )
        )

        self.assertEqual(result.content, "Local Jarvis answer.")
        self.assertEqual(result.provider, "local")
        self.assertEqual(result.model, "local-test-model")
        self.assertEqual(result.stop_reason, "eos_token")
        self.assertEqual(result.finish_reason, "stop")
        self.assertEqual(result.input_tokens, 120)
        self.assertEqual(result.output_tokens, 18)
        fake_model.generate_chat.assert_called_once()
        args = fake_model.generate_chat.call_args.args
        self.assertEqual(args[0][0]["role"], "system")
        self.assertEqual(args[0][1]["role"], "user")
        self.assertEqual(args[1], 320)
        self.assertEqual(args[2], 0.25)
        self.assertEqual(args[3], "debug")
        self.assertEqual(args[4]["provider"], "local")
        self.assertEqual(args[4]["provider_kind"], "local")

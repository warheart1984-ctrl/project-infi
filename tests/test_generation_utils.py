"""Tests for prompt formatting and decode helpers."""

import unittest

from src.generation_utils import (
    decode_generated_text,
    looks_like_prompt_echo,
    resolve_input_token_limit,
)


class FakeTokenizer:
    """Small tokenizer stub for generation helper tests."""

    def __init__(self, model_max_length=4096):
        self.model_max_length = model_max_length

    def decode(self, token_ids, skip_special_tokens=True):
        if not token_ids:
            return ""
        return " ".join(str(token) for token in token_ids)


class TestGenerationUtils(unittest.TestCase):
    """Exercise helper behavior around token budgets and decode safety."""

    def test_decode_generated_text_does_not_echo_prompt_when_no_new_tokens(self):
        tokenizer = FakeTokenizer()
        self.assertEqual(decode_generated_text(tokenizer, [1, 2, 3], 3), "")

    def test_resolve_input_token_limit_keeps_room_for_context(self):
        tokenizer = FakeTokenizer(model_max_length=4096)
        self.assertEqual(resolve_input_token_limit(tokenizer, 320), 2048)
        self.assertEqual(resolve_input_token_limit(tokenizer, 64), 2048)

    def test_resolve_input_token_limit_respects_small_model_limit(self):
        tokenizer = FakeTokenizer(model_max_length=512)
        self.assertEqual(resolve_input_token_limit(tokenizer, 320), 256)

    def test_looks_like_prompt_echo_detects_runtime_blocks(self):
        self.assertTrue(looks_like_prompt_echo("system\nJarvis runtime state:\n- active_mode: explore"))
        self.assertTrue(
            looks_like_prompt_echo(
                "I have the following files from your workspace. Please let me know what you would like to do with this information."
            )
        )
        self.assertFalse(looks_like_prompt_echo("Fast mode is live and answering directly."))


if __name__ == "__main__":
    unittest.main()

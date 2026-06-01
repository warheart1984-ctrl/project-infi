"""Tests for AI models."""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.models import MultiModalAI


class TestMultiModalAI(unittest.TestCase):
    """Test cases for MultiModalAI."""

    @patch("src.models.get_optimal_dtype", return_value="float32")
    @patch.object(MultiModalAI, "_load_models")
    def test_initialization_uses_explicit_device(self, mock_load_models, mock_dtype):
        """Test model initialization with an explicit device."""
        ai = MultiModalAI(device="cpu")

        self.assertIsNotNone(ai)
        self.assertEqual(ai.device, "cpu")
        self.assertEqual(ai.dtype, "float32")
        mock_dtype.assert_called_once_with("cpu")
        mock_load_models.assert_called_once_with()

    @patch("src.models.get_optimal_dtype", return_value="float16")
    @patch("src.models.get_optimal_device", return_value="cuda")
    @patch.object(MultiModalAI, "_load_models")
    def test_device_selection_uses_optimal_device(
        self,
        mock_load_models,
        mock_get_device,
        mock_dtype,
    ):
        """Test device auto-selection without loading real models."""
        ai = MultiModalAI()

        self.assertEqual(ai.device, "cuda")
        self.assertEqual(ai.dtype, "float16")
        mock_get_device.assert_called_once_with()
        mock_dtype.assert_called_once_with("cuda")
        mock_load_models.assert_called_once_with()

    @patch("src.models.get_quantization_config", return_value=None)
    @patch("src.models.warm_up_model")
    @patch("src.models.try_compile_model", side_effect=lambda model: model)
    @patch("src.models.AutoModelForCausalLM.from_pretrained")
    @patch("src.models.AutoTokenizer.from_pretrained")
    @patch.object(MultiModalAI, "_load_models")
    @patch("src.models.get_optimal_dtype", return_value="float32")
    def test_text_adapter_path_loads_optional_adapter(
        self,
        mock_dtype,
        mock_load_models,
        mock_tokenizer,
        mock_model_loader,
        mock_compile,
        mock_warm_up,
        mock_quantization,
    ):
        """Configured adapter paths should attach a PEFT adapter to the base text model."""
        fake_tokenizer = MagicMock()
        fake_tokenizer.pad_token = "<pad>"
        fake_tokenizer.eos_token = "</s>"
        mock_tokenizer.return_value = fake_tokenizer

        fake_base_model = MagicMock()
        fake_adapter_model = MagicMock()
        mock_model_loader.return_value = fake_base_model

        with patch.dict(
            os.environ,
            {
                "AAIS_TEXT_ADAPTER_PATH": "training/out/demo-adapter",
                "AAIS_ENABLE_TEXT_ADAPTERS": "1",
            },
            clear=False,
        ):
            ai = MultiModalAI(device="cpu")
            with patch.object(ai, "_load_text_adapter", return_value=fake_adapter_model) as mock_adapter:
                ai._load_text_model()

        mock_adapter.assert_called_once_with("training/out/demo-adapter", adapter_name="fast")
        self.assertIs(ai.text_model, fake_adapter_model)
        mock_warm_up.assert_called_once()

    @patch("src.models.get_quantization_config", return_value=None)
    @patch("src.models.warm_up_model")
    @patch("src.models.try_compile_model", side_effect=lambda model: model)
    @patch("src.models.AutoModelForCausalLM.from_pretrained")
    @patch("src.models.AutoTokenizer.from_pretrained")
    @patch.object(MultiModalAI, "_load_models")
    @patch("src.models.get_optimal_dtype", return_value="float32")
    def test_text_adapters_can_be_disabled_explicitly(
        self,
        mock_dtype,
        mock_load_models,
        mock_tokenizer,
        mock_model_loader,
        mock_compile,
        mock_warm_up,
        mock_quantization,
    ):
        """AAIS_ENABLE_TEXT_ADAPTERS=0 should keep the base model active even if paths exist."""
        fake_tokenizer = MagicMock()
        fake_tokenizer.pad_token = "<pad>"
        fake_tokenizer.eos_token = "</s>"
        mock_tokenizer.return_value = fake_tokenizer

        fake_base_model = MagicMock()
        mock_model_loader.return_value = fake_base_model

        with patch.dict(
            os.environ,
            {
                "AAIS_ENABLE_TEXT_ADAPTERS": "0",
                "AAIS_TEXT_ADAPTER_PATH": "training/out/demo-adapter",
            },
            clear=False,
        ):
            ai = MultiModalAI(device="cpu")
            with patch.object(ai, "_load_text_adapter") as mock_adapter:
                ai._load_text_model()

        mock_adapter.assert_not_called()
        self.assertIs(ai.text_model, fake_base_model.to.return_value)
        mock_warm_up.assert_called_once()

    @patch("src.models.get_quantization_config", return_value=None)
    @patch("src.models.warm_up_model")
    @patch("src.models.try_compile_model", side_effect=lambda model: model)
    @patch("src.models.AutoModelForCausalLM.from_pretrained")
    @patch("src.models.AutoTokenizer.from_pretrained")
    @patch.object(MultiModalAI, "_load_models")
    @patch("src.models.get_optimal_dtype", return_value="float32")
    def test_mode_specific_adapter_paths_register_aliases(
        self,
        mock_dtype,
        mock_load_models,
        mock_tokenizer,
        mock_model_loader,
        mock_compile,
        mock_warm_up,
        mock_quantization,
    ):
        """Six runtime modes should resolve to the expected adapter aliases."""
        fake_tokenizer = MagicMock()
        fake_tokenizer.pad_token = "<pad>"
        fake_tokenizer.eos_token = "</s>"
        mock_tokenizer.return_value = fake_tokenizer

        fake_base_model = MagicMock()
        fake_base_model.load_adapter = MagicMock()
        fake_base_model.set_adapter = MagicMock()
        fake_adapter_model = MagicMock()
        fake_adapter_model.load_adapter = MagicMock()
        fake_adapter_model.set_adapter = MagicMock()
        mock_model_loader.return_value = fake_base_model

        with patch.dict(
            os.environ,
            {
                "AAIS_ENABLE_TEXT_ADAPTERS": "1",
                "AAIS_TEXT_ADAPTER_FAST_PATH": "training/out/jarvis-fast/final",
                "AAIS_TEXT_ADAPTER_THINK_PATH": "training/out/jarvis-think/final",
            },
            clear=False,
        ):
            ai = MultiModalAI(device="cpu")
            with patch.object(ai, "_load_text_adapter", return_value=fake_adapter_model) as mock_adapter:
                ai._load_text_model()
                ai._select_text_adapter("think")

        mock_adapter.assert_called_once_with(
            "training/out/jarvis-fast/final",
            adapter_name="fast",
        )
        self.assertEqual(
            fake_adapter_model.load_adapter.call_args_list,
            [
                unittest.mock.call(
                    "training/out/jarvis-think/final",
                    adapter_name="think",
                    is_trainable=False,
                ),
                unittest.mock.call(
                    "training/out/jarvis-think/final",
                    adapter_name="debug",
                    is_trainable=False,
                ),
                unittest.mock.call(
                    "training/out/jarvis-think/final",
                    adapter_name="research",
                    is_trainable=False,
                ),
            ],
        )
        self.assertEqual(ai.text_adapter_aliases["builder"], "fast")
        self.assertEqual(ai.text_adapter_aliases["operator"], "fast")
        self.assertEqual(ai.text_adapter_aliases["debug"], "debug")
        self.assertEqual(ai.text_adapter_aliases["research"], "research")
        fake_adapter_model.set_adapter.assert_called_once_with("think")

    @patch.object(MultiModalAI, "_load_models")
    @patch("src.models.get_optimal_dtype", return_value="float32")
    def test_generate_chat_retries_when_first_pass_echoes_prompt(
        self,
        mock_dtype,
        mock_load_models,
    ):
        """Prompt-echo outputs should trigger a compact retry before returning."""
        ai = MultiModalAI(device="cpu")
        ai.text_model = MagicMock()
        ai.text_tokenizer = MagicMock()
        ai._select_text_adapter = MagicMock()

        with patch("src.models.render_messages_for_model", side_effect=["full prompt", "retry prompt"]):
            with patch.object(
                ai,
                "_generate_from_rendered_prompt",
                side_effect=[
                    "system\nJarvis runtime state:\n- active_mode: explore",
                    "Think mode is live and answering directly.",
                ],
            ) as mock_generate:
                response = ai.generate_chat(
                    [{"role": "user", "content": "Help me confirm Think mode is live."}],
                    response_mode="think",
                )

        self.assertEqual(response, "Think mode is live and answering directly.")
        self.assertEqual(mock_generate.call_count, 2)

    @patch.object(MultiModalAI, "_load_models")
    @patch("src.models.get_optimal_dtype", return_value="float32")
    def test_generate_chat_uses_model_route_profile(
        self,
        mock_dtype,
        mock_load_models,
    ):
        """Turn-level model routes should influence adapter selection and decoding settings."""
        ai = MultiModalAI(device="cpu")
        ai.text_model = MagicMock()
        ai.text_tokenizer = MagicMock()
        ai._select_text_adapter = MagicMock()

        with patch("src.models.render_messages_for_model", return_value="full prompt"):
            with patch.object(
                ai,
                "_generate_from_rendered_prompt",
                return_value="Debug mode found the likeliest break point.",
            ) as mock_generate:
                response = ai.generate_chat(
                    [{"role": "user", "content": "Debug api.py."}],
                    response_mode="debug",
                    routing_profile={
                        "id": "bug_hunter",
                        "adapter_mode": "debug",
                        "generation_overrides": {
                            "temperature_max": 0.12,
                            "repetition_penalty": 1.13,
                            "input_max_length": 2176,
                            "no_repeat_ngram_size": 4,
                        },
                    },
                )

        self.assertEqual(response, "Debug mode found the likeliest break point.")
        ai._select_text_adapter.assert_called_once_with("debug")
        self.assertEqual(mock_generate.call_args.kwargs["temperature"], 0.12)
        self.assertEqual(mock_generate.call_args.kwargs["repetition_penalty"], 1.13)
        self.assertEqual(mock_generate.call_args.kwargs["input_max_length"], 2176)
        self.assertEqual(mock_generate.call_args.kwargs["no_repeat_ngram_size"], 4)

    @patch.object(MultiModalAI, "_load_models")
    @patch("src.models.get_optimal_dtype", return_value="float32")
    def test_generate_chat_preserves_last_generation_metadata(
        self,
        mock_dtype,
        mock_load_models,
    ):
        """Chat generation should retain finish metadata for the output completion guard."""
        ai = MultiModalAI(device="cpu")
        ai.text_model = MagicMock()
        ai.text_tokenizer = MagicMock()
        ai._select_text_adapter = MagicMock()

        def fake_generate(*args, **kwargs):
            del args, kwargs
            ai.last_generation_metadata = {
                "stop_reason": "max_new_tokens",
                "finish_reason": "length",
                "input_tokens": 96,
                "output_tokens": 64,
                "output_token_budget": 64,
            }
            return "The reply ended near the budget edge"

        with patch("src.models.render_messages_for_model", return_value="prompt"):
            with patch.object(ai, "_generate_from_rendered_prompt", side_effect=fake_generate):
                response = ai.generate_chat(
                    [{"role": "user", "content": "Keep the reply complete."}],
                    max_length=64,
                    response_mode="think",
                )

        self.assertEqual(response, "The reply ended near the budget edge")
        self.assertEqual(ai.last_generation_metadata["stop_reason"], "max_new_tokens")
        self.assertEqual(ai.last_generation_metadata["finish_reason"], "length")
        self.assertEqual(ai.last_generation_metadata["output_tokens"], 64)
        self.assertEqual(ai.last_generation_metadata["output_token_budget"], 64)

    def test_chat_generation_profile_accepts_route_overrides(self):
        """Route overrides should tighten the base response-mode profile."""
        profile = MultiModalAI._chat_generation_profile(
            response_mode="builder",
            temperature=0.7,
            max_length=200,
            routing_profile={
                "generation_overrides": {
                    "temperature_max": 0.18,
                    "min_new_tokens_floor": 40,
                    "repetition_penalty": 1.12,
                    "input_max_length": 2048,
                    "no_repeat_ngram_size": 4,
                }
            },
        )

        self.assertEqual(profile["temperature"], 0.18)
        self.assertGreaterEqual(profile["min_new_tokens"], 40)
        self.assertEqual(profile["repetition_penalty"], 1.12)
        self.assertEqual(profile["input_max_length"], 2048)
        self.assertEqual(profile["no_repeat_ngram_size"], 4)

    def test_build_grounded_image_description_uses_matches_colors_and_size(self):
        """Grounded image summaries should mention labels, colors, and image shape."""
        description = MultiModalAI._build_grounded_image_description(
            [
                {"label": "screenshot", "score": 0.62},
                {"label": "code", "score": 0.24},
                {"label": "text-heavy", "score": 0.08},
            ],
            [
                {"hex": "#102132", "share": 0.41},
                {"hex": "#F8FAFC", "share": 0.31},
            ],
            (1440, 900),
        )

        self.assertIn("landscape", description)
        self.assertIn("screenshot", description)
        self.assertIn("#102132", description)
        self.assertIn("1440x900", description)


if __name__ == "__main__":
    unittest.main()

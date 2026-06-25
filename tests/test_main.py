"""Tests for main module."""

import os
import unittest
from unittest.mock import patch

from src.main import apply_runtime_preset, config, main, parse_args


class TestMain(unittest.TestCase):
    """Test cases for main module."""

    def test_parse_args_uses_defaults(self):
        """Test CLI parsing defaults."""
        args = parse_args([])

        self.assertEqual(args.mode, "api")
        self.assertEqual(args.host, "0.0.0.0")
        self.assertEqual(args.port, 5000)
        self.assertEqual(args.preset, "default")

    def test_apply_runtime_preset_sets_laptop_defaults(self):
        """Laptop preset should set lightweight defaults."""
        preset_keys = set()
        for values in apply_runtime_preset.__globals__["RUNTIME_PRESETS"].values():
            preset_keys.update(values.keys())

        with patch.dict(os.environ, {}, clear=False):
            for key in preset_keys:
                os.environ.pop(key, None)

            applied = apply_runtime_preset("laptop")

            self.assertEqual(os.environ["AAIS_MODEL_MODE"], "real")
            self.assertEqual(os.environ["AAIS_MODEL_PROFILE"], "lite")
            self.assertEqual(
                os.environ["AAIS_TEXT_MODEL_NAME"],
                "Qwen/Qwen2.5-0.5B-Instruct",
            )
            self.assertEqual(os.environ["AAIS_HF_LOCAL_ONLY"], "1")
            self.assertEqual(os.environ["AAIS_DISABLE_IMAGE_GENERATION"], "true")
            self.assertEqual(os.environ["AAIS_DEFAULT_MAX_LENGTH"], "96")
            self.assertEqual(os.environ["AAIS_MAX_TEXT_TOKENS"], "160")
            self.assertEqual(os.environ["AAIS_RESPONSE_TOKEN_SCALE"], "0.25")
            self.assertEqual(os.environ["AAIS_DEFAULT_TEMPERATURE"], "0.6")
            self.assertEqual(os.environ["AAIS_ENABLE_TEXT_ADAPTERS"], "0")
            self.assertEqual(os.environ["QUANTIZATION"], "int4")
            self.assertEqual(os.environ["SKIP_WARMUP"], "true")
            self.assertEqual(os.environ["DISABLE_TORCH_COMPILE"], "true")
            self.assertEqual(os.environ["MODEL_PRECISION"], "fp16")
            self.assertIn("AAIS_MODEL_MODE", applied)

    def test_apply_runtime_preset_sets_default_real_bootstrap(self):
        """Default Infinity preset should opt into real AI bootstrap (not auto-mock)."""
        preset_keys = set()
        for values in apply_runtime_preset.__globals__["RUNTIME_PRESETS"].values():
            preset_keys.update(values.keys())

        with patch.dict(os.environ, {}, clear=False):
            for key in preset_keys:
                os.environ.pop(key, None)

            applied = apply_runtime_preset("default")

            self.assertEqual(os.environ["AAIS_MODEL_MODE"], "real")
            self.assertEqual(os.environ["AAIS_BOOTSTRAP_REAL_AT_STARTUP"], "1")
            self.assertIn("AAIS_MODEL_MODE", applied)

    def test_apply_runtime_preset_sets_production_strict(self):
        """Production preset should disable mock fallback and mark environment production."""
        preset_keys = set()
        for values in apply_runtime_preset.__globals__["RUNTIME_PRESETS"].values():
            preset_keys.update(values.keys())

        with patch.dict(os.environ, {}, clear=False):
            for key in preset_keys:
                os.environ.pop(key, None)

            applied = apply_runtime_preset("production")

            self.assertEqual(os.environ["ENVIRONMENT"], "production")
            self.assertEqual(os.environ["AAIS_MODEL_MODE"], "real")
            self.assertEqual(os.environ["AAIS_ALLOW_STARTUP_FALLBACK"], "0")
            self.assertEqual(os.environ["AAIS_BOOTSTRAP_REAL_AT_STARTUP"], "1")
            self.assertEqual(os.environ["AAIS_HEALTH_SKIP_CONTRACTOR_PROBES"], "1")
            self.assertEqual(os.environ["AAIS_MESH_ENABLED"], "0")
            self.assertEqual(os.environ["AAIS_MODEL_PROFILE"], "lite")
            self.assertEqual(
                os.environ["AAIS_TEXT_MODEL_NAME"],
                "Qwen/Qwen2.5-0.5B-Instruct",
            )
            self.assertIn("ENVIRONMENT", applied)

    def test_apply_runtime_preset_preserves_explicit_env(self):
        """Preset defaults should not override explicit env vars."""
        with patch.dict(
            os.environ,
            {"AAIS_MODEL_MODE": "mock", "AAIS_MODEL_PROFILE": "custom"},
            clear=False,
        ):
            applied = apply_runtime_preset("laptop")

            self.assertEqual(os.environ["AAIS_MODEL_MODE"], "mock")
            self.assertEqual(os.environ["AAIS_MODEL_PROFILE"], "custom")
            self.assertNotIn("AAIS_MODEL_MODE", applied)
            self.assertNotIn("AAIS_MODEL_PROFILE", applied)

    @patch("src.main.run_api")
    def test_main_runs_api_mode(self, mock_run_api):
        """Test API mode delegates to the Flask runner."""
        result = main(["--mode", "api", "--host", "127.0.0.1", "--port", "5050"])

        self.assertEqual(result, "api")
        mock_run_api.assert_called_once_with(
            host="127.0.0.1",
            port=5050,
            debug=config.DEBUG,
        )

    @patch("src.main.run_api")
    def test_main_cli_mode_skips_server_start(self, mock_run_api):
        """Test CLI mode does not start the API server."""
        result = main(["--mode", "cli"])

        self.assertEqual(result, "cli")
        mock_run_api.assert_not_called()

if __name__ == "__main__":
    unittest.main()

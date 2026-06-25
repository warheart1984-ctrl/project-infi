"""Tests for scripts/preflight_production_ai.py."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO = Path(__file__).resolve().parents[1]
_PREFLIGHT = _REPO / "scripts" / "preflight_production_ai.py"


def _load_preflight_main():
    spec = importlib.util.spec_from_file_location("preflight_production_ai", _PREFLIGHT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.main


class TestPreflightProductionAi(unittest.TestCase):
    def setUp(self):
        self._argv_patch = patch.object(sys, "argv", ["preflight_production_ai.py"])
        self._argv_patch.start()

    def tearDown(self):
        self._argv_patch.stop()

    def test_passes_when_remote_providers_configured(self):
        main = _load_preflight_main()
        with patch("src.api._configured_remote_providers", return_value=["openrouter"]):
            with patch("src.provider_registry.provider_registry") as mock_reg:
                mock_reg.refresh = MagicMock()
                mock_reg.list_status = MagicMock(return_value=[])
                with patch("dotenv.load_dotenv"):
                    self.assertEqual(main(), 0)

    def test_passes_when_torch_available_no_remote(self):
        main = _load_preflight_main()
        with patch("src.api._configured_remote_providers", return_value=[]):
            with patch("src.provider_registry.provider_registry") as mock_reg:
                mock_reg.refresh = MagicMock()
                mock_reg.list_status = MagicMock(return_value=[])
                with patch("dotenv.load_dotenv"):
                    import builtins

                    real_import = builtins.__import__

                    def fake_import(name, *args, **kwargs):
                        if name == "torch":
                            return MagicMock()
                        return real_import(name, *args, **kwargs)

                    with patch("builtins.__import__", side_effect=fake_import):
                        self.assertEqual(main(), 0)

    def test_fails_when_no_remote_and_no_torch(self):
        main = _load_preflight_main()
        with patch("src.api._configured_remote_providers", return_value=[]):
            with patch("src.provider_registry.provider_registry") as mock_reg:
                mock_reg.refresh = MagicMock()
                mock_reg.list_status = MagicMock(return_value=[])
                with patch("dotenv.load_dotenv"):
                    import builtins

                    real_import = builtins.__import__

                    def fake_import(name, *args, **kwargs):
                        if name == "torch":
                            raise ImportError("No module named 'torch'")
                        return real_import(name, *args, **kwargs)

                    with patch("builtins.__import__", side_effect=fake_import):
                        self.assertEqual(main(), 1)

    def test_production_preset_uses_lite_model_resolution(self):
        main = _load_preflight_main()
        with patch("src.api._configured_remote_providers", return_value=[]):
            with patch("src.provider_registry.provider_registry") as mock_reg:
                mock_reg.refresh = MagicMock()
                mock_reg.list_status = MagicMock(return_value=[])
                with patch("dotenv.load_dotenv"):
                    with patch("src.main.apply_runtime_preset") as mock_preset:
                        import builtins

                        real_import = builtins.__import__

                        def fake_import(name, *args, **kwargs):
                            if name == "torch":
                                return MagicMock()
                            return real_import(name, *args, **kwargs)

                        with patch("builtins.__import__", side_effect=fake_import):
                            with patch.object(sys, "argv", ["preflight_production_ai.py", "--preset", "production"]):
                                self.assertEqual(main(), 0)
                        mock_preset.assert_called_once_with("production")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from src.imagine_grok import (
    KeysRequiredError,
    grok_render_pattern,
    grok_render_path,
    keys_status,
    resolve_xai_api_key,
)
from src.imagine_generator import build_pattern_from_fixture, persist_pattern


class FakeTransport:
    def post_json(self, url, body, headers, timeout_seconds):
        return {
            "data": [
                {
                    "b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                }
            ]
        }


class TestImagineGrok(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="imagine_grok_test_"))
        self.imagine_root = self.temp_root / "imagine"
        for key in ("STORY_FORGE_XAI_API_KEY", "XAI_API_KEY"):
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)
        for key in ("STORY_FORGE_XAI_API_KEY", "XAI_API_KEY"):
            os.environ.pop(key, None)

    def test_keys_status_without_env(self) -> None:
        status = keys_status()
        self.assertFalse(status["configured"])
        self.assertIsNone(resolve_xai_api_key())

    def test_grok_render_requires_env_key(self) -> None:
        pattern = build_pattern_from_fixture("scene-seed-demo")
        with self.assertRaises(KeysRequiredError):
            grok_render_pattern(pattern, imagine_root=self.imagine_root)

    def test_grok_render_with_mock_transport(self) -> None:
        os.environ["XAI_API_KEY"] = "test-key-not-real"
        pattern = build_pattern_from_fixture("scene-seed-demo")
        persist_pattern(pattern, root=self.imagine_root)
        result = grok_render_pattern(
            pattern,
            transport=FakeTransport(),
            imagine_root=self.imagine_root,
        )
        self.assertEqual(result["status"], "rendered")
        path = grok_render_path(pattern["pattern_id"], imagine_root=self.imagine_root)
        self.assertTrue(path.is_file())
        artifact = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["provider"], "xai")
        self.assertEqual(artifact["image_count"], 1)


class TestImagineGrokAPI(unittest.TestCase):
    def test_keys_status_endpoint(self) -> None:
        import src.api as api

        with api.app.test_client() as client:
            response = client.get("/api/jarvis/imagine/keys-status")
            self.assertEqual(response.status_code, 200)
            body = response.get_json()
            self.assertIn("configured", body)
            self.assertIn("env_vars", body)

    def test_grok_render_endpoint_keys_required(self) -> None:
        import src.api as api

        for key in ("STORY_FORGE_XAI_API_KEY", "XAI_API_KEY"):
            os.environ.pop(key, None)
        with api.app.test_client() as client:
            emit = client.post(
                "/api/jarvis/imagine/emit",
                json={"fixture": "scene-seed-demo"},
            )
            pattern_id = emit.get_json()["pattern"]["pattern_id"]
            grok = client.post(
                "/api/jarvis/imagine/grok-render",
                json={"pattern_id": pattern_id},
            )
            self.assertEqual(grok.status_code, 428)
            self.assertEqual(grok.get_json()["error"], "keys_required")


if __name__ == "__main__":
    unittest.main()

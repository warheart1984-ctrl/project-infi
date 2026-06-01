from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main as app_main


class TestPackagedFrontend(unittest.TestCase):
    def test_root_redirects_to_packaged_frontend_when_modern_bundle_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            static_dir = Path(temp_dir)
            (static_dir / "assets").mkdir()
            (static_dir / "index.html").write_text("<html><body>AAIS App</body></html>", encoding="utf-8")

            with patch.object(app_main, "STATIC_DIR", static_dir):
                with TestClient(app_main.app) as client:
                    response = client.get("/", follow_redirects=False)

            self.assertEqual(response.status_code, 307)
            self.assertEqual(response.headers["location"], app_main.APP_SHELL_BASE_PATH)

    def test_packaged_frontend_serves_assets_and_spa_routes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            static_dir = Path(temp_dir)
            (static_dir / "assets").mkdir()
            (static_dir / "index.html").write_text("<html><body>AAIS App</body></html>", encoding="utf-8")
            (static_dir / "assets" / "main.js").write_text("console.log('bundle');", encoding="utf-8")

            with patch.object(app_main, "STATIC_DIR", static_dir):
                with TestClient(app_main.app) as client:
                    asset_response = client.get(f"{app_main.APP_SHELL_BASE_PATH}/assets/main.js")
                    route_response = client.get(f"{app_main.APP_SHELL_BASE_PATH}/workflows")

            self.assertEqual(asset_response.status_code, 200)
            self.assertIn("console.log('bundle');", asset_response.text)
            self.assertEqual(route_response.status_code, 200)
            self.assertIn("AAIS App", route_response.text)


if __name__ == "__main__":
    unittest.main()

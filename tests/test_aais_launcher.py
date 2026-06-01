from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aais import launcher


class TestAAISLauncher(unittest.TestCase):
    def test_prepare_frontend_bundle_promotes_build_into_packaged_static_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_dir = root / "frontend" / "build"
            static_dir = root / "app" / "static"

            (build_dir / "assets").mkdir(parents=True)
            static_dir.mkdir(parents=True)
            (build_dir / "index.html").write_text("<html>modern bundle</html>", encoding="utf-8")
            (build_dir / "assets" / "main.js").write_text("console.log('ready');", encoding="utf-8")
            (static_dir / "index.html").write_text("<html>legacy placeholder</html>", encoding="utf-8")

            prepared_dir = launcher.prepare_frontend_bundle(root, "/app")

            self.assertEqual(prepared_dir, static_dir)
            self.assertTrue((static_dir / "assets" / "main.js").exists())
            self.assertIn("modern bundle", (static_dir / "index.html").read_text(encoding="utf-8"))

    def test_normalize_argv_defaults_to_start_command(self):
        self.assertEqual(launcher.normalize_argv([]), ["start"])
        self.assertEqual(launcher.normalize_argv(["--help"]), ["--help"])
        self.assertEqual(launcher.normalize_argv(["--port", "8100"]), ["start", "--port", "8100"])
        self.assertEqual(launcher.normalize_argv(["prepare"]), ["prepare"])

    def test_normalize_app_base_defaults_to_app(self):
        self.assertEqual(launcher.normalize_app_base(None), "/app")
        self.assertEqual(launcher.normalize_app_base("/"), "/")
        self.assertEqual(launcher.normalize_app_base("custom"), "/custom")


if __name__ == "__main__":
    unittest.main()

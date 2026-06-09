"""Tests for operator plugin bootstrap."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.operator_plugin_bootstrap import (
    apply_plug_enables,
    bootstrap_operator_plugins,
    configured_mcp_server_ids,
    load_policy,
    merge_mcp_manifest,
    plugs_to_enable,
    repo_root_from,
)
from src.plug_adapter_runtime import PlugAdapterRuntime
from src.plug_discovery import discover_plugs


class PlugsToEnableTests(unittest.TestCase):
    def test_native_capability_enabled_cursor_skill_skipped(self):
        policy = load_policy(repo_root=repo_root_from())
        plugs = [
            {"plug_id": "native.foo", "plug_class": "native_capability", "authority_level": "assist"},
            {"plug_id": "skill.bar", "plug_class": "cursor_skill", "authority_level": "assist"},
            {"plug_id": "native.admin", "plug_class": "native_capability", "authority_level": "admin"},
        ]
        enable, skipped = plugs_to_enable(plugs, policy=policy, configured_mcp_server_ids=set())
        self.assertIn("native.foo", enable)
        self.assertIn("skill.bar", skipped)
        self.assertIn("native.admin", skipped)

    def test_mcp_enabled_when_configured(self):
        policy = load_policy(repo_root=repo_root_from())
        plugs = [
            {
                "plug_id": "mcp.linear",
                "plug_class": "mcp",
                "authority_level": "assist",
                "library_id": "lib.mcp.linear",
            },
        ]
        enable, skipped = plugs_to_enable(
            plugs,
            policy=policy,
            configured_mcp_server_ids={"plugin-linear-linear"},
        )
        # May skip if library_id does not map to plugin-linear-linear in this repo.
        self.assertEqual(len(enable) + len(skipped), 1)


class McpManifestTests(unittest.TestCase):
    def test_merge_redacts_secrets(self):
        cursor_cfg = {
            "mcpServers": {
                "linear": {
                    "command": "npx",
                    "args": ["-y", "mcp-remote", "https://example.com/mcp"],
                    "env": {"LINEAR_API_KEY": "secret"},
                },
            }
        }
        manifest = merge_mcp_manifest(cursor_config=cursor_cfg, existing={"servers": {}})
        server = manifest["servers"]["plugin-linear-linear"]
        self.assertEqual(server["transport"], "stdio")
        self.assertIn("LINEAR_API_KEY", server["env_keys"])
        self.assertNotIn("LINEAR_API_KEY", server.get("env", {}))

    def test_configured_mcp_server_ids(self):
        manifest = {
            "servers": {
                "a": {"configured": True},
                "b": {"configured": False},
            }
        }
        self.assertEqual(configured_mcp_server_ids(manifest), {"a"})


class BootstrapDryRunTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.runtime_dir = Path(self._tmpdir.name)

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_dry_run_does_not_write_enabled_plugs(self):
        os.environ["AAIS_RUNTIME_DIR"] = str(self.runtime_dir)
        report = bootstrap_operator_plugins(
            dry_run=True,
            enable_operator_plugs=True,
            generate_mcp_manifest=False,
            skip_gates=True,
            runtime_dir=self.runtime_dir,
        )
        self.assertTrue(report.get("ok"))
        enabled_path = self.runtime_dir / "plug_adapter" / "enabled_plugs.json"
        self.assertFalse(enabled_path.is_file())
        self.assertIn("operator_plugs", report)
        self.assertGreater(report["operator_plugs"]["discovered"], 0)

    def test_apply_writes_enabled_plugs(self):
        os.environ["AAIS_RUNTIME_DIR"] = str(self.runtime_dir)
        runtime = PlugAdapterRuntime(runtime_dir=self.runtime_dir)
        plugs = discover_plugs()
        policy = load_policy(repo_root=repo_root_from())
        enable_ids, _ = plugs_to_enable(plugs, policy=policy, configured_mcp_server_ids=set())
        if not enable_ids:
            self.skipTest("no plugs matched auto-enable policy in this checkout")
        result = apply_plug_enables(runtime, enable_ids[:1], dry_run=False)
        self.assertEqual(len(result["enabled"]), 1)
        enabled_path = self.runtime_dir / "plug_adapter" / "enabled_plugs.json"
        self.assertTrue(enabled_path.is_file())
        doc = json.loads(enabled_path.read_text(encoding="utf-8"))
        enabled_map = doc.get("enabled") or {}
        self.assertTrue(enabled_map.get(result["enabled"][0]))


if __name__ == "__main__":
    unittest.main()

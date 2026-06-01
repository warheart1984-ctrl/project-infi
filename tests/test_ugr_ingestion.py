"""Tests for UGR Phase 3 governed ingestion."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.ingestion.config import IngestionConfig
from src.ugr.ingestion.invariants import validate_proposal
from src.ugr.ingestion.pipeline import GovernedIngestionPipeline
from src.ugr.ingestion.sanitize import contains_blocked_secret, sanitize_text
from src.ugr.pattern_ledger import PatternLedgerStore


SAMPLE_RELEASES = [
    {
        "source_uri": "https://github.com/python/cpython/releases/tag/v3.13.0",
        "title": "Python 3.13.0",
        "summary": "New release with improved runtime performance.",
        "published_at": "2026-01-01T00:00:00+00:00",
        "tags": ["release"],
        "actors": ["python"],
    }
]

SAMPLE_ARXIV = [
    {
        "source_uri": "http://arxiv.org/abs/2601.00001",
        "title": "Governed Cognitive Runtimes",
        "summary": "We study runtime governance for multi-agent systems.",
        "published_at": "2026-01-02T00:00:00+00:00",
        "tags": ["cs.AI"],
        "actors": ["arxiv"],
    }
]


class TestUGRIngestionSanitize(unittest.TestCase):
    def test_secret_patterns_are_blocked(self):
        self.assertTrue(contains_blocked_secret("api_key=super-secret-value"))
        cleaned = sanitize_text("Contact user@example.com about api_key=abc")
        self.assertIn("[redacted-email]", cleaned)
        self.assertIn("[redacted-secret]", cleaned)


class TestUGRIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-ingest-"))
        self.config_path = self.temp_root / "sources.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "config_version": "0.1",
                    "sources": {
                        "test_github": {
                            "type": "github_releases",
                            "enabled": True,
                            "tenant_scope": "global",
                            "repo": "python/cpython",
                            "limit": 1,
                        },
                        "disabled_rss": {
                            "type": "rss",
                            "enabled": False,
                            "tenant_scope": "global",
                            "url": "https://example.com/feed.xml",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        self.pipeline = GovernedIngestionPipeline(
            config=IngestionConfig(self.config_path),
            ledger=PatternLedgerStore(runtime_dir=self.temp_root),
            runtime_root=self.temp_root,
            fetch_fn=lambda _source: [],
        )

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_dry_run_does_not_write_claims(self):
        result = self.pipeline.run_source("test_github", dry_run=True, records=SAMPLE_RELEASES)
        self.assertEqual(result.status, "ok")
        self.assertGreater(result.accepted_count, 0)
        self.assertFalse(list(self.temp_root.glob("**/claims.jsonl")))

    def test_ingestion_writes_claims_with_provenance(self):
        result = self.pipeline.run_source("test_github", records=SAMPLE_RELEASES)
        self.assertEqual(result.status, "ok")
        claims = PatternLedgerStore(runtime_dir=self.temp_root).read_claims()
        self.assertTrue(claims)
        self.assertTrue(all(row.get("source_lane") == "ingestion" for row in claims))

    def test_disabled_source_is_rejected(self):
        result = self.pipeline.run_source("disabled_rss", records=SAMPLE_ARXIV)
        self.assertEqual(result.status, "rejected")

    def test_secret_payload_is_quarantined(self):
        bad_records = [
            {
                **SAMPLE_ARXIV[0],
                "summary": "Leak api_key=totally-real-secret-token",
            }
        ]
        result = self.pipeline.run_source("test_github", records=bad_records)
        self.assertIn(result.status, {"quarantined", "no_accepted_proposals"})
        self.assertEqual(result.accepted_count, 0)

    def test_validate_proposal_requires_provenance(self):
        source = IngestionConfig(self.config_path).get("test_github")
        assert source is not None
        gate = validate_proposal({"claim": {"subject": "x", "predicate": "y", "object": "z", "confidence": 0.5}}, source)
        self.assertFalse(gate["allows"])


class TestUGRIngestionConfig(unittest.TestCase):
    def test_default_config_has_enabled_sources(self):
        config = IngestionConfig()
        if config.path.exists():
            enabled = config.enabled_sources()
            self.assertTrue(any(source.source_id == "arxiv_cs_ai" for source in enabled))


if __name__ == "__main__":
    unittest.main()

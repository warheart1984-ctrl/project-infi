from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.cloud_forge.cache import (
    CloudForgeCacheStore,
    build_l1_key,
    effective_cache_mode,
    persist_cache_outcomes,
    resolve_cache,
)
from src.cloud_forge.cache_bridge import bridge_l0_get, bridge_l0_set, l0_context_from_env
from src.cloud_forge.integration import schedule_request_observed
from src.cloud_forge.templates import DOMAIN_FORGE_VOSS_OS
from src.cloud_forge.types import LawEnvelope, TaskSignature


def _law() -> LawEnvelope:
    return LawEnvelope(
        law_id="meta.architect.v1",
        law_version="2026-05-28",
        signals=["read_only", "docs"],
    )


def _task(**overrides) -> TaskSignature:
    base = {
        "task_id": "t-cache-1",
        "pattern_class": "docs_explanation",
        "mutation_scope": "none",
        "domain": DOMAIN_FORGE_VOSS_OS,
        "normalized_prompt_hash": "sha256:question-abc",
    }
    base.update(overrides)
    return TaskSignature.from_dict(base)


class CloudForgeCacheKeyTests(unittest.TestCase):
    def test_l1_key_scoped_by_tenant_and_law(self) -> None:
        k1 = build_l1_key("tenant-a", "law.a", "v1", "What is Voss?")
        k2 = build_l1_key("tenant-b", "law.a", "v1", "What is Voss?")
        k3 = build_l1_key("tenant-a", "law.b", "v1", "What is Voss?")
        self.assertNotEqual(k1, k2)
        self.assertNotEqual(k1, k3)

    def test_effective_cache_mode_respects_law_ceiling(self) -> None:
        law = LawEnvelope(
            law_id="x",
            law_version="1",
            forbid_cache_above="L0",
        )
        self.assertEqual(effective_cache_mode("L2", law), "L0")


class CloudForgeCacheStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.store = CloudForgeCacheStore(Path(self._tmp.name) / "cache")

    def test_l0_roundtrip(self) -> None:
        self.store.l0_set("t1", _law(), "calculator", "2+2", "4")
        self.assertEqual(self.store.l0_get("t1", _law(), "calculator", "2+2"), "4")
        self.assertIsNone(self.store.l0_get("t2", _law(), "calculator", "2+2"))

    def test_l1_roundtrip_and_law_version_mismatch(self) -> None:
        self.store.l1_set("t1", _law(), "sha256:q1", "answer-one")
        hit = self.store.l1_get("t1", _law(), "sha256:q1")
        self.assertEqual(hit["answer"], "answer-one")

        other_law = LawEnvelope(law_id="meta.architect.v1", law_version="2099-01-01")
        self.assertIsNone(self.store.l1_get("t1", other_law, "sha256:q1"))

    def test_l2_plan_roundtrip(self) -> None:
        plan = {"steps": ["PLAN_TOOLS", "FINAL"], "cache_mode": "L2"}
        self.store.l2_set("t1", _law(), _task(), plan)
        hit = self.store.l2_get("t1", _law(), _task())
        self.assertEqual(hit["cognition_plan"]["steps"], ["PLAN_TOOLS", "FINAL"])

    def test_flush_tenant_scoped(self) -> None:
        self.store.l1_set("t1", _law(), "q-a", "a1")
        self.store.l1_set("t2", _law(), "q-b", "b1")
        removed = self.store.flush(tenant_id="t1", layers=("L1",))
        self.assertGreaterEqual(removed, 1)
        self.assertIsNone(self.store.l1_get("t1", _law(), "q-a"))
        self.assertIsNotNone(self.store.l1_get("t2", _law(), "q-b"))

    def test_resolve_l2_before_l1(self) -> None:
        self.store.l1_set("t1", _law(), "sha256:question-abc", "cached-answer")
        self.store.l2_set("t1", _law(), _task(), {"steps": ["PLAN_TOOLS", "FINAL"]})
        resolution = resolve_cache(
            tenant_id="t1",
            law=_law(),
            task=_task(),
            cache_mode="L2",
            store=self.store,
            normalized_question="sha256:question-abc",
        )
        self.assertEqual(resolution["status"], "hit")
        self.assertEqual(resolution["layer"], "L2")


class CloudForgeCacheBridgeTests(unittest.TestCase):
    def test_l0_bridge_via_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "CLOUD_FORGE_CACHE_ROOT": str(Path(tmp) / "cache"),
                "CLOUD_FORGE_TENANT_ID": "bridge-tenant",
                "CLOUD_FORGE_LAW_ID": "meta.architect.v1",
                "CLOUD_FORGE_LAW_VERSION": "2026-05-28",
            }
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertIsNotNone(l0_context_from_env())
                bridge_l0_set("calculator", "1+1", "2")
                self.assertEqual(bridge_l0_get("calculator", "1+1"), "2")


class CloudForgeCacheIntegrationTests(unittest.TestCase):
    def test_observed_cache_hit_l1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_root = Path(tmp) / "cache"
            ledger_path = Path(tmp) / "rail.jsonl"
            store = CloudForgeCacheStore(cache_root)
            store.l1_set(
                "tenant-x",
                _law(),
                "sha256:question-abc",
                "Prior governed answer.",
            )
            env = {
                "CLOUD_FORGE_CACHE_ROOT": str(cache_root),
                "CLOUD_FORGE_LEDGER_PATH": str(ledger_path),
            }
            with mock.patch.dict(os.environ, env, clear=False):
                bundle = schedule_request_observed(
                    task=_task(),
                    actor={"wL": 120},
                    tenant={"latency_bias": 0.4},
                    law_envelope={
                        "law_id": "meta.architect.v1",
                        "law_version": "2026-05-28",
                        "signals": ["read_only", "docs", "governance"],
                    },
                    tenant_id="tenant-x",
                    log_ledger=False,
                    cache_store=store,
                    normalized_question="sha256:question-abc",
                )
            self.assertEqual(bundle["cache_resolution"]["status"], "hit")
            self.assertEqual(bundle["cache_resolution"]["layer"], "L1")
            self.assertEqual(bundle["cached_answer"], "Prior governed answer.")

    def test_persist_after_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CloudForgeCacheStore(Path(tmp) / "cache")
            persisted = persist_cache_outcomes(
                tenant_id="t1",
                law=_law(),
                task=_task(),
                cache_mode="L2",
                cognition_plan={"steps": ["PLAN_TOOLS", "FINAL"], "cache_mode": "L2"},
                store=store,
                store_answer="final answer text",
                store_plan=True,
                normalized_question="sha256:question-abc",
            )
            self.assertEqual(len(persisted["layers"]), 2)
            resolution = resolve_cache(
                tenant_id="t1",
                law=_law(),
                task=_task(),
                cache_mode="L2",
                store=store,
                normalized_question="sha256:question-abc",
            )
            self.assertEqual(resolution["layer"], "L2")


if __name__ == "__main__":
    unittest.main()

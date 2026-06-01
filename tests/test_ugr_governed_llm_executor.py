"""Tests for governed LLM provider execution commit layer."""

import os
import unittest
from typing import Any

from src.aais_governed_llm_module import propose_governed_llm_envelope
from src.jarvis_protocol import ProviderResponse
from src.jarvis_provider_registry import ProviderConfig
from src.provider_registry import ProviderRegistry
from src.ugr.governed_llm_executor import (
    build_messages_for_proposal,
    execute_governed_llm_proposal,
    llm_execution_enabled,
)
from src.ugr.llm_lane import build_bridge_result_for_llm_lane, run_governed_llm_lane
from src.ugr.lane_manager import LaneSpec


class _MockProvider:
    async def invoke(self, messages, **kwargs) -> ProviderResponse:
        del messages, kwargs
        return ProviderResponse(
            content="Mock governed inference: inspect orchestrator latency traces.",
            provider="mock",
            model="mock-model",
            input_tokens=8,
            output_tokens=16,
        )


class TestGovernedLLMExecutor(unittest.TestCase):
    def setUp(self):
        self.bridge_result = build_bridge_result_for_llm_lane(
            {
                "question": "What caused the latency spike?",
                "intent": "diagnose_runtime",
                "trace_id": "trace-exec-1",
            }
        )
        self.envelope = propose_governed_llm_envelope(self.bridge_result)
        self.registry = ProviderRegistry()
        self.registry._providers = {}
        self.registry._adapters = {}
        self.registry.register(
            ProviderConfig(name="local", display_name="Mock Local", enabled=True, is_default=True),
            adapter=_MockProvider(),
        )

    def tearDown(self):
        os.environ.pop("UGR_LLM_EXECUTE", None)

    def test_execution_disabled_by_default(self):
        result = execute_governed_llm_proposal(
            self.envelope,
            bridge_result=self.bridge_result,
            question="What caused the latency spike?",
            provider_registry_instance=self.registry,
        )
        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(result["reason"], "execution_disabled")

    def test_execution_runs_with_force_flag(self):
        result = execute_governed_llm_proposal(
            self.envelope,
            bridge_result=self.bridge_result,
            question="What caused the latency spike?",
            provider_registry_instance=self.registry,
            force_execute=True,
        )
        self.assertEqual(result["status"], "EXECUTED")
        self.assertIn("Mock governed inference", result["content"])
        self.assertGreater(result["tokens_used"], 0)

    def test_build_messages_for_proposal(self):
        messages = build_messages_for_proposal(
            question="latency spike",
            envelope=self.envelope,
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")


class TestGovernedLLMLaneExecution(unittest.TestCase):
    def setUp(self):
        self.spec = LaneSpec(lane_id="lane-llm-exec", lane_type="llm")
        self.shared_context = {
            "trace_id": "trace-exec-lane",
            "question": "Explain orchestrator restart impact",
            "intent": "diagnose_runtime",
            "context": {},
        }
        self.registry = ProviderRegistry()
        self.registry._providers = {}
        self.registry._adapters = {}
        self.registry.register(
            ProviderConfig(name="local", display_name="Mock Local", enabled=True, is_default=True),
            adapter=_MockProvider(),
        )

    def tearDown(self):
        os.environ.pop("UGR_LLM_EXECUTE", None)

    def test_lane_skips_execution_when_disabled(self):
        result = run_governed_llm_lane(
            self.spec,
            self.shared_context,
            provider_registry_instance=self.registry,
        )
        execution = result.payload.get("governed_llm_execution") or {}
        self.assertEqual(execution.get("status"), "SKIPPED")

    def test_lane_executes_with_force_execute(self):
        result = run_governed_llm_lane(
            self.spec,
            self.shared_context,
            provider_registry_instance=self.registry,
            force_execute=True,
        )
        execution = result.payload.get("governed_llm_execution") or {}
        self.assertEqual(execution.get("status"), "EXECUTED")
        self.assertGreater(result.metrics.get("tokens_used", 0), 0)
        claims = result.payload.get("claims") or []
        primary = next(item for item in claims if item.get("predicate") == "suggested_next_step")
        self.assertIn("Mock governed inference", primary.get("object"))


if __name__ == "__main__":
    unittest.main()

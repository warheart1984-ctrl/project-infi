"""Regression tests for deterministic prompt assembly cleanup."""

import unittest

from src.prompt_assembly import (
    PromptAssemblyIdentityError,
    assemble_prompt_blocks,
    combine_system_prompt,
    scrub_assistant_guidance_echo,
)


class TestPromptAssembly(unittest.TestCase):
    """Verify prompt assembly removes inflation and scaffold contamination."""

    def test_exact_duplicate_rules_collapse_to_one_canonical_block(self):
        """Exact duplicate instruction families should survive once by semantic identity."""
        guidance = (
            "You already gathered the evidence for this turn.\n"
            "Jarvis internal guidance for this turn:\n"
            "Keep the answer centered on the active repair."
        )

        blocks, report = assemble_prompt_blocks(
            [
                {"identity": "plan_guidance", "content": guidance},
                {"identity": "plan_guidance", "content": guidance},
            ],
            prompt_token_budget=256,
            reserved_response_budget=192,
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].identity, "plan_guidance")
        self.assertEqual(report.duplicates_removed, 1)
        self.assertEqual(report.identity_counts["plan_guidance"], 1)

    def test_clipped_duplicate_rule_is_rejected_before_assembly(self):
        """Malformed scaffold fragments should fail closed instead of surviving canonicalization."""
        clipped = (
            "You already gathered the evidence for this turn.\n"
            "Jarvis internal guidance for this turn:"
        )
        complete = (
            "You already gathered the evidence for this turn.\n"
            "Jarvis internal guidance for this turn:\n"
            "Ground the answer in this evidence: workspace context only."
        )

        blocks, report = assemble_prompt_blocks(
            [
                {"identity": "plan_guidance", "content": clipped},
                {"identity": "plan_guidance", "content": complete},
            ],
            prompt_token_budget=256,
            reserved_response_budget=192,
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(report.malformed_fragments_removed, 1)
        self.assertIn("Ground the answer in this evidence", combine_system_prompt(blocks))

    def test_scrub_assistant_guidance_echo_keeps_only_answer_body(self):
        """Assistant-visible scaffold text must not re-enter future assembly as fresh guidance."""
        echoed = (
            "Response Trace\n"
            "Memory Cues\n"
            "Keep the answer grounded.\n\n"
            "Give the quickest safe next step."
        )

        self.assertEqual(
            scrub_assistant_guidance_echo(echoed),
            "Give the quickest safe next step.",
        )
        self.assertEqual(
            scrub_assistant_guidance_echo("Mode: think\nFocus: repair the seam"),
            "",
        )

    def test_budget_first_assembly_drops_optional_context_before_required_guidance(self):
        """Reserved answer budget should be protected by dropping optional context first."""
        large_block = "Support detail. " * 120
        blocks, report = assemble_prompt_blocks(
            [
                {"identity": "system_seed", "content": "You are Jarvis.", "required": True, "priority": 0},
                {"identity": "runtime_directive", "content": "Jarvis runtime state:\n- current_focus: repair", "required": True, "priority": 10},
                {"identity": "plan_guidance", "content": "You already gathered the evidence for this turn.\nJarvis internal guidance for this turn:\nLead with the answer.", "required": True, "priority": 20},
                {"identity": "workspace_context", "content": large_block, "priority": 55},
                {"identity": "live_research", "content": large_block, "priority": 50},
            ],
            prompt_token_budget=80,
            reserved_response_budget=192,
        )

        identities = [block.identity for block in blocks]
        self.assertIn("system_seed", identities)
        self.assertIn("runtime_directive", identities)
        self.assertIn("plan_guidance", identities)
        self.assertGreaterEqual(report.budget_dropped, 1)
        self.assertLessEqual(report.chars_after_cleanup, report.prompt_token_budget * 4)

    def test_system_blocks_without_semantic_identity_fail_closed(self):
        """System guidance must declare a stable semantic identity instead of relying on fallback labels."""
        with self.assertRaises(PromptAssemblyIdentityError) as raised:
            assemble_prompt_blocks(
                [
                    {
                        "role": "system",
                        "channel": "instruction",
                        "source": "test_fixture",
                        "content": "You are Jarvis.",
                    }
                ],
                prompt_token_budget=256,
                reserved_response_budget=192,
            )
        message = str(raised.exception)
        self.assertIn("system guidance block", message)
        self.assertIn("semantic identity", message)
        self.assertIn("source_class=test_fixture", message)
        self.assertIn("prompt-assembly seam violation", message)

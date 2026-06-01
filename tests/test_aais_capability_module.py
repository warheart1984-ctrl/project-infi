"""Tests for the AAIS capability adapter base law."""

from pathlib import Path
import tempfile
import unittest

from src.aais_capability_module import (
    AAISCapabilityModule,
    AAISDocumentModule,
    AAISFileCapabilityModule,
    ERROR_TAXONOMY,
)


class DemoDocumentModule(AAISDocumentModule):
    """Simple test double for deterministic capability execution."""

    def __init__(self, result=None, exc: Exception | None = None):
        super().__init__(provider="demo_provider", model="demo-model")
        self._result = result
        self._exc = exc

    def _execute_provider(self, action: str, translated_payload: dict[str, object]):
        if self._exc:
            raise self._exc
        return self._result


class DemoFileModule(AAISFileCapabilityModule):
    """File-backed capability test double."""

    module_name = "document"
    supported_actions = ("summarize",)

    def _semantic_required_fields(self, action: str) -> tuple[str, ...]:
        return ("summary",)

    def _execute_provider(self, action: str, translated_payload: dict[str, object]):
        path = translated_payload["source_path"]
        return {"summary": f"Read {Path(path).name}"}


class TestAAISCapabilityModule(unittest.TestCase):
    """Verify the sealed translator contract and failure normalization."""

    def test_success_result_is_normalized_and_governance_friendly(self):
        """Valid provider output should return one AAIS-native success object."""
        module = DemoDocumentModule(result={"summary": "Short deterministic summary."})

        result = module.execute("summarize", {"content": "hello"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["module"], "document")
        self.assertEqual(result["action"], "summarize")
        self.assertEqual(result["data"]["summary"], "Short deterministic summary.")
        self.assertEqual(result["provider"], "demo_provider")
        self.assertEqual(result["model"], "demo-model")
        self.assertTrue(result["trace_id"].startswith("cap_"))
        self.assertGreater(result["meta"]["result_size"], 0)

    def test_timeout_becomes_deterministic_timeout_error(self):
        """Boundary timeouts should never leak raw exceptions."""
        module = DemoDocumentModule(exc=TimeoutError("slow provider"))

        result = module.execute("summarize", {"content": "hello"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertTrue(result["retryable"])
        self.assertIn("timed out", result["message"].lower())

    def test_missing_required_field_fails_semantic_guard(self):
        """Malformed but non-exceptional results should be rejected semantically."""
        module = DemoDocumentModule(result={"label": "summary_without_body"})

        result = module.execute("summarize", {"content": "hello"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "SchemaError")
        self.assertIn("missing required fields", result["message"].lower())

    def test_invalid_input_rejects_before_provider_execution(self):
        """Unsupported or empty requests should fail before any provider work."""
        module = DemoDocumentModule(result={"summary": "unused"})

        result = module.execute("summarize", {})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "InputError")

        unsupported = module.execute("translate", {"content": "hello"})
        self.assertFalse(unsupported["ok"])
        self.assertEqual(unsupported["error_type"], "InputError")

    def test_missing_file_maps_to_file_error(self):
        """File-backed modules should normalize missing source paths."""
        module = DemoFileModule(provider="local_fs", model="native")

        result = module.execute("summarize", {"source_path": "Z:/does/not/exist.txt"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "FileError")

    def test_file_module_accepts_existing_path(self):
        """File-backed modules should still return a normalized success object on valid paths."""
        module = DemoFileModule(provider="local_fs", model="native")
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.txt"
            path.write_text("hello", encoding="utf-8")

            result = module.execute("summarize", {"source_path": str(path)})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["summary"], "Read sample.txt")

    def test_error_taxonomy_stays_governed(self):
        """The published error taxonomy should stay explicit and bounded."""
        self.assertIn("SemanticError", ERROR_TAXONOMY)
        self.assertIn("ProviderUnavailable", ERROR_TAXONOMY)
        self.assertIn("UnknownError", ERROR_TAXONOMY)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

import numpy as np

from src.document_rag import DocumentStore, infer_document_role, sanitize_document_text


class TestDocumentRagHelpers(unittest.TestCase):
    def test_sanitize_document_text_strips_controls_and_normalizes_whitespace(self):
        cleaned = sanitize_document_text("Alpha\x00\t\n  Beta\r\nGamma")

        self.assertEqual(cleaned, "Alpha Beta Gamma")

    def test_infer_document_role_recognizes_fix_language_as_input_artifact(self):
        role = infer_document_role("Please fix this and revise the draft before we ship it.")

        self.assertEqual(role, "input_artifact")

    def test_ingest_text_uses_sanitized_text_for_chunks(self):
        store = DocumentStore()

        with patch.object(store, "_embed", return_value=np.zeros((1, 3))):
            doc_id = store.ingest_text("Alpha\x00\n\nBeta", doc_id="doc-1", metadata={"document_role": "context"})

        self.assertEqual(doc_id, "doc-1")
        self.assertEqual(store.documents["doc-1"]["chunks"], ["Alpha Beta"])
        self.assertEqual(store.documents["doc-1"]["metadata"]["document_role"], "context")


if __name__ == "__main__":
    unittest.main()

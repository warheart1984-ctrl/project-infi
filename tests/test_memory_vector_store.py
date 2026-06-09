"""Tests for governed Memory Board vector store adapter."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from src.jarvis_memory_board import (
    MemoryController,
    MemoryModule,
    build_default_memory_controller,
    default_memory_slots,
    retrieve_board_memory,
    resolve_retrieval_slots,
    slot_retrieval_metadata,
    store_board_memory,
)
from src.memory_vector_store import (
    DEFAULT_MEMORY_SLOT,
    DOCS_MEMORY_SLOT,
    ChromaVectorBackend,
    FirebaseDataConnectVectorBackend,
    MemoryChunkMeta,
    reset_backend_for_tests,
    retrieve_memory,
    should_store_memory,
    store_memory,
    vector_backend_name,
)


def _temp_chroma_backend() -> ChromaVectorBackend:
    temp_dir = tempfile.mkdtemp(prefix="jarvis-chroma-test-")
    return ChromaVectorBackend(temp_dir)


class TestMemoryVectorStore(unittest.TestCase):
    def setUp(self):
        reset_backend_for_tests()
        os.environ["AAIS_VECTOR_BACKEND"] = "chroma"
        self.backend = _temp_chroma_backend()

    def tearDown(self):
        reset_backend_for_tests()
        os.environ.pop("AAIS_VECTOR_BACKEND", None)

    def test_should_store_memory_signals(self):
        self.assertTrue(should_store_memory("Remember that my project goal is stability."))
        self.assertFalse(should_store_memory("ok"))

    def test_slot_filtered_retrieval_returns_only_matching_memory_slot(self):
        self.backend.store_memory(
            "Session-scoped operator preference for dark mode.",
            MemoryChunkMeta(session_id="sess-a", memory_slot="session_v1"),
        )
        self.backend.store_memory(
            "Canonical foundation doctrine for governed execution.",
            MemoryChunkMeta(session_id="sess-a", memory_slot="foundation_v1"),
        )

        session_rows = self.backend.retrieve_memory(
            "operator preference",
            session_id="sess-a",
            memory_slot="session_v1",
            n_results=4,
        )
        foundation_rows = self.backend.retrieve_memory(
            "governed execution",
            session_id="sess-a",
            memory_slot="foundation_v1",
            n_results=4,
        )

        self.assertEqual(len(session_rows), 1)
        self.assertIn("preference", session_rows[0].lower())
        self.assertEqual(len(foundation_rows), 1)
        self.assertIn("foundation", foundation_rows[0].lower())

    def test_trust_class_filter_excludes_mismatched_chunks(self):
        self.backend.store_memory(
            "Verified operational routing default.",
            MemoryChunkMeta(
                session_id="sess-b",
                memory_slot="operational_v1",
                trust_class="verified",
            ),
        )
        self.backend.store_memory(
            "Low-confidence signal that should not surface under verified filter.",
            MemoryChunkMeta(
                session_id="sess-b",
                memory_slot="operational_v1",
                trust_class="low_confidence",
            ),
        )

        verified_rows = self.backend.retrieve_memory(
            "routing default",
            session_id="sess-b",
            memory_slot="operational_v1",
            trust_class="verified",
            n_results=4,
        )
        self.assertEqual(len(verified_rows), 1)
        self.assertIn("verified", verified_rows[0].lower())

    def test_default_backend_is_chroma(self):
        self.assertEqual(vector_backend_name(), "chroma")

    @mock.patch("src.memory_vector_store.get_backend")
    def test_public_store_api_delegates_to_backend(self, mock_get_backend):
        mock_get_backend.return_value = self.backend
        store_memory(
            "Conversation summary: operator prefers concise answers.",
            session_id="sess-c",
            memory_slot=DEFAULT_MEMORY_SLOT,
            trust_class="working",
        )
        rows = retrieve_memory(
            "concise answers",
            session_id="sess-c",
            memory_slot=DEFAULT_MEMORY_SLOT,
            n_results=2,
        )
        self.assertGreaterEqual(len(rows), 1)

    def test_docs_use_docs_memory_slot_partition(self):
        self.backend.add_doc_chunks(
            ["Jarvis memory board doctrine governs slot installs."],
            [{"path": "docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md"}],
        )
        rows = self.backend.query_docs("memory board doctrine", n_results=2)
        self.assertEqual(len(rows), 1)
        self.assertIn("slot installs", rows[0])


class TestFirebaseVectorBackend(unittest.TestCase):
    def setUp(self):
        reset_backend_for_tests()
        self.backend = FirebaseDataConnectVectorBackend()

    def tearDown(self):
        reset_backend_for_tests()

    @mock.patch("src.firebase_dataconnect_client.execute_mutation")
    @mock.patch("src.memory_vector_store._embed_query")
    def test_store_memory_calls_store_mutation(self, mock_embed, mock_mutate):
        mock_embed.return_value = [0.1] * 384
        self.backend.store_memory(
            "Remember that my project goal is stability.",
            MemoryChunkMeta(session_id="sess-f", memory_slot="session_v1"),
        )
        mock_mutate.assert_called_once()
        args = mock_mutate.call_args
        self.assertEqual(args[0][0], "StoreMemoryChunk")
        self.assertEqual(args[0][1]["sessionId"], "sess-f")
        self.assertEqual(args[0][1]["memorySlot"], "session_v1")

    @mock.patch("src.firebase_dataconnect_client.execute_query")
    @mock.patch("src.memory_vector_store._embed_query")
    def test_retrieve_memory_uses_verified_query_when_trust_class_set(
        self, mock_embed, mock_query
    ):
        mock_embed.return_value = [0.2] * 384
        mock_query.return_value = {
            "data": {
                "memoryChunks_embedding_similarity": [
                    {"textBody": "Verified operational routing default."}
                ]
            }
        }
        rows = self.backend.retrieve_memory(
            "routing default",
            session_id="sess-b",
            memory_slot="operational_v1",
            trust_class="verified",
            n_results=2,
        )
        self.assertEqual(rows, ["Verified operational routing default."])
        self.assertEqual(mock_query.call_args[0][0], "RetrieveMemorySimilarityVerified")

    @mock.patch("src.firebase_dataconnect_client.execute_query")
    @mock.patch("src.memory_vector_store._embed_query")
    def test_query_docs_uses_docs_query(self, mock_embed, mock_query):
        mock_embed.return_value = [0.3] * 384
        mock_query.return_value = {
            "data": {
                "memoryChunks_embedding_similarity": [
                    {"textBody": "Jarvis memory board doctrine governs slot installs."}
                ]
            }
        }
        rows = self.backend.query_docs("memory board doctrine", n_results=2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(mock_query.call_args[0][0], "RetrieveMemorySimilarityDocs")

    @mock.patch("src.firebase_dataconnect_client.execute_mutation")
    def test_clear_docs_deletes_docs_slot(self, mock_mutate):
        self.backend.clear_docs()
        mock_mutate.assert_called_once_with(
            "DeleteMemoryChunksBySlot",
            {"tenantId": mock.ANY, "memorySlot": DOCS_MEMORY_SLOT},
        )


class TestMemoryBoardVectorWiring(unittest.TestCase):
    def setUp(self):
        reset_backend_for_tests()
        os.environ["AAIS_VECTOR_BACKEND"] = "chroma"
        self.backend = _temp_chroma_backend()
        self._backend_patcher = mock.patch(
            "src.memory_vector_store.get_backend",
            return_value=self.backend,
        )
        self._backend_patcher.start()

    def tearDown(self):
        self._backend_patcher.stop()
        reset_backend_for_tests()
        os.environ.pop("AAIS_VECTOR_BACKEND", None)

    def test_resolve_retrieval_slots_follows_doctrine_order(self):
        controller = build_default_memory_controller()
        slots = resolve_retrieval_slots(controller, "task")
        self.assertEqual(slots[:3], ["slot_03", "slot_02", "slot_04"])

    def test_slot_retrieval_metadata_maps_trust_class(self):
        controller = build_default_memory_controller()
        meta = slot_retrieval_metadata(controller, "slot_03")
        self.assertEqual(meta["memory_slot"], "session_v1")
        self.assertEqual(meta["trust_class"], "working")

    def test_store_and_retrieve_board_memory_routes_through_primary_slot(self):
        controller = build_default_memory_controller()
        stored_slots = store_board_memory(
            controller,
            "Conversation summary: operator wants task-scoped recall only.",
            session_id="board-sess",
            query_type="task",
        )
        self.assertEqual(stored_slots, ["slot_03"])
        rows = retrieve_board_memory(
            controller,
            "task-scoped recall",
            session_id="board-sess",
            query_type="task",
            n_results=2,
        )
        self.assertGreaterEqual(len(rows), 1)

    def test_board_retrieval_honors_slot_partition(self):
        controller = MemoryController(default_memory_slots())
        archive_module = MemoryModule(
            module_id="archive_v1",
            module_version="1.0.0",
            module_class="archive",
            supported_slot="slot_04",
            capacity=1024,
            trust_class="preserved",
            retrieval_priority=30,
            retention_policy="long_term",
            eviction_policy="none",
        )
        foundation_module = MemoryModule(
            module_id="foundation_v1",
            module_version="1.0.0",
            module_class="foundation",
            supported_slot="slot_01",
            capacity=128,
            trust_class="canonical",
            retrieval_priority=100,
            retention_policy="explicit_only",
            eviction_policy="none",
        )
        controller.register_module("slot_04", archive_module)
        controller.register_module("slot_01", foundation_module)

        store_board_memory(
            controller,
            "Conversation summary: archive slot holds preserved operator history.",
            session_id="iso-sess",
            query_type="history",
        )
        self.backend.store_memory(
            "Canonical foundation truth unrelated to archive history.",
            MemoryChunkMeta(
                session_id="iso-sess",
                memory_slot="foundation_v1",
                trust_class="canonical",
            ),
        )

        history_rows = retrieve_board_memory(
            controller,
            "preserved operator history",
            session_id="iso-sess",
            query_type="history",
            n_results=2,
        )
        self.assertTrue(any("archive slot" in row.lower() for row in history_rows))
        self.assertFalse(any("foundation truth" in row.lower() for row in history_rows))


if __name__ == "__main__":
    unittest.main()

-- Jarvis Memory Board vector projection (ScyllaDB Cloud Vector Search)
-- Query-first design: partition by (tenant_id, memory_slot), cluster by time.

CREATE KEYSPACE IF NOT EXISTS jarvis_memory
  WITH replication = {'class': 'NetworkTopologyStrategy', 'AWS_US_EAST_1': 3};

USE jarvis_memory;

CREATE TABLE IF NOT EXISTS memory_chunks (
    tenant_id       text,
    memory_slot     text,
    chunk_id        timeuuid,
    session_id      text,
    trust_class     text,
    source          text,
    text_body       text,
    embedding       vector<float, 384>,
    recorded_at     timestamp,
    cisiv_stage     text,
    PRIMARY KEY ((tenant_id, memory_slot), recorded_at, chunk_id)
) WITH CLUSTERING ORDER BY (recorded_at DESC);

CREATE CUSTOM INDEX IF NOT EXISTS memory_embedding_idx ON memory_chunks (embedding)
USING 'vector_index'
WITH OPTIONS = {
  'similarity_function': 'COSINE',
  'source_id': 'chunk_id'
};

CREATE INDEX IF NOT EXISTS memory_session_idx ON memory_chunks (session_id);

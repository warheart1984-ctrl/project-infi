-- Emergent Substrate Database Schema
-- 9 tables + 2 views
-- PostgreSQL 15+ / SQLite 3.35+

-- Entropy Packets Table
CREATE TABLE IF NOT EXISTS entropy_packets (
    packet_id TEXT PRIMARY KEY,
    packet_type TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    emotional_tone TEXT NOT NULL,
    cross_domain TEXT,
    intensity REAL NOT NULL,
    tags TEXT,
    timestamp TEXT NOT NULL,
    metadata TEXT
);

-- Structured Models Table
CREATE TABLE IF NOT EXISTS structured_models (
    model_id TEXT PRIMARY KEY,
    source_packet_id TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    invariants TEXT,
    cross_domain_decomposition TEXT,
    constraints TEXT,
    structure_type TEXT,
    confidence_score REAL,
    timestamp TEXT NOT NULL,
    raw_model TEXT,
    FOREIGN KEY (source_packet_id) REFERENCES entropy_packets(packet_id)
);

-- Governed Specs Table
CREATE TABLE IF NOT EXISTS governed_specs (
    spec_id TEXT PRIMARY KEY,
    source_model_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    validation_results TEXT,
    governance_status TEXT NOT NULL,
    integrated BOOLEAN DEFAULT FALSE,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (source_model_id) REFERENCES structured_models(model_id)
);

-- Identity Memory Table
CREATE TABLE IF NOT EXISTS identity_memory (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    last_updated TEXT NOT NULL
);

-- Continuity Memory Table
CREATE TABLE IF NOT EXISTS continuity_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT NOT NULL,
    active_projects TEXT,
    attached_constitutions TEXT,
    last_updated TEXT NOT NULL
);

-- Evolution Events Table
CREATE TABLE IF NOT EXISTS evolution_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    related_ids TEXT,
    timestamp TEXT NOT NULL,
    metadata TEXT
);

-- Constitution Hooks Table
CREATE TABLE IF NOT EXISTS constitution_hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    constitution_name TEXT NOT NULL,
    constitution_version TEXT NOT NULL,
    priority INTEGER NOT NULL,
    attached_at TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE
);

-- Validation Results Table
CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    constitution_name TEXT NOT NULL,
    constitution_version TEXT NOT NULL,
    priority INTEGER NOT NULL,
    status TEXT NOT NULL,
    violations TEXT,
    warnings TEXT,
    timestamp TEXT NOT NULL,
    source_model_id TEXT,
    FOREIGN KEY (source_model_id) REFERENCES structured_models(model_id)
);

-- Substrate States Table
CREATE TABLE IF NOT EXISTS substrate_states (
    state_id TEXT PRIMARY KEY,
    iteration INTEGER DEFAULT 0,
    is_alive BOOLEAN DEFAULT FALSE,
    total_packets_emitted INTEGER DEFAULT 0,
    total_specs_produced INTEGER DEFAULT 0,
    total_constitutions_attached INTEGER DEFAULT 0,
    total_loop_iterations INTEGER DEFAULT 0,
    identity_memory_non_empty BOOLEAN DEFAULT FALSE,
    last_activity TEXT,
    timestamp TEXT NOT NULL
);

-- View: Full Loop Trace
CREATE VIEW IF NOT EXISTS v_full_loop_trace AS
SELECT 
    ep.packet_id,
    ep.packet_type,
    ep.raw_content,
    sm.model_id,
    sm.title,
    gs.spec_id,
    gs.governance_status,
    vr.status as validation_status,
    vr.constitution_name
FROM entropy_packets ep
LEFT JOIN structured_models sm ON ep.packet_id = sm.source_packet_id
LEFT JOIN governed_specs gs ON sm.model_id = gs.source_model_id
LEFT JOIN validation_results vr ON sm.model_id = vr.source_model_id;

-- View: Evolution Timeline
CREATE VIEW IF NOT EXISTS v_evolution_timeline AS
SELECT 
    ee.event_id,
    ee.event_type,
    ee.description,
    ee.timestamp,
    gs.title as related_spec_title
FROM evolution_events ee
LEFT JOIN governed_specs gs ON json_extract(ee.related_ids, '$[0]') = gs.spec_id
ORDER BY ee.timestamp DESC;

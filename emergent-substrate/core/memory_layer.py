"""
Memory Layer - SQLite-backed
Identity + Continuity + Evolution Log (append-only)
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from .models import (
    IdentityMemory,
    ContinuityMemory,
    EvolutionEvent,
    ConstitutionHook,
    SubstrateState,
    EntropyPacket,
    StructuredModel,
    GovernedSpec,
    ValidationResult
)


class MemoryLayer:
    """
    SQLite-backed memory layer
    Manages identity, continuity, and append-only evolution log
    """

    def __init__(self, db_path: str = "substrate.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
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
            )
        """)
        
        cursor.execute("""
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
            )
        """)
        
        cursor.execute("""
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
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS identity_memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS continuity_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                active_projects TEXT,
                attached_constitutions TEXT,
                last_updated TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                related_ids TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS constitution_hooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                constitution_name TEXT NOT NULL,
                constitution_version TEXT NOT NULL,
                priority INTEGER NOT NULL,
                attached_at TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
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
            )
        """)
        
        cursor.execute("""
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
            )
        """)
        
        # Create views
        cursor.execute("""
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
            LEFT JOIN validation_results vr ON sm.model_id = vr.source_model_id
        """)
        
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_evolution_timeline AS
            SELECT 
                ee.event_id,
                ee.event_type,
                ee.description,
                ee.timestamp,
                gs.title as related_spec_title
            FROM evolution_events ee
            LEFT JOIN governed_specs gs ON json_extract(ee.related_ids, '$[0]') = gs.spec_id
            ORDER BY ee.timestamp DESC
        """)
        
        conn.commit()
        conn.close()

    # Entropy Packets
    def save_packet(self, packet: EntropyPacket) -> None:
        """Save entropy packet to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entropy_packets 
            (packet_id, packet_type, raw_content, emotional_tone, cross_domain, 
             intensity, tags, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            packet.packet_id,
            packet.packet_type.value,
            packet.raw_content,
            packet.emotional_tone.value,
            json.dumps(packet.cross_domain),
            packet.intensity,
            json.dumps(packet.tags),
            packet.timestamp.isoformat(),
            json.dumps(packet.metadata)
        ))
        conn.commit()
        conn.close()

    def get_packet(self, packet_id: str) -> Optional[EntropyPacket]:
        """Retrieve entropy packet by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entropy_packets WHERE packet_id = ?", (packet_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return EntropyPacket(
                packet_id=row[0],
                packet_type=row[1],
                raw_content=row[2],
                emotional_tone=row[3],
                cross_domain=json.loads(row[4]) if row[4] else [],
                intensity=row[5],
                tags=json.loads(row[6]) if row[6] else [],
                timestamp=datetime.fromisoformat(row[7]),
                metadata=json.loads(row[8]) if row[8] else {}
            )
        return None

    # Structured Models
    def save_model(self, model: StructuredModel) -> None:
        """Save structured model to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO structured_models 
            (model_id, source_packet_id, title, abstract, invariants, 
             cross_domain_decomposition, constraints, structure_type, 
             confidence_score, timestamp, raw_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model.model_id,
            model.source_packet_id,
            model.title,
            model.abstract,
            json.dumps(model.invariants),
            json.dumps(model.cross_domain_decomposition),
            json.dumps(model.constraints),
            model.structure_type,
            model.confidence_score,
            model.timestamp.isoformat(),
            json.dumps(model.raw_model) if model.raw_model else None
        ))
        conn.commit()
        conn.close()

    # Governed Specs
    def save_spec(self, spec: GovernedSpec) -> None:
        """Save governed spec to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO governed_specs 
            (spec_id, source_model_id, title, content, validation_results, 
             governance_status, integrated, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            spec.spec_id,
            spec.source_model_id,
            spec.title,
            spec.content,
            json.dumps([r.model_dump() for r in spec.validation_results]),
            spec.governance_status.value,
            spec.integrated,
            spec.timestamp.isoformat()
        ))
        conn.commit()
        conn.close()

    # Identity Memory
    def set_identity(self, key: str, value: str) -> None:
        """Set identity memory key-value pair"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO identity_memory (key, value, last_updated)
            VALUES (?, ?, ?)
        """, (key, value, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    def get_identity(self, key: str) -> Optional[str]:
        """Get identity memory value by key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM identity_memory WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_identity(self) -> Dict[str, str]:
        """Get all identity memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM identity_memory")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    # Continuity Memory
    def set_continuity(self, goal: str, active_projects: List[str], attached_constitutions: List[str]) -> None:
        """Set continuity memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO continuity_memory (goal, active_projects, attached_constitutions, last_updated)
            VALUES (?, ?, ?, ?)
        """, (goal, json.dumps(active_projects), json.dumps(attached_constitutions), datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    def get_continuity(self) -> Optional[ContinuityMemory]:
        """Get continuity memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM continuity_memory ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ContinuityMemory(
                goal=row[1],
                active_projects=json.loads(row[2]) if row[2] else [],
                attached_constitutions=json.loads(row[3]) if row[3] else [],
                last_updated=datetime.fromisoformat(row[4])
            )
        return None

    # Evolution Events
    def append_evolution_event(self, event_type: str, description: str, related_ids: List[str] = None, metadata: Dict[str, Any] = None) -> None:
        """Append evolution event (append-only)"""
        import uuid
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evolution_events (event_id, event_type, description, related_ids, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            event_type,
            description,
            json.dumps(related_ids or []),
            datetime.utcnow().isoformat(),
            json.dumps(metadata or {})
        ))
        conn.commit()
        conn.close()

    def get_evolution_timeline(self, limit: int = 100) -> List[EvolutionEvent]:
        """Get evolution timeline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evolution_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            EvolutionEvent(
                event_id=row[0],
                event_type=row[1],
                description=row[2],
                related_ids=json.loads(row[3]) if row[3] else [],
                timestamp=datetime.fromisoformat(row[4]),
                metadata=json.loads(row[5]) if row[5] else {}
            )
            for row in rows
        ]

    # Constitution Hooks
    def attach_constitution(self, name: str, version: str, priority: int) -> None:
        """Attach constitution to governance layer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO constitution_hooks (constitution_name, constitution_version, priority, attached_at, active)
            VALUES (?, ?, ?, ?, TRUE)
        """, (name, version, priority, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    def get_constitutions(self) -> List[ConstitutionHook]:
        """Get all attached constitutions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM constitution_hooks WHERE active = TRUE ORDER BY priority")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            ConstitutionHook(
                constitution_name=row[1],
                constitution_version=row[2],
                priority=row[3],
                attached_at=datetime.fromisoformat(row[4]),
                active=row[5]
            )
            for row in rows
        ]

    # Substrate State
    def save_state(self, state: SubstrateState) -> None:
        """Save substrate state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO substrate_states 
            (state_id, iteration, is_alive, total_packets_emitted, total_specs_produced, 
             total_constitutions_attached, total_loop_iterations, identity_memory_non_empty, 
             last_activity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state.state_id,
            state.iteration,
            state.is_alive,
            state.total_packets_emitted,
            state.total_specs_produced,
            state.total_constitutions_attached,
            state.total_loop_iterations,
            state.identity_memory_non_empty,
            state.last_activity.isoformat() if state.last_activity else None,
            state.timestamp.isoformat()
        ))
        conn.commit()
        conn.close()

    def get_state(self) -> Optional[SubstrateState]:
        """Get current substrate state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM substrate_states ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SubstrateState(
                state_id=row[0],
                iteration=row[1],
                is_alive=row[2],
                total_packets_emitted=row[3],
                total_specs_produced=row[4],
                total_constitutions_attached=row[5],
                total_loop_iterations=row[6],
                identity_memory_non_empty=row[7],
                last_activity=datetime.fromisoformat(row[8]) if row[8] else None,
                timestamp=datetime.fromisoformat(row[9])
            )
        return None

    # Validation Results
    def save_validation_result(self, result: ValidationResult, source_model_id: str = None) -> None:
        """Save validation result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO validation_results 
            (constitution_name, constitution_version, priority, status, violations, warnings, timestamp, source_model_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.constitution_name,
            result.constitution_version,
            result.priority,
            result.status.value,
            json.dumps(result.violations),
            json.dumps(result.warnings),
            result.timestamp.isoformat(),
            source_model_id
        ))
        conn.commit()
        conn.close()

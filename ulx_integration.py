#!/usr/bin/env python3
"""
ULX Integration Layer for AI Organism
Integrates ULX constitutional programming language with the 7-layer architecture
"""

import sys
import os
import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from enum import Enum

# Import ULX implementation from E:\ulx.py
sys.path.insert(0, 'E:\\')
from ulx import (
    lex, parse, Interpreter, InvariantEngine, SignalBus, AnchorStore,
    Lawful, Governed, Signal, Trust, Record, GovernanceViolation,
    AUTH_ORDER, build_stdlib
)


class Layer(Enum):
    """7-Layer Architecture Model"""
    L0_CONSTITUTIONAL_SUBSTRATE = 0
    L1_INFRASTRUCTURE_BEDROCK = 1
    L2_PLATFORM_SERVICES = 2
    L3_APPLICATION_CORE = 3
    L4_INTEGRATION_FABRIC = 4
    L5_INTELLIGENCE_AUTOMATION = 5
    L6_GOVERNANCE_OBSERVABILITY = 6


class AuthorityTier(Enum):
    """UCDD S-004 Layered Authority Model"""
    PRIME = "prime"
    SOVEREIGN = "sovereign"
    DELEGATE = "delegate"
    OBSERVER = "observer"


@dataclass
class Component:
    """Component catalog entry per prime architect blueprint"""
    component_id: str
    name: str
    layer: Layer
    responsibility: str
    dependencies: List[str]
    ucdd_ref: List[str]
    const_ref: List[str]
    status: str = "pending"


class ConstitutionalRuleEngine:
    """COMP-0001: Constitutional Rule Engine (Layer 0)"""
    
    def __init__(self):
        self.interpreter = Interpreter()
        self.invariants = InvariantEngine(self.interpreter)
        self.clauses = {}
        
    def load_constitution(self, constitution_source: str):
        """Load and parse ULX constitution"""
        program = parse(constitution_source)
        self.invariants.load_constitution(program.constitution)
        self.interpreter.load_program(program)
        
    def evaluate_rule(self, rule_name: str, context: Dict[str, Any]) -> bool:
        """Evaluate a constitutional rule against context"""
        try:
            return self.interpreter.run_function(rule_name, [context])
        except GovernanceViolation:
            return False
        except Exception:
            return None  # Not applicable
    
    def query_constitution(self, query: str) -> Dict[str, Any]:
        """Read-only query to constitutional clauses"""
        return {
            "query": query,
            "timestamp": time.time(),
            "result": self.invariants.articles
        }


class ImmutableArtifactRegistry:
    """COMP-0002: Immutable Artifact Registry (Layer 0)"""
    
    def __init__(self):
        self.artifacts = {}  # hash -> artifact metadata
        self.hashes = {}     # artifact_id -> hash
        
    def register_artifact(self, artifact_id: str, content: bytes, metadata: Dict):
        """Register an artifact with cryptographic hash"""
        hash_val = hashlib.sha256(content).hexdigest()
        self.artifacts[hash_val] = {
            "artifact_id": artifact_id,
            "hash": hash_val,
            "content": content.hex(),
            "metadata": metadata,
            "timestamp": time.time()
        }
        self.hashes[artifact_id] = hash_val
        return hash_val
    
    def verify_artifact(self, artifact_id: str, content: bytes) -> bool:
        """Verify artifact integrity"""
        expected_hash = self.hashes.get(artifact_id)
        if not expected_hash:
            return False
        actual_hash = hashlib.sha256(content).hexdigest()
        return actual_hash == expected_hash
    
    def get_artifact(self, hash_val: str) -> Optional[Dict]:
        """Retrieve artifact by hash"""
        return self.artifacts.get(hash_val)


class TraceabilityRegistry:
    """COMP-0003: Traceability Registry (Layer 0)"""
    
    def __init__(self):
        self.links = {}  # trace_id -> linkage data
        self.bidirectional = {}  # (source, target) -> trace_id
        
    def register_link(self, trace_id: str, source: str, target: str, 
                     link_type: str, metadata: Dict = None):
        """Register bidirectional traceability link"""
        link_data = {
            "trace_id": trace_id,
            "source": source,
            "target": target,
            "link_type": link_type,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        self.links[trace_id] = link_data
        self.bidirectional[(source, target)] = trace_id
        self.bidirectional[(target, source)] = trace_id
        
    def resolve_forward(self, source: str) -> List[Dict]:
        """Resolve all forward links from source"""
        return [link for link in self.links.values() if link["source"] == source]
    
    def resolve_backward(self, target: str) -> List[Dict]:
        """Resolve all backward links to target"""
        return [link for link in self.links.values() if link["target"] == target]


class ImmutableAuditLedger:
    """COMP-0019: Immutable Audit Ledger (Layer 6)"""
    
    def __init__(self):
        self.entries = []
        self.chain_hashes = []
        
    def append_entry(self, entry_type: str, data: Dict):
        """Append entry to append-only ledger"""
        entry = {
            "type": entry_type,
            "data": data,
            "timestamp": time.time(),
            "index": len(self.entries)
        }
        
        # Chain hash verification
        prev_hash = self.chain_hashes[-1] if self.chain_hashes else "genesis"
        entry_blob = json.dumps(entry, sort_keys=True) + prev_hash
        chain_hash = hashlib.sha256(entry_blob.encode()).hexdigest()
        
        entry["chain_hash"] = chain_hash
        entry["prev_hash"] = prev_hash
        
        self.entries.append(entry)
        self.chain_hashes.append(chain_hash)
        
    def verify_chain(self) -> bool:
        """Verify hash chain integrity"""
        for i, entry in enumerate(self.entries):
            if i == 0:
                if entry["prev_hash"] != "genesis":
                    return False
            else:
                prev_hash = self.chain_hashes[i-1]
                entry_blob = json.dumps(entry, sort_keys=True) + prev_hash
                expected_hash = hashlib.sha256(entry_blob.encode()).hexdigest()
                if entry["chain_hash"] != expected_hash:
                    return False
        return True


class ComplianceDashboard:
    """COMP-0020: Compliance Dashboard (Layer 6)"""
    
    def __init__(self, audit_ledger: ImmutableAuditLedger):
        self.audit_ledger = audit_ledger
        self.conformance_status = {}
        
    def update_conformance(self, component_id: str, standard: str, status: str):
        """Update conformance status for component"""
        if component_id not in self.conformance_status:
            self.conformance_status[component_id] = {}
        self.conformance_status[component_id][standard] = {
            "status": status,
            "timestamp": time.time()
        }
        
    def get_conformance_summary(self) -> Dict:
        """Get overall conformance summary"""
        summary = {
            "total_components": len(self.conformance_status),
            "by_standard": {},
            "open_findings": []
        }
        
        for component, standards in self.conformance_status.items():
            for standard, data in standards.items():
                if standard not in summary["by_standard"]:
                    summary["by_standard"][standard] = {"compliant": 0, "non_compliant": 0}
                if data["status"] == "compliant":
                    summary["by_standard"][standard]["compliant"] += 1
                else:
                    summary["by_standard"][standard]["non_compliant"] += 1
                    summary["open_findings"].append({
                        "component": component,
                        "standard": standard,
                        "status": data["status"]
                    })
        
        return summary


class ConstitutionalPromptGovernor:
    """UCDD S-007: Constitutional Prompt Governor (Layer 5)"""
    
    def __init__(self, rule_engine: ConstitutionalRuleEngine):
        self.rule_engine = rule_engine
        self.rejection_log = []
        
    def validate_prompt_header(self, header: Dict) -> tuple[bool, str]:
        """Validate constitutional prompt header"""
        required_fields = [
            "SOVEREIGN-CONTEXT", "UCDD", "LAYER", 
            "COMPONENT", "TRACE-ID", "AUTHORITY"
        ]
        
        for field in required_fields:
            if field not in header:
                error = f"Missing required field: {field}"
                self.rejection_log.append({
                    "error": error,
                    "timestamp": time.time(),
                    "header": header
                })
                return False, error
        
        # Validate UCDD format
        if header.get("UCDD") != "S-007 COMPLIANT":
            error = "UCDD field must be 'S-007 COMPLIANT'"
            self.rejection_log.append({
                "error": error,
                "timestamp": time.time(),
                "header": header
            })
            return False, error
        
        return True, "Valid"
    
    def reject_session(self, reason: str, session_data: Dict):
        """Reject non-compliant session"""
        self.rejection_log.append({
            "reason": reason,
            "session_data": session_data,
            "timestamp": time.time()
        })


class ConformanceEvidenceBundle:
    """UCDD S-001: Conformance Evidence Bundle"""
    
    def __init__(self):
        self.bundle = {
            "manifest": {},
            "traceability": [],
            "sbom": [],
            "build_evidence": [],
            "security_evidence": [],
            "runtime_conformance": [],
            "audit_findings": [],
            "amendment_history": []
        }
        
    def add_evidence(self, evidence_type: str, evidence: Dict):
        """Add evidence to bundle"""
        if evidence_type in self.bundle:
            self.bundle[evidence_type].append(evidence)
            
    def sign_bundle(self, signing_key: str) -> str:
        """Sign the bundle with constitutional key"""
        bundle_str = json.dumps(self.bundle, sort_keys=True)
        signature = hashlib.sha256((bundle_str + signing_key).encode()).hexdigest()
        self.bundle["signature"] = signature
        return signature


class SevenLayerArchitecture:
    """Main 7-Layer Architecture Implementation"""
    
    def __init__(self):
        # Layer 0: Constitutional Substrate
        self.constitutional_rule_engine = ConstitutionalRuleEngine()
        self.immutable_artifact_registry = ImmutableArtifactRegistry()
        self.traceability_registry = TraceabilityRegistry()
        
        # Layer 6: Governance & Observability
        self.audit_ledger = ImmutableAuditLedger()
        self.compliance_dashboard = ComplianceDashboard(self.audit_ledger)
        
        # Layer 5: Intelligence & Automation
        self.prompt_governor = ConstitutionalPromptGovernor(self.constitutional_rule_engine)
        
        # Component catalog
        self.components = {}
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize component catalog from prime architect blueprint"""
        components = [
            Component("COMP-0001", "Constitutional Rule Engine", Layer.L0_CONSTITUTIONAL_SUBSTRATE,
                     "Read-only evaluation of constitutional clauses", ["Immutable Artifact Registry"],
                     ["S-003", "S-006"], ["CONST-C01", "C02"], "active"),
            Component("COMP-0002", "Immutable Artifact Registry", Layer.L0_CONSTITUTIONAL_SUBSTRATE,
                     "Cryptographically signed artifact store", ["HSM"],
                     ["S-003"], ["CONST-C02"], "active"),
            Component("COMP-0019", "Immutable Audit Ledger", Layer.L6_GOVERNANCE_OBSERVABILITY,
                     "Append-only audit ledger", ["HSM"],
                     ["S-001", "S-005"], ["CONST-C02", "C05"], "active"),
            Component("COMP-0020", "Compliance Dashboard", Layer.L6_GOVERNANCE_OBSERVABILITY,
                     "Real-time governance dashboard", ["Immutable Audit Ledger", "Constitutional Rule Engine"],
                     ["S-005"], ["CONST-C05"], "active"),
        ]
        
        for comp in components:
            self.components[comp.component_id] = comp
            
    def load_constitution(self, constitution_source: str):
        """Load ULX constitution into Layer 0"""
        self.constitutional_rule_engine.load_constitution(constitution_source)
        self.audit_ledger.append_entry("CONSTITUTION_LOADED", {
            "timestamp": time.time(),
            "status": "loaded"
        })
        
    def register_artifact(self, artifact_id: str, content: bytes, metadata: Dict):
        """Register artifact in Layer 0"""
        hash_val = self.immutable_artifact_registry.register_artifact(artifact_id, content, metadata)
        self.audit_ledger.append_entry("ARTIFACT_REGISTERED", {
            "artifact_id": artifact_id,
            "hash": hash_val,
            "metadata": metadata
        })
        return hash_val
        
    def create_traceability_link(self, trace_id: str, source: str, target: str, 
                                link_type: str, metadata: Dict = None):
        """Create traceability link in Layer 0"""
        self.traceability_registry.register_link(trace_id, source, target, link_type, metadata)
        self.audit_ledger.append_entry("TRACEABILITY_LINK_CREATED", {
            "trace_id": trace_id,
            "source": source,
            "target": target,
            "link_type": link_type
        })
        
    def validate_ai_session(self, prompt_header: Dict) -> tuple[bool, str]:
        """Validate AI agent session via UCDD S-007"""
        return self.prompt_governor.validate_prompt_header(prompt_header)
        
    def get_compliance_status(self) -> Dict:
        """Get overall compliance status from Layer 6"""
        return self.compliance_dashboard.get_conformance_summary()
        
    def verify_audit_chain(self) -> bool:
        """Verify audit ledger chain integrity"""
        return self.audit_ledger.verify_chain()


# Initialize global architecture instance
architecture = SevenLayerArchitecture()


def get_architecture() -> SevenLayerArchitecture:
    """Get global architecture instance"""
    return architecture

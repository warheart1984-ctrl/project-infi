use serde::{Deserialize, Serialize};

use crate::types::EventId;

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ConceptPayload {
    pub name: String,
    pub definition: String,
    pub evidence_refs: Vec<EventId>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct InvariantPayload {
    pub name: String,
    pub description: String,
    pub scope: String,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ArchitecturePayload {
    pub name: String,
    pub version: String,
    pub definition: String,
    pub invariants: Vec<String>,
    pub components: Vec<String>,
    pub evidence_refs: Vec<EventId>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct GovernancePayload {
    pub name: String,
    pub authority_scope: String,
    pub invariants: Vec<String>,
    pub constraints: Vec<String>,
    pub evidence_refs: Vec<EventId>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct DecisionPayload {
    pub title: String,
    pub rationale: String,
    pub chosen_architecture: Option<EventId>,
    pub alternatives: Vec<EventId>,
    pub evidence_refs: Vec<EventId>,
    pub governance_refs: Vec<EventId>,
    pub outcome_summary: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EvidencePayload {
    pub source: String,
    pub summary: String,
    pub details: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct NotePayload {
    pub text: String,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "data")]
pub enum EventPayload {
    Concept(ConceptPayload),
    Invariant(InvariantPayload),
    Architecture(ArchitecturePayload),
    Governance(GovernancePayload),
    Decision(DecisionPayload),
    Evidence(EvidencePayload),
    Note(NotePayload),
    Custom {
        type_name: String,
        json: serde_json::Value,
    },
}

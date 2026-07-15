# CIEMS Kernel Architecture

```mermaid
flowchart TB
  subgraph Twins["AI Twin Civilization"]
    ST["Strategic Twin"]
    ET["Execution Twin"]
    NT["Negotiation Twin"]
    SMT["Simulation Twin"]
    FT["Federation Twin"]
  end

  subgraph Kernel["CIEMS Constitutional Membrane"]
    IK["IntentKernel"]
    GK["Governance evaluation"]
    PK["PlanKernel"]
    XK["ExecutionKernel"]
    EVK["EvidenceKernel"]
    UK["USSKernel"]
    FG["Federation policy"]
    SG["Simulation policy"]
  end

  subgraph Runtime["Governed Runtime"]
    ISL["ISL compiler"]
    ORCH["Orchestration"]
    ADAPT["Adapter runtime"]
    SUB["Contract-bound substrates"]
  end

  subgraph USS["Physical USS + Logical Projections"]
    IG["IdentityGraph"]
    MG["MissionGraph"]
    EG["EvidenceGraph"]
    LG["LineageGraph"]
    MVG["MultiverseGraph"]
    SIM["Isolated SimulationGraph"]
    GOV["Governance projection"]
    FED["Federation projection"]
  end

  ST --> IK
  ET --> IK
  NT --> IK
  SMT --> IK
  FT --> IK
  IK --> GK
  GK -->|"intent admitted"| ISL
  ISL --> PK
  PK --> GK
  GK -->|"plan approved"| XK
  XK --> ORCH
  ORCH --> ADAPT --> SUB
  SUB --> EVK
  EVK --> GK
  GK -->|"evidence admitted"| UK
  UK --> IG
  UK --> MG
  UK --> EG
  UK --> LG
  UK --> MVG
  SG --> SIM
  FG --> FED
  GK --> GOV
  NT --> GK
  SMT --> SG
  FT --> FG
```

The governing path is `Intent → Governance → ISL Plan → Governance → Authorized Execution → Evidence → Governance → USS Update`. Governance is a membrane around each boundary, not a downstream cleanup stage.

Twins never address physical or projected graphs directly. Queries pass through authorized USS services; mutations require admissible evidence and USSKernel continuity approval. Federation imports require provenance, governance alignment, and unanimous admission. Simulations write only to the isolated SimulationGraph.

`Governance projection` and `Federation projection` are composed from CIEMS configuration, Identity, Evidence, and Lineage records. They do not add physical graph engines to the frozen runtime.

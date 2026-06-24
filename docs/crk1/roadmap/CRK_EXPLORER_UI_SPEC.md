# CRK-Explorer UI Specification

**Web continuity browser** — Phase 2 deliverable.

---

## Top-level layout

### Header bar

| Region | Content |
|--------|---------|
| Left | **CRK-Explorer** + epoch badge: `CRK-1 v1.0 · Epoch N` |
| Center | Focus chain breadcrumb: Identity → Decision → Outcome → Evidence → Interpretation |
| Right | Filters (time window, object type), connection status **LIVE** / **PAUSED** |

### Main body — 3-pane layout

#### Left pane — object list / search

- Search by ID, type, label
- Tabs: Identities | Decisions | Outcomes | Evidence | Interpretations | Receipts
- List item: primary label, secondary `id`, `created_at`, `type`
- Click → centers graph on node

#### Center pane — continuity graph

- Layered layout (recommended) or force-directed:
  - Row 1: Identity
  - Row 2: Decision
  - Row 3: Outcome
  - Row 4: Evidence
  - Row 5: Interpretation
- Node color by type; directed edges for continuity flow
- Live updates: new nodes fade-in, edges animate briefly
- Click node → populates right pane

#### Right pane — inspector

| Tab | Content |
|-----|---------|
| **Details** | `id`, `type`, `created_at`, `created_by`, `receipt_id`, epoch |
| **Provenance** | Direct parents/children with IDs and types |
| **Receipts** | Linked governance receipt(s), invariant checks, red-team status |
| **Chain** | Linear view: Identity → … → Interpretation (clickable IDs) |

### Footer

Event log ticker, e.g.:

> + Interpretation `I-1234` added to Evidence `E-5678` (Receipt `R-9999`)

---

## Data sources

| UI region | API |
|-----------|-----|
| Object list | `GET /graph/full`, type filters |
| Graph | `GET /graph/node/{id}`, `GET /graph/chain/{id}` |
| Inspector | `GET /{type}/{id}`, `GET /receipt/{receipt_id}` |
| Live updates | `WS /events/stream` |

See [CRK1_GRAPH_DATA_CONTRACT.md](CRK1_GRAPH_DATA_CONTRACT.md).

---

## Node styling

| Type | Color (suggested) | Shape |
|------|-------------------|-------|
| Identity | Blue | Circle |
| Decision | Amber | Diamond |
| Outcome | Green | Rounded rect |
| Evidence | Purple | Document |
| Interpretation | Teal | Hexagon |

Receipts appear in inspector only (optional `ReceiptNode` in graph later).

---

## Implementation status

| Piece | Status | Path |
|-------|--------|------|
| CRK-Explorer app | Not started | — |
| Static CRK dashboard | Partial | `docs/crk1/crk1_continuity_dashboard.html` |
| Constitutional cockpit | Partial (law spine) | `frontend/src/pages/ConstitutionalCockpit.jsx` |
| Evidence graph component | Reusable pattern | `frontend/src/components/constitutional/EvidenceGraph.jsx` |

**Recommended stack:** React + same API client as VR (thin truth client).

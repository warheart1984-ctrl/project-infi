# CRK-1 Interpretive Lineage Tree
Version 1.0

The Interpretive Lineage Tree records the ancestry of interpretive frames.
It is used to:

- replay interpretive evolution
- detect doctrinal lock-in
- audit semantic drift

---

## 1. Node Definition

Each node is an InterpretationObject:

- `id`: UUID
- `name`: string
- `version`: string
- `assumptions`: [string]
- `prediction_binding`: true
- `weight`: float
- `adversarial`: boolean
- `lineage`: [UUID]  # parent frames
- `created_at`: datetime

---

## 2. Tree Structure

- Root frames: `lineage = []`
- Child frames: `lineage = [parent_id, ...]`

Example:

- Frame F0 (root)
- Frame F1 (child of F0)
- Frame F2 (child of F0 and F1)

Lineage:

- F0: `[]`
- F1: `[F0]`
- F2: `[F0, F1]`

---

## 3. Lineage Queries

Implemented in `src/crk1/interpretive_lineage_tree.py`:

- `get_ancestors(frame_id)` → all upstream frames
- `get_descendants(frame_id)` → all downstream frames
- `get_siblings(frame_id)` → frames sharing at least one parent

---

## 4. Constitutional Uses

- **K7**: ensure pluralism across lineages
- **K9**: detect interpretive monoculture
- **K10**: ensure adversarial branches exist
- **K11**: replay interpretive drift over time

The lineage tree is stored in the Semantic Ledger as a replayable structure on each `InterpretationObject`.

---

## 5. Bootstrap Lineage

Default CRK-1 runtime seeds:

- `dominant-frame` — root (`lineage = []`)
- `adversarial-frame` — child of dominant (`lineage = [dominant.id]`)

This guarantees at least one adversarial branch for K10 reconstruction replay.

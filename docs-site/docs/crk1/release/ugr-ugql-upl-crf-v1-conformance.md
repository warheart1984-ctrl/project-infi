---
title: UGR, UGQL, UPL, and CRF v1 Conformance
---

# UGR, UGQL, UPL, and CRF v1 Conformance

This page mirrors the machine-readable conformance artifact for the unified knowledge and replay substrate.

## Conformance intent

Systems claiming conformance to this bundle MUST provide:

- UGR storage for worlds, documents, metrics, concepts, rules, agents, arenas, lineages, and mesh links.
- UGQL support for `SELECT`, `SEARCH`, `TRACE`, `AGGREGATE`, and `COMPARE`.
- UPL support for domain modules, governance modules, and world packs.
- CRF support for replayable timeline, governance state, impact, lineage, and validation data.
- Constitutional Change Ledger support for query, history, replay, diff, impact, and lineage views.

## Machine-readable mirror

```json
{
  "$id": "docs/crk1/release/UGR_UGQL_UPL_CRF_V1.conformance.json",
  "artifact": "UGR/UGQL/UPL/CRF v1 conformance",
  "purpose": "Machine-readable conformance artifact for the unified knowledge and replay substrate."
}
```

## Evidence surface

- `GET /ugr/world/:id`
- `GET /ugr/object/:id`
- `GET /ugr/lineage/:id`
- `GET /ugr/mesh/neighbors`
- `POST /ugr/query`
- `GET /ugr/query?ugql=...`
- `GET /upl/modules`
- `GET /crf/artifacts`
- `GET /crf/artifacts/:artifactId`
- `GET /governance/change-ledger`
- `GET /governance/history/:intentId`
- `GET /governance/replay-state`
- `GET /governance/replay-change/:entryId`
- `GET /governance/diff`
- `GET /governance/impact/:entryId`
- `GET /governance/lineage/:subjectId`

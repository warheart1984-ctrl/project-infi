# Reasoning Exchange Protocol Spec

This spec defines the smallest active AAIS contract for admitting external or
cross-system reasoning without weakening local law.

## What It Is

It is a neutral envelope plus a predictable handshake.

The shared layer defines:

- how reasoning is packaged
- how AAIS receives it
- how AAIS returns an admit/reject/partial decision

The shared layer does not define truth.

AAIS still decides locally whether a packet is usable.

## Compatibility Profile

External reasoning that asks for continuity-grade admission should align with
the canonical
[`AAIS_REASONING_PROFILE.md`](AAIS_REASONING_PROFILE.md): evidence references,
declared assumptions, alternatives, bounded uncertainty, law surface,
continuity impact, and governed recommendations.

CCS object references should conform to
[`CCS_CORE_SCHEMA.md`](CCS_CORE_SCHEMA.md) and
[`../../schemas/ccs_core_objects.v1.json`](../../schemas/ccs_core_objects.v1.json).

## Canonical Packet

```json
{
  "version": "1.0",
  "type": "reasoning_packet",
  "id": "uuid",
  "timestamp": "iso8601",
  "payload": {
    "claim": "string",
    "reasoning": "string",
    "evidence": ["string"],
    "confidence": 0.0
  },
  "meta": {
    "source": "system_id",
    "domain": "optional",
    "tags": ["string"]
  }
}
```

## Active Rules

- malformed packets fail fast before governance
- unsupported versions return `REJECT` with `unsupported_version`
- unsupported packet types return `REJECT` with `unsupported_packet_type`
- no extra top-level, payload, or meta fields are allowed
- no side-channel context is passed through the packet body
- size and complexity stay bounded

## First Runtime Boundary

AAIS admits this protocol through:

- `POST /api/reasoning/evaluate`

The route flow is:

1. parse and validate the envelope
2. normalize the packet
3. apply phase gate, verification gate, and module governance
4. return `ADMIT`, `REJECT`, or `PARTIAL`
5. log through the existing runtime/governance stack

## Handshake Response

```json
{
  "status": "ADMIT | REJECT | PARTIAL",
  "reason": "string",
  "confidence_adjustment": 0.0,
  "notes": []
}
```

## Architectural Placement

This protocol belongs at the governance boundary.

It is:

- not a shared truth layer
- not a memory layer
- not an identity layer
- not a replacement reasoning engine

It is the narrow ingress where outside reasoning asks for admission under local
AAIS law.

# Emergent Substrate

A 5-phase interaction loop with constitutional governance for emergent cognitive systems.

## Overview

Emergent Substrate implements a cognitive architecture where raw entropy (ideas, feelings, metaphors, challenges, extensions, mutations) is shaped through constitutional governance into governed specifications. The system maintains identity, continuity, and an append-only evolution log.

## Architecture

### 5-Phase Loop

1. **INPUT** - Entropy packet persisted
2. **STABILIZATION** - OrderEngine.shape() → StructuredModel
3. **VALIDATION** - GovernanceLayer.validate() → PASS/WARN/BLOCK
4. **FEEDBACK** - Optional feedback hook fires
5. **INTEGRATION** - OrderEngine.integrate() → MemoryLayer

### Governance Stack

| Priority | Constitution | Blocks On |
|----------|--------------|-----------|
| 5 | AAIS/AAES-OS | Recursive self-modification, adaptation gate violations, constitution-freeze enforcement, runaway loops |
| 10 | CIB-1 | Harmful content signals, identity nullification, epistemic contradiction |
| 20 | GPS | Profile axis drift, metaphor collapse, homogenization after 10 identical structure types |
| ∞ | Core (built-in) | no_harmful_drift, no_pure_chaos, no_over_constraint, identity_continuity |

## Installation

```bash
cd emergent-substrate
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn api.main:app --reload --port 8000
```

## API Endpoints

- `POST /loop/run` - Run the full 5-phase interaction loop
- `GET /state` - Get current substrate state
- `GET /memory/identity` - Get all identity memory
- `POST /memory/identity` - Set identity memory key-value pair
- `GET /evolution/timeline` - Get evolution timeline
- `GET /constitutions` - Get attached constitutions
- `POST /entropy/emit` - Emit entropy packet without running full loop
- `GET /profile/axes` - Get GPS profile axis values
- `GET /health` - Health check
- `POST /state/reset` - Reset substrate state

## Example Usage

```bash
curl -X POST http://localhost:8000/loop/run \
  -H "Content-Type: application/json" \
  -d '{
    "packet_type": "idea",
    "raw_content": "What if governance was a living membrane — permeable to good ideas, impermeable to harmful ones?",
    "emotional_tone": "curious",
    "cross_domain": ["biology", "constitutional law", "systems theory"],
    "intensity": 0.85,
    "tags": ["governance", "emergence", "membrane"]
  }'
```

## Execution Contract

`state.is_alive()` is `True` when:
- At least one entropy packet emitted
- At least one governed spec produced
- At least one constitution attached
- At least one full loop iteration completed
- Identity memory is non-empty

## Database Schema

9 tables + 2 views:
- `entropy_packets` - Every raw packet emitted
- `structured_models` - Pre-governance shaped output
- `governed_specs` - Post-governance final artifacts
- `identity_memory` - Key-value: worldview, aesthetic, tone, philosophy, patterns
- `continuity_memory` - Goals, active projects, constitution IDs
- `evolution_events` - Append-only ledger
- `constitution_hooks` - Registry of attached constitutions
- `validation_results` - Per-model governance verdicts
- `substrate_states` - Session snapshots
- `v_full_loop_trace` - View: packet → model → spec → validation
- `v_evolution_timeline` - View: Evolution log + spec titles

## Testing

```bash
pytest tests/ -v
```

## Docker

```bash
docker compose up --build
```

## Constitutional Alignment

This system operates under constitutional governance principles:
- AAIS/AAES-OS (Priority 5) - System-level adaptation gates
- CIB-1 (Priority 10) - Cognitive integrity baseline
- GPS (Priority 20) - Generative profile specification

## License

MIT

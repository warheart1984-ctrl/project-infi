# OTEM Autonomic Routines Contract

Status: **active contract** (Release 33)

## Purpose

Low-risk governed reflexes under OTEM without bypassing operator authority for high blast-radius actions.

## ARC classes

| Class | Meaning |
|-------|---------|
| ARC-0 | Read-only |
| ARC-1 | Idempotent local writes |
| ARC-2 | Requires explicit operator approval |

## Activation

- `AAIS_OTEM_AUTONOMIC_ENABLED=1`
- `AAIS_OTEM_AUTONOMIC_ARC_CEILING` (default `ARC-1`)

## Forbidden autonomic

Repo patch apply, forge mutation, immune quarantine, biometric storage.

Registry: [governance/otem_autonomic_routines.v1.json](../../governance/otem_autonomic_routines.v1.json)

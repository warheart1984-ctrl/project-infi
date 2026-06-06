# SEAM-TRANSITION-002 — Dual-path chat

## Title

Workflow shell `/chat` vs Jarvis `/api/chat/sessions` (governed transition)

## Classification

- seam class: `routing_seam`
- boundary: `chat_ingress_duality`
- severity: `low` (governed transition)
- status: closed (governed)
- discovery state: Wave 6 GA closure

## Summary

Two chat ingress paths coexist: FastAPI shell routes (`POST /chat`) and Flask Jarvis routes (`POST /api/chat/sessions`). Canonical operator documentation uses the Jarvis path under `/legacy_api`.

## Law Definition

Canonical operator chat path is `/legacy_api/api/chat/sessions/*`. Shell `/chat` remains compat-only and must not grant additional execution authority.

## Closure

- [x] AAIS_CHAT_ROUTING_CONTRACT published
- [x] wave6-transition-gate regression tests
- [ ] Single-path FastAPI-native Jarvis (post-GA)

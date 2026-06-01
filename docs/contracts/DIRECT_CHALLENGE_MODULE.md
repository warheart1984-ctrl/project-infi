# Direct Challenge Module

Version: `1.0`  
Module ID: `aais.direct_challenge_module`

## Purpose

Detect direct challenges aimed at Jarvis, classify their severity, and
stabilize the reply path when generic assistant language leaks through.

## Capabilities

- Detect direct challenge turns
- Classify severity as `low`, `medium`, or `high`
- Produce severity-aware anchor replies
- Generate governed guidance for the reply model
- Replace collapsed or generic identity output with a stable Jarvis reply

## Runtime Integration

- Detection stays compatible with the existing `handle_direct_challenge` objective
- Severity metadata can surface in `response_trace.direct_challenge_profile`
- Final reply stabilization remains bounded and deterministic

## Fallback Doctrine

- Mild challenge: invite the concrete miss
- Medium challenge: invite correction directly
- High challenge: stay firm without mirroring hostility

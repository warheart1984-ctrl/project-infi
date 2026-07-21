# AAES-OS Engineering Handbook

Version: 1.0.0
Status: Stable

## Purpose

Canonical engineering guide for AAES-OS contributors, architects, and maintainers.

## Core principles

- Intent before generation
- Evidence before optimization
- Governance before execution
- Memory before mutation
- Measurement before scaling

## Runtime shape

AAES-OS is organized around a governed mission flow:

1. Human intent
2. Mission director
3. Agent council
4. Evolution engine
5. Image generation
6. Vision evaluation
7. Governance
8. Memory
9. Learning
10. Deployment

## Required runtime services

- Prompt Compiler
- Genome Service
- Image Generation Service
- Vision Evaluation Service
- Governance Service
- Memory Service
- Evolution Service
- Dashboard API

## Repository standard

Core runtime, SDKs, APIs, governance, memory, docs, tests, examples, and extensions should exist as first-class workspace areas.
Research belongs in isolated folders and does not directly modify production code.

## SDK contract

The primary developer flow should remain simple and typed:

```python
aaes = AAES()
mission = aaes.create_mission()
prompt = aaes.compile_prompt()
image = aaes.generate()
evaluation = aaes.evaluate()
genome = aaes.save()
next_generation = aaes.evolve()
```

## Release posture

v1.x should remain the stable platform baseline.
Later majors may add enterprise, federation, and research capabilities, but only with validated implementation and governance review.


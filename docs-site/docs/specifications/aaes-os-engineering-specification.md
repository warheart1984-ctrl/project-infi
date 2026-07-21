---
title: AAES-OS Engineering Specification
---

# Engineering Specification

This page states the canonical engineering architecture for AAES-OS v1.x.

## Scope

All implementation artifacts should remain traceable to this specification.

## Architecture

- Core runtime: prompt compiler, genome engine, image generation, vision evaluation, evolution engine, memory engine, governance engine, mission director, agent council
- Support services: REST API, Python SDK, dashboard, authentication, logging, configuration, deployment
- Extensions: plugins only, not runtime-kernel forks

## Boundaries

- Core runtime: stable and deterministic
- Extensions: officially supported
- Research: isolated from production
- Labs: exploratory only

## API rules

- Version every public API
- Publish request schema, response schema, error model, authentication requirements, version compatibility, and deprecation policy
- Require a major version for breaking changes


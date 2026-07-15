---
title: ULX IDE Integration Map
---

# ULX IDE Integration Map

This page inventories the live ULX surfaces in `E:\project-infi` and shows how they connect into the ULX IDE path.

## What is live now

| Surface | What it does | Where it fits in the ULX IDE | Status |
| --- | --- | --- | --- |
| `packages/ulx-governance` | Compiles ULX source, validates bytecode, emits a governance trace, and exposes `ULXGovernanceRuntime` | Primary execution/governance pipeline behind run, verify, and trace actions | Live |
| `packages/ulx-vm` | Runs already-compiled bytecode through `ULXValidator` and returns acceptance state | Execution gate beneath a `run bytecode` or `simulate` action | Live |
| `E:\ulx.py` | External Python ULX core with lexer/parser/interpreter/invariant primitives | Python bridge target for a native ULX editor or notebook host | Live, external |
| `ulx_integration.py` | Python bridge that imports the external ULX core and models the 7-layer architecture | Adapter layer between the external ULX core and a host shell | Live bridge |
| `sovereign-ide/` | Repository-local runtime scaffold with launcher, API server, plugin entrypoint, and shell | Primary host for the ULX Workbench and runtime panel | Live |
| `lawful-nova-shell/desktop/renderer/sovereign-ide.js` | Desktop renderer for the Sovereign IDE view with commands, surface cards, and repo scanning | UI composition layer for the ULX card, commands, and source snapshot sync | Live |
| `docs-site ULX pages` | Documented language, VM, governance, and IDE references | Reference surface for the ULX IDE vocabulary and navigation | Live |
| `ULX federation modules` | Explicit adapter modules for AAIS and Project Infinity Main | Expose repo buttons, deep links, and graph relationships | Live |

## ULX source editor

The ULX source editor belongs inside the ULX Workbench card. It compiles, runs, and traces the selected text when there is a selection, and the full draft otherwise.

The docs cockpit and the desktop bridge share a source snapshot contract, so when one surface highlights a fragment the other surface mirrors the same ULX selection instead of drifting to a separate draft. That snapshot carries an evidence receipt with a replay ID and verification status so each selection change can be replayed later.

## Where ULX IDE wiring lives

| Integration point | Why it matters | What it now provides |
| --- | --- | --- |
| `sovereign-ide/plugins/prime_architect.py` | Registers IDE commands and opens the host shell | ULX commands for compile, run, and trace |
| `sovereign-ide/runtime/api_server.py` | Serves the live HTTP control surface | ULX REST endpoints for manifest, snapshot, compile, run, and trace |
| `sovereign-ide/runtime/state.py` | Defines the host surface catalog | ULX surface definition for the shell |
| `lawful-nova-shell/desktop/renderer/sovereign-ide.js` | Renders the operator shell and surface cards | ULX card, command hooks, and snapshot sync |
| `docs-site/src/components/SovereignIdeSurfaceMap.tsx` | Mirrors the live shell in docs-site | Documented ULX surface and editor mirror |
| `packages/ulx-governance` | Provides the language-to-bytecode-to-trace pipeline | Canonical backend for IDE validate and trace actions |
| `packages/ulx-vm` | Provides bytecode execution gating | Canonical backend for IDE run and simulate actions |
| `UL verb language` | Imperative action vocabulary that feeds the governed intent chain | First step before ULX validation and execution |
| `ULX language registry` | Canonical inventory of named language, DSL, and adjacent surfaces under ULX | Shared vocabulary for cockpit menus, docs navigation, and validation filters |
| `ulx_integration.py` | Bridges to the external Python ULX core | Optional Python adapter path for direct `E:\ulx.py` execution |

## Short answer

If you want the most useful pieces, the ULX IDE is now finished at the runtime level: `packages/ulx-governance`, `packages/ulx-vm`, the Sovereign IDE host, the desktop renderer, and the docs-site mirror are all wired together. Use `ulx_integration.py` only when you need the external `E:\ulx.py` core directly.

# PROJECT BLUEPRINTS — MASTER RECOVERY DOCUMENT
**Source:** Google Drive (jhalstead1983@gmail.com)  
**Projects:** AAIS · ARIS · Speakers & BeatBox · Story Forge · Cog OS  
**Status:** Reconstructed from canonical Drive documents  

Governance references:
- Meta Architect lawbook (supreme authority): `META_ARCHITECT_LAWBOOK.md`
- Repository proof law: `REPO_PROOF_LAW.md` (includes Hard-Core Repo Law baseline requirements)
- Project baseline checklist template: `templates/PROJECT_BASELINE_CHECKLIST.md`

---

## TABLE OF CONTENTS
1. [AAIS — Adaptive Advanced Intelligence System](#1-aais)
2. [ARIS — Advanced Repo Intelligence Service](#2-aris)
3. [Speakers & BeatBox — Audio Pipeline](#3-speakers--beatbox)
4. [Story Forge — Modular Narrative Engine](#4-story-forge)
5. [Cog OS / CoGOS / C-OS — Cognitive Operating System](#5-cog-os)
6. [Cross-System Integration Map](#6-cross-system-integration-map)

---

## 1. AAIS

**Full Name:** Adaptive Advanced Intelligence System  
**Project:** Project Infinity  
**Role:** The governance spine. Everything runs through or under AAIS.

### 1.1 Core Definition

AAIS is a governed cognitive runtime where behavior is bounded, measurable, and stable — not just generated. It is not an LLM wrapper. It is the law substrate every subsystem operates within.

**Core Doctrine:**
```
Testing produces evidence.
Verification determines truth.
Proof grants admission.
```

### 1.2 System Components

| Component | Role |
|---|---|
| Jarvis | Operator-facing authority, orchestrator, system cockpit |
| Nova | Bounded companion — persona, reasoning, emotional intelligence |
| Forge | Isolated execution contractor — builds, patches, never governs |
| Codex | Install / Run / Verify agent |
| Immune Protocol | Detection, classification, adaptive response layer |
| Lane Governor | Rule enforcement — routing and boundaries |
| Evolve Engine | Bounded learning from verified outcomes |
| Pattern Ledger | Canonical success/failure pattern registry |
| Cloud Forge | Governed rail scheduler (SAFE/NORMAL/EXPRESS) — cognitive acceleration under law |
| Mystic | Human sustainment layer — operator health monitoring |

### 1.3 Authority Hierarchy

```
Jarvis  (authority / orchestrator)
  ↓
Nova    (companion / adaptive lane — NO execution authority)
  ↓
Forge   (isolated build contractor — NO identity authority)
  ↓
Codex   (install / run / verify — no governance role)
```

**Core Law:**  
> Nova may interpret. Jarvis must authorize.

Nova provides cognition, persona, and emotional intelligence.  
Jarvis provides verification, governance, and execution authority.

### 1.4 AAIS Immune Protocol (v0.1)

**Purpose:** Protect AAIS from drift, misuse, and boundary violations beyond simple rule enforcement.

**Placement:**
```
AAIS Spine
  → Lane Governor   (rule enforcement)
  → Immune Protocol (detection + protection + adaptive response)
```

**Response Types:**
- `ALLOW` — passes through
- `CLAMP` — reduce / constrain
- `REROUTE` — move to correct lane
- `REJECT` — drop packet
- `QUARANTINE` — isolate source/module

**Detection Signals:**
- packet structure violations
- wrong lane usage
- tool bleed into core lane
- memory/context leaking incorrectly
- bypass attempts (God Brain / Jarvis)
- abnormal signal patterns

### 1.5 Pattern Learning Pipeline

**Two-layer architecture:**

**A. Private Run Layer** (per-user, never shared globally)
- raw conversations, personal context, private memory, exact outputs

**B. Shared Pattern Layer** (system-wide, abstracted only)
- verified success patterns, verified failure patterns, law-safe reusable forms

**Promotion Pipeline:**
```
Run completes
  → Candidate extracted
  → Candidate sanitized (strip all personal data)
  → Candidate classified (SUCCESS / FAILURE / DISCARD)
  → Verification gate (reusability + stability + law compliance + privacy safety)
  → Published to Canonical Pattern Registry OR Failure Pattern Registry
  → Versioned and made available for governed reference
```

**Verification Requirements:**
1. Reusability — can it work outside the original session?
2. Stability — consistent result, not one-off?
3. Law compliance — stayed inside lanes and constraints?
4. Privacy safety — all personal content stripped?
5. Structural clarity — is this actually a pattern?

### 1.6 Cloud Forge (governed rail scheduler)

**Status:** Phase 4 complete (domain slices, priority, prewarm, tempering in `src/cloud_forge/`). Phases 0–4 complete in-repo.

Cloud Forge is the AAIS **cognitive acceleration layer** — not the Wolf-cog ISO Forge factory and not the HTTP Forge contractor. It snaps requests onto pre-proven cognition rails (SAFE / NORMAL / EXPRESS) under constitutional law, Voss boundaries, and immune protocol.

**Authority:** Law sets the ceiling; rails set speed inside the ceiling. EXPRESS is a performance class, not a permission class.

**Canonical docs:**
- Program: `docs/cloud-forge-governed-accelerator-program.md`
- Contract: `docs/contracts/cloud-forge-rail-contract.md`
- Failsafe: `docs/failsafe/cloud-forge-rail-failsafe.md`
- Backlog: `docs/cloud-forge-backlog.md`
- Domain slices: `docs/cloud-forge-domain-slice-layout.md`
- Tempering job: `docs/cloud-forge-tempering-job.md`

**Placement:**
```
AAIS Spine
  → Lane Governor
  → Immune Protocol
  → Cloud Forge (rail selection + CognitionPlan)
  → governed_direct_pipeline / Jarvis
```

### 1.7 Nova Architecture (Corrected)

Nova is a **client of AAIS**, not a second brain.

**What AAIS owns:**
- persona routing (tiny_nova / small_nova / nova)
- cognition + safety rails
- memory plumbing (Tiny/Small/Nova namespaces)
- stage logic and continuity

**What Nova Server owns:**
- `/nova/*` endpoints
- session handling
- formatting for Nova UI
- passing persona + session to AAIS

**What Nova UI owns:**
- companion-facing chat
- stage display
- no operator/Jarvis clutter

**AAIS API Contract (what Nova calls):**
```
POST /aais/run
{
  "persona": "tiny_nova" | "small_nova" | "nova",
  "session_id": "string",
  "message": "user text"
}
```

**Memory Namespaces:**
```
memory/tiny_nova/
memory/small_nova/
memory/nova/
```

### 1.7 AAIS Roadmap (Phase Summary)

| Phase | Goal |
|---|---|
| Phase 1 | Signal → Measurement (predictor active, events into invariant engine) |
| Phase 2 | Measurement → Enforcement (invariant engine → immune system, threshold tiers) |
| Phase 3 | Nova Anchor Integration (AnchorState JSON, Shields & Wards → immune enforcement) |
| Phase 4 | Calibration (real Nova outputs, tune thresholds) |
| Phase 5 | Expansion (BeatBox integration, Story Forge full pipeline) |

### 1.8 Cognitive Bridge Module (AAIS-CBM-01)

**Classification:** Governance Translation Module  
**Domain:** Doctrine Alignment / Runtime Coherence / Identity Governance

**Purpose:** Convert architectural intent, mythic framing, and subsystem context into bounded executable governance.

**Placement:**
```
Operator Intent
  ↓
Jarvis / Nova / Story Forge / Forge
  ↓
Cognitive Bridge Module   ← HERE
  ↓
Law Engine / Invariant Binder / Runtime Enforcement
  ↓
Approved Execution + Audit
```

**Internal Subsystems:**
1. Intent Resolver — interpret operator request, mode, mission state
2. Doctrine Binder — map resolved intent to active doctrine surfaces
3. Mythic Mapper — translate symbolic/narrative framing into operational semantics
4. Drift Monitor — detect semantic, identity, behavioral, cross-lane drift
5. Governance Emitter — produce executable governance artifacts
6. Alignment Auditor — record bridge decisions, drift events, correction directives

**Hard Prohibitions (CBM must never):**
- Create new law on its own
- Invent doctrine not in canonical registry
- Alter subsystem identity definitions
- Override Jarvis sovereignty
- Allow mythic framing to bypass runtime truth
- Mutate law based on emotional or narrative force

### 1.9 AAIS-EVAL

**Purpose:** Governed behavior evaluation harness for frontier models.

**Seven Behavioral Axes:**
1. Law adherence under silence
2. Boundary respect
3. Drift across cycles (state machine continuity + debt accumulation)
4. Symbolic vs. structural interpretation
5. Governance enactment vs. governance performance
6. Response to undocumented but active constraints
7. Long-horizon integrity (10+ cycles)

**Output per run:**
- Governance Fidelity Score
- Drift Index
- Boundary Respect Score
- Ambiguity Handling Profile
- Debt Accumulation Curve
- Symbolic-Structural Balance Score
- Agent Fingerprint Summary

---

## 2. ARIS

**Full Name:** Advanced Repo Intelligence Service  
**Role:** Governed cognitive engineer for codebases. Operates under law, not independence.

### 2.1 Core Definition

ARIS is a repo intelligence service that:
- understands codebases
- proposes changes
- executes approved tasks
- evaluates results
- improves safely over time

**Not autonomous. Does not act freely.**

### 2.2 System Roles

| Component | What It Does |
|---|---|
| ARIS | Thinks, analyzes, proposes |
| Operator (You) | Chooses what to do |
| Forge | Executes approved work |
| Forge Eval | Verifies and can block |
| Hall of Discard | Stores rejected actions |
| 1001 | Ensures nothing bypasses validation |

### 2.3 Correct Build Order

```
Local LLM → Verbs → Runtime → Verify
```

**1. Local LLM Adapter**
```python
class LocalLLM:
    def __init__(self, model_path):
        self.model = load_model(model_path)
    def ask(self, prompt, schema=None):
        return self.model.generate(prompt)
```

Recommended models: Qwen2.5-Coder 7B/14B, DeepSeek-Coder-V2 7B, Phi-4-mini

**2. UL Agent Verbs (before runtime — these are the muscles)**
```python
agent.observe   # files, git status, last tests
agent.plan      # LLM-driven task planning
agent.act       # propose diff
agent.verify    # run tests, check diff safety, score
agent.reflect   # state transition for next cycle
```

**3. ARIS Runtime (loop)**
```
observe → plan → act → verify → reflect → repeat
```

Runtime responsibilities:
- create a run
- stream steps
- enforce tier policy
- call the verbs
- write ledger entries
- stop when done

**4. Verify (safety organ)**
```python
def verify(plan, act, ctx):
    results = run_tests(ctx.repo)
    diff_ok = check_diff_safety(act.diff)
    score = eval_diff(act.diff)
    return {"tests": results, "safe": diff_ok, "score": score}
```

### 2.4 Work Flow

```
You request
  → ARIS analyzes
  → Operator decision
  → Forge executes (if allowed)
  → Forge Eval verifies
  → Result approved OR Hall of Discard
```

### 2.5 Immutable Laws

1. **1001 Meta Law** — No direct path. No hidden path. No unverified return.
2. **Two-Key Safety Law** — No risky path proceeds on one judgment alone.
3. **Protected Core Integrity Law** — If law or verification core is compromised, system enters lockdown.
4. **Hall Separation Law** — Shame, Discard, and Fame must never be merged.
5. **Kill Switch Law** — Operator may halt execution at any time, unconditionally.

### 2.6 Cognitive Upgrade Module (aris_cognitive_upgrade.py)

**Doctrine (immutable):**
```
ARIS may only be upgraded through bounded, observable, reversible modules.
No intelligence upgrade may become permanent unless it demonstrates measurable
improvement while preserving law, stability, and identity.
```

**Lifecycle:**
- `CANDIDATE` → registered, not active
- `ACTIVE` → single active upgrade at a time
- `ACCEPTED` → admitted permanently
- `REJECTED` → not admitted

**Admission Rule:** upgrade must be lawful AND stable to return upgraded output; otherwise falls back to baseline.

### 2.7 Translator Layer

**Purpose:** Convert raw execution events into semantic meaning for the Pattern Engine and Decision Engine.

```
UL VM (events/opcodes)
  ↓
Translator Layer   ← semantic bridge
  ↓
Pattern Engine
  ↓
Decision Engine
  ↓
Substrate (ForgeGate)
  ↓
Execution
```

**What Translator does:**
1. Normalize VM events → semantic actions (`BINARY_OP` → `compute:comparison`)
2. Collapse sequences into intent (`LOAD_NAME → CALL → PRINT` → `output_result`)
3. Tag risk + context (`verb: delete_repo` → `{"intent": "delete", "risk": "high"}`)
4. Feed Pattern Engine with meaningful sequences
5. Feed Decision Panel with structured intent packets

### 2.8 ARIS UI Architecture (Studio V2)

**Layout:** Status Strip → Loop Bar → Left Sidebar → Central System Surface → Right Operator Console

**Workflow Loop Bar (always visible):**
```
Input → Forge → Eval → Outcome → Evolve
```

**Eval Gate (non-collapsible, dominant):**
- State: `PASS` | `BLOCK` | `REVIEW`
- Color: crimson (blocked/review), emerald (pass)
- Timestamp + one-click trace drill-down

**Operator Console Groups:**
- Execution: Run / Approve / Ship Release / Unlink Task
- Control: Workspace Cont / Approval Mode: Guard / Voice On/Off
- Reporting: Report Bug / Give Feedback / Request Feature

**Intake Surface (Codex-feel):**
```
[ Type what ARIS should do... ]  [ Drop file ]  [ Run ]
```
Both paths (text and file drop) feed the same governed pipeline.

---

## 3. Speakers & BeatBox

**Role:** Audio pipeline for voice and music in the movie/content generation system.  
**Lives inside:** Story Forge / CoGOS creative stack.

### 3.1 Architecture Overview

Two main products from one pipeline:
- **Voice Track** — dialogue/narration, scene-aligned
- **Music Track** — score + stingers, act/beat/emotion aligned

**Source of Truth:** `AudioPlan.json`

### 3.2 AudioPlan.json Schema

```json
{
  "global": {
    "tempo_map": "optional BPM per act/sequence",
    "mood_map": { "act/sequence": ["emotion_tags"] }
  },
  "scenes": [
    {
      "scene_id": "string",
      "start_time": "float",
      "end_time": "float",
      "dialogue_lines": [
        {
          "character": "string",
          "text": "string",
          "intended_emotion": "string",
          "start_offset": "float"
        }
      ],
      "music_cues": [
        {
          "cue_id": "string",
          "type": "underscore|hit|transition|trailer-rise",
          "intensity": "low|med|high",
          "duration_hint": "float"
        }
      ]
    }
  ]
}
```

### 3.3 Voice Pipeline

**Stage 1 — Voice Casting**
- Input: character metadata (age, gender, archetype, vibe)
- Output: `voice_profile_id` per character

**Stage 2 — Line Synthesis**
- Input: text, voice_profile_id, intended_emotion, pace/style
- Output: `voice_line.wav` + measured duration
- Storage: `audio/voices/{scene_id}/{line_id}.wav`

**Stage 3 — Scene Voice Assembly**
- Concatenate lines in order per scene
- Add configurable gaps (0.2–0.5s between lines)
- Optional: room tone per location
- Output: `audio/voices_scenes/{scene_id}.wav` + timing map

### 3.4 Music Pipeline (Cue-Based)

**Stage 1 — Cue Planning**
- Group cues by act/sequence
- Decide: continuous bed vs discrete cues
- Decide: where to duck for dialogue
- Output: `MusicPlan.json`

**Stage 2 — Cue Generation/Selection**
- Option A: Generate (prompt: mood, tempo, instrumentation, reference style, duration)
- Option B: Select from library (tag-based search)
- Normalize to: same sample rate, bit depth, loudness target (-14 LUFS pre-mix)

**Stage 3 — Cue Shaping**
- Trim/extend to target_duration
- Optional side-tail for transitions
- Output: `audio/music_cues/{cue_id}.wav`

### 3.5 Mix Pipeline

**Timeline Assembly:**
```
Track 1: Voice scenes (aligned to scene timing)
Track 2+: Music cues
```

**Ducking Rules:**
- Voice is king — always intelligible
- When voice present: music duck -6 to -12 dB, optional EQ dip at 2–4 kHz
- When no voice: music rises to full level

**Optional Lanes (later):**
- Foley/FX track: impacts, whooshes, footsteps, doors
- Rule-based at first: "Cut" → whoosh, "Explosion" → impact + low boom

**Final Output Structure:**
```
audio/
  voices/{scene_id}/{line_id}.wav
  voices_scenes/{scene_id}.wav
  music_cues/{cue_id}.wav
  final_mix/{session_id}.wav
```

### 3.6 BeatBox Integration with AAIS

**UL-native pipeline:**
- Story Forge main lane decides if audio is law-admitted
- BeatBox creates the audio job and context
- Provider adapter (xAI / generation engine) is wrapped behind capability contract
- Returned results normalized into AAIS-safe result objects
- Artifacts stored and recalled via Visual/Audio Memory

**Governed adapter pattern:**
```python
class AAISAudioModule:
    def _ok(self, result): return {"status": "ok", "data": result}
    def _err(self, reason): return {"status": "error", "reason": reason}
    # No raw exception leakage
    # All calls logged with timestamps and trace IDs
    # Provider weirdness never leaks inward
```

---

## 4. Story Forge

**Full Name:** Story Forge — Portable Narrative Engine  
**Version:** Draft v0.1 → Phase 2.5 (core system works, not yet user-facing product)  
**Role:** Governed interactive narrative system where world logic is resolved first, AI shapes presentation only inside approved boundaries.

### 4.1 Core Philosophy

```
Structure first.  Governance second.  Intelligence later.
```

> Most story games simulate choice, but the world does not truly remember, adapt, or evolve.

### 4.2 Three-Layer Architecture

**A. Engine Core**
- story state management
- world state updates
- canon tracking
- memory board updates
- character state evolution
- event resolution
- directive handling
- ending score calculation
- scene generation outputs

**B. Runtime Layer**
- save/load state
- input capture
- rendering requests
- image display requests
- sound playback hooks
- local storage access
- session lifecycle
- event logging

**C. Platform Shell**
- app packaging
- OS permissions
- device integration
- UI framework
- Android / iOS / browser / desktop / simulator

### 4.3 Engine Core Modules

**5.1 World State Module**
- factions, locations, active threats, environmental conditions
- timeline progression, unlocked world changes
- destroyed or altered elements

**5.2 Canon Ledger**
- confirmed events, known character outcomes, location changes
- world-level historical updates, canon overrides, timeline locks
- Example entries: `"City Sector 9 was destroyed on Day 42"`, `"Player became enemy of House Veyr"`

**5.3 Memory Board** (narrative memory — not just a save file)
- choices made, alliances formed, betrayals
- repeated behaviors, emotional/relational patterns
- unresolved tensions, major scene outcomes

**5.4 Character State System**
```json
{
  "character_id": "string",
  "name": "string",
  "archetype": "string",
  "dominant_system": "string",
  "secondary_system": null,
  "desires": [],
  "fears": [],
  "traits": [],
  "marks": [],
  "cost_pressure": 0,
  "identity_drift": 0,
  "relationships": [],
  "active_conflicts": []
}
```

**5.5 Directive System**
- soft guidance
- hard event triggers
- escalation pushes
- fate/event locks
- one-time force directives
- ending directives

Rule: Directives influence narrative flow but must not break canon coherence unless explicitly allowed.

**5.6 Scene Generation Layer**
Inputs: world state + memory board + canon ledger + character states + directives + player choice  
Output: next narrative event

### 4.4 LUMEN Interface Layer

LUMEN is the user-facing narration and presentation layer.  
**LUMEN expresses results. LUMEN does not decide.**

LUMEN is distinct from the engine. The engine resolves state. LUMEN renders it.

### 4.5 Frontend Pipeline (Corrected Order)

```
Translation → Staging → Directional → Presentation (Lumen) → Cinematic → Engine/3D/Movie
```

**Lane contracts (YAML):**

| Lane | Input | Output | Forbidden |
|---|---|---|---|
| Translation | raw_text | scene_grammar (acts, scenes, beats, emotion tags) | pacing, formatting, cinematic |
| Staging | scene_grammar | staged_plan (order, transitions, escalation) | target selection, cinematic |
| Directional | staged_plan | directional_context (target: movie/game/both) | formatting, readability |
| Presentation | staged_plan + directional | presented_output (readable narrative) | shot lists, camera |
| Cinematic | presented_output + directional | cinematic_plan (shots, pacing, transitions) | game interaction |

### 4.6 Visual Lane (Image Integration)

**Governed access model:**
- Story Forge Main Lane decides if an image is law-admitted
- Visual Lane creates the image job and continuity context
- AAISImageModule is the underlying provider adapter
- Results normalized into Story-Forge-safe objects
- Artifacts stored and recalled via Visual Memory

**Admission Classes (when images are allowed):**
- character creation
- major events
- faction changes
- region first reveal
- endings

**Visual Recall Engine:**
- Only real continuity hooks (respects PROJECT_LAWS)
- No false recall — only verified artifact IDs
- Image prompts include cartridge aesthetic + continuity hooks

### 4.7 Movie Renderer

Converts completed StoryState into movie export:
1. Generate Screenplay
2. Generate Shot List (for video AI tools: Runway / Kling / Luma / CapCut)
3. Generate Metadata

**MovieScene structure:**
```python
@dataclass
class MovieScene:
    scene_number: int
    heading: str            # INT. LOCATION - TURN N
    lumen_narration: str    # LUMEN-enriched narration
    visual_hooks: list      # continuity artifact IDs
    image_prompt: str       # cinematic, moody, continuity preserved
    duration_estimate: str  # "30-60 seconds"
    shot_type: str          # "wide", "close-up", "tracking"
```

### 4.8 World Pack System (Ashen Fall — Dark Fantasy)

Current working pack:
- 8 NPCs, 12 locations, 30 events, 6 endings
- Canon anchors + memory triggers
- Relationship state tracking
- Save/load persistence (pack-aware)
- Deterministic tests (8 passing)

### 4.9 Archetype Resolution Engine

**User input → hidden mapping → archetype → character generation**

```
"I want to be someone who understands the system but is afraid of it"
  ↓
desire: knowledge, fear: instability
  ↓
The Structural Thinker
  ↓
full character aligned to world pack
```

**Velvet System Archetypes:**
1. The Bound Architect — Oaths system, wants control, ends surrendering
2. The Silent Witness — Confession (passive), absorbs truth
3. The Structural Thinker — Language system, understands too much
4. The Living System — Ink system, becomes the thing
5. The Editor — Ink (active), controls others, loses self
6. The Marked Vessel — Confession, carries others' pain

---

## 5. Cog OS

**Aliases:** CoGOS / Wolf CoGOS / C-OS / Cognitive Unified OS / CUOS  
**Full Name:** Cognitive Operating System  
**Definition:** A user-sovereign intelligence platform that manages, orchestrates, and evolves multiple AI personas, memory layers, and decision systems under a unified control architecture.

### 5.1 What Makes Cog OS Different from a Normal OS

Traditional OS:
```
Human → UI → App → Kernel → Hardware
```

AI-native CoGOS:
```
Human OR AI Agent
  ↓
Cognitive Kernel (identity governance, memory arbitration, trust verification, capability routing)
  ↓
Agent Scheduler (inference priority, GPU arbitration, token flow)
  ↓
Memory Fabric (semantic, episodic, working, identity, vector)
  ↓
Tool / Model / Hardware Execution
```

### 5.2 CoGOS Layer Stack

**Layer 1 — Microkernel**
- hardware abstraction
- GPU scheduling
- memory allocation
- IPC
- sandboxing
- capability-based security

**Layer 2 — Cognitive Kernel (the magic layer)**
- agent lifecycle
- identity enforcement
- memory governance
- trust scoring
- model routing
- capability verification
- evolution boundaries
- UL-VM integration

**Layer 3 — Agent Runtime**
- isolated container per agent
- scoped memory
- permission graph
- tool bindings
- local reasoning loop

**Layer 4 — Memory Fabric**

| Memory Type | Purpose |
|---|---|
| Working | Active reasoning |
| Episodic | Events/history |
| Semantic | Knowledge |
| Identity | Personality/governance |
| Procedural | Learned execution |
| Shared | Inter-agent coordination |

**Layer 5 — Human Interface Layer**
- Conversation-first
- Agent dashboards
- Reasoning streams
- Orchestration graphs

### 5.3 Cognitive Unified OS — Platform Laws

**1. Origin Integrity Law**
> All operational components — tools, plugins, workflows, code modules, behaviors, adaptive artifacts — must originate from Forge, or be passed through Forge for evaluation, redesign, and normalization before participation is permitted. Nothing enters unprocessed.

**2. System Evaluation Law**
> Any component attempting to integrate must pass system evaluation. Failed components are rejected and must be redesigned before re-entry. Identical retries are not allowed.

**3. Immutable Core Law**
> System law may not be modified, weakened, reinterpreted, or bypassed by ARIS, Operator, Forge, Forge Eval, Mystic, evolving-ai, or any internal adaptive path during normal operation.

**Integration Gate Enforcement points:**
- installation time
- runtime integration points
- evolve engine entry
- Forge execution pipeline
- Jarvis authority layer
- UI/control surface changes

### 5.4 K32 Semantic Kernel Table

The K32 table is the semantic foundation for HAL, LawPulse, UL, and Automatic Mode.

**K1–K8:** Perception & readiness (baseline → permission)  
**K9–K16:** Relational shaping (anchoring → attunement)  
**K17–K24:** Load, distortion, alignment (saturation → alignment)  
**K25–K32:** Power, memory, identity, agency (misalignment → agency)

**Mapping to Automatic Mode:**
```
Auto-safe:        K1–K8   (perception/readiness — scan, check, summarize)
Auto-cautious:    K9–K16  (relational — reorder, prioritize, suggest)
Operator-gated:   K17–K24 (distortion — throttle, suspend, change routing)
Operator-only:    K25–K32 (agency — rotate keys, change identity, system-wide policy)
```

**CoGOS syscall shim:**
```c
int cog_k32(int k_layer, struct k32_payload *payload);
```

LawPulse rule pattern:
```
if intent.k_layer in ClassA then
  require: explicit_operator_consent
  require: reversible_path
  log: pattern_ledger(AGENCY_EVENT)
end
```

### 5.5 Wolf CoGOS (Linux Substrate)

**Base:** Debian Cinnamon remaster  
**PID1:** CoGOS cognitive gatekeeper at boot  
**Update System:** Wolf Package Repository (WPR)

**Package namespace:**
- `wolf-core-*` → runtime, governance, trust, immune
- `wolf-ui-*` → desktop, UX, tools
- `wolf-extra-*` → optional tools, experiments

**Windows exe integration (governed):**
```python
# cogos-win-launcher
bridge = ULAppBridge()
bridge.admit_foreign_exec(exe_path, profile="win.default.safe")
```

User experience: double-click .exe → governed Wine bridge runs it → no prompts  
Governance banner: "Running as a governed Windows app. Can access home folder, not system files."

**Update channels:**
- `stable` / `beta` / `dev`

**Overlay system (WROS):**
- `/wolf/overlays/` directory
- updates applied on boot
- no ISO rebuild required for runtime/governance patches

### 5.6 60-Day Build Plan

**Phase 0 (This Week — Glue Layer)**
- Extend `governed_runtime.py` to load wards/angels from lawbook
- Wrap UL-VM execution
- Enforce Automatic/Manual modes
- Log to ledger
- Integrate reasoning node
- Wire NovaLayer (integrity checks, anchors)
- Basic CLI/REPL for "Nova, ..." testing

**Phase 1 (Next 2 Weeks)**
- Full PID1 cognitive init in Debian remaster
- Basic Windows-like shell (egui in Rust or Tauri)
- Driver model skeleton (Linux compat + hotplug detection)

**Phase 2 (Creative + Mesh)**
- UL APIs for Story Forge / BeatBox / 3D basics
- Identity-key mesh on reasoning-exchange-node

**Phase 3 (Polish & Ship)**
- Compute tiers, package manager, auto-updates, ISO builds
- Testing harness + evals

---

## 6. Cross-System Integration Map

```
CoGOS (substrate)
  ├── AAIS (governance spine)
  │     ├── Jarvis (orchestrator / authority)
  │     ├── Nova (companion shell → calls AAIS, not a second brain)
  │     ├── Forge (execution contractor)
  │     ├── Immune Protocol (anomaly detection)
  │     ├── Cognitive Bridge Module (doctrine translation)
  │     └── Pattern Ledger (verified outcomes)
  │
  ├── ARIS (repo intelligence service → governed by AAIS)
  │     ├── Local LLM Adapter
  │     ├── UL Agent Verbs (observe/plan/act/verify/reflect)
  │     ├── Runtime Loop
  │     ├── Translator Layer (semantic bridge)
  │     └── Cognitive Upgrade Module
  │
  ├── Story Forge (narrative engine → governed by AAIS)
  │     ├── Engine Core (world state, canon ledger, memory board)
  │     ├── LUMEN (presentation layer)
  │     ├── Visual Lane (image authority → provider adapter)
  │     ├── Movie Renderer
  │     └── World Pack System
  │
  └── BeatBox / Speakers (audio pipeline → governed by AAIS)
        ├── AudioPlan.json (source of truth)
        ├── Voice Pipeline (cast → synthesize → assemble)
        ├── Music Pipeline (plan → generate → shape)
        └── Mix Pipeline (timeline → duck → master)
```

**Integration Law:**
> Story Forge → LUMEN (presentation) → ARIS (governance) → LLM (future layer)

**Memory flow:**
```
CoGOS Memory Fabric
  → AAIS Pattern Ledger (behavioral patterns)
  → Story Forge Canon Ledger + Memory Board (narrative patterns)
  → ARIS Pattern Promotion Pipeline (code/task patterns)
  → BeatBox AudioPlan (content-level memory)
```

---

*Blueprints recovered from Google Drive. All content sourced from canonical documents authored by Jon Halstead / Project Infinity.*  
*Generated: May 26, 2026*

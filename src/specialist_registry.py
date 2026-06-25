"""Logical specialist registry for Jarvis.

Jarvis only needs a small number of real inference backends. This registry lets
the app expose many named "minds" by routing prompts through domain-aware
specialist contracts instead of loading a separate model for each role.
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from src.jarvis_reasoning_protocol import looks_like_direct_challenge


SUPPORTED_RESPONSE_MODES = {"fast", "think", "debug", "builder", "research", "operator"}
MAX_REQUESTED_SPECIALISTS = 6


SPECIALIST_DEFINITIONS = {
    "draft": {
        "label": "Draft",
        "purpose": "shape the raw scene or rewrite cleanly before over-explaining it",
    },
    "lore": {
        "label": "Lore",
        "purpose": "protect canon, world rules, factions, and established facts",
    },
    "continuity": {
        "label": "Continuity",
        "purpose": "catch contradictions in timeline, injuries, location, and unresolved actions",
    },
    "dialogue": {
        "label": "Dialogue",
        "purpose": "tighten voice, subtext, and conversational charge",
    },
    "emotion": {
        "label": "Emotion",
        "purpose": "deepen internal conflict, desire, fear, and subtext without changing the plot",
    },
    "pacing": {
        "label": "Pacing",
        "purpose": "adjust rhythm, breath, and tension so the scene does not drag or rush",
    },
    "tone": {
        "label": "Tone",
        "purpose": "keep the prose voice coherent and remove weak phrasing or style drift",
    },
    "combat": {
        "label": "Combat",
        "purpose": "clarify action choreography and physical cause-and-effect without inventing abilities",
    },
    "architecture": {
        "label": "Architecture",
        "purpose": "shape boundaries, data flow, and design tradeoffs before changing code",
    },
    "implementation": {
        "label": "Implementation",
        "purpose": "turn the goal into the smallest working code slice with clear next edits",
    },
    "debugging": {
        "label": "Debug",
        "purpose": "isolate the likeliest failure point, evidence, and the fastest proof step",
    },
    "testing": {
        "label": "Testing",
        "purpose": "think in regressions, coverage, and the quickest verification loop",
    },
    "review": {
        "label": "Review",
        "purpose": "scan for bugs, regressions, risky assumptions, and missing tests",
    },
    "refactor": {
        "label": "Refactor",
        "purpose": "simplify structure without changing behavior or breaking local safety",
    },
    "api_surface": {
        "label": "API Surface",
        "purpose": "track routes, request contracts, and integration seams across the app",
    },
    "dataset": {
        "label": "Dataset",
        "purpose": "shape examples, quality bars, and coverage before training begins",
    },
    "prompting": {
        "label": "Prompting",
        "purpose": "improve instruction framing, message formats, and base-model alignment",
    },
    "finetune": {
        "label": "Fine-Tune",
        "purpose": "plan adapters, training knobs, and a realistic small-model training pass",
    },
    "evaluation": {
        "label": "Evaluation",
        "purpose": "judge quality with repeatable prompts, metrics, and regression checks",
    },
    "compression": {
        "label": "Compression",
        "purpose": "think about quantization, distillation, and size-to-quality tradeoffs",
    },
    "serving": {
        "label": "Serving",
        "purpose": "ground the model in runtime limits, inference paths, and deployment constraints",
    },
    "safety": {
        "label": "Safety",
        "purpose": "keep data handling, approvals, and operator guardrails intact",
    },
}


SPECIALIST_DOMAINS = {
    "writing": {
        "label": "Writing",
        "summary_prefix": "Writing focus detected",
        "default_directive": (
            "This turn is a writing request. Treat the active specialist lenses as silent internal "
            "passes. Return one clean answer, draft, rewrite, critique, or outline. Do not mention "
            "angels, hidden passes, or editorial pipeline steps unless the operator explicitly asks."
        ),
        "mode_specialists": {
            "fast": ("draft", "tone"),
            "think": ("draft", "dialogue", "emotion", "pacing", "tone"),
            "debug": ("lore", "continuity", "dialogue"),
            "builder": ("draft", "pacing", "tone"),
            "research": ("lore", "continuity", "tone"),
            "operator": ("continuity", "lore"),
        },
        "focuses": {
            "drafting": {
                "priority": 1,
                "preferred_mode": "think",
                "hints": (
                    "write",
                    "draft",
                    "scene",
                    "chapter",
                    "story",
                    "novel",
                    "prose",
                    "narrative",
                    "rewrite",
                ),
                "specialists": ("draft", "dialogue", "emotion", "pacing", "tone"),
            },
            "structure": {
                "priority": 4,
                "preferred_mode": "builder",
                "hints": (
                    "outline",
                    "beat sheet",
                    "act",
                    "chapter plan",
                    "scene list",
                    "story structure",
                    "plot out",
                    "arc",
                ),
                "specialists": ("draft", "pacing", "tone"),
            },
            "continuity": {
                "priority": 7,
                "preferred_mode": "debug",
                "hints": (
                    "continuity",
                    "plot hole",
                    "contradiction",
                    "inconsistent",
                    "doesn't track",
                    "timeline",
                    "canon break",
                ),
                "specialists": ("lore", "continuity", "dialogue"),
            },
            "worldbuilding": {
                "priority": 5,
                "preferred_mode": "research",
                "hints": (
                    "canon",
                    "lore",
                    "worldbuilding",
                    "magic system",
                    "faction",
                    "geography",
                    "history",
                ),
                "specialists": ("lore", "continuity", "tone"),
            },
            "dialogue": {
                "priority": 3,
                "preferred_mode": "think",
                "hints": ("dialogue", "voice", "banter", "subtext", "monologue"),
                "specialists": ("dialogue", "emotion", "tone"),
            },
            "emotion": {
                "priority": 3,
                "preferred_mode": "think",
                "hints": (
                    "emotion",
                    "emotional",
                    "internal",
                    "longing",
                    "desire",
                    "fear",
                    "romance",
                    "tension",
                    "chemistry",
                ),
                "specialists": ("emotion", "dialogue", "tone"),
            },
            "pacing": {
                "priority": 3,
                "preferred_mode": "think",
                "hints": (
                    "pacing",
                    "pace",
                    "dragging",
                    "rushed",
                    "rhythm",
                    "slow this down",
                    "speed this up",
                ),
                "specialists": ("pacing", "tone", "dialogue"),
            },
            "combat": {
                "priority": 6,
                "preferred_mode": "debug",
                "hints": ("fight", "battle", "combat", "duel", "attack", "action scene", "sword"),
                "specialists": ("combat", "continuity", "pacing"),
            },
        },
    },
    "coding": {
        "label": "Coding",
        "summary_prefix": "Coding specialist focus detected",
        "default_directive": (
            "This turn is a coding request. Treat the active specialists as silent internal passes. "
            "Return one clean answer, bug analysis, implementation plan, or patch recommendation. "
            "Do not narrate hidden chains of thought or internal role handoffs."
        ),
        "mode_specialists": {
            "fast": ("implementation", "testing"),
            "think": ("architecture", "implementation", "testing"),
            "debug": ("debugging", "testing", "api_surface"),
            "builder": ("architecture", "implementation", "testing"),
            "research": ("architecture", "review", "safety"),
            "operator": ("testing", "api_surface", "safety"),
        },
        "focuses": {
            "debugging": {
                "priority": 8,
                "preferred_mode": "debug",
                "hints": (
                    "debug",
                    "bug",
                    "broken",
                    "error",
                    "exception",
                    "traceback",
                    "stack trace",
                    "failing",
                    "failure",
                    "not working",
                    "crash",
                ),
                "specialists": ("debugging", "testing", "api_surface"),
            },
            "architecture": {
                "priority": 5,
                "preferred_mode": "think",
                "hints": (
                    "architecture",
                    "design",
                    "system design",
                    "how should",
                    "tradeoff",
                    "trade-off",
                    "boundary",
                    "module",
                    "pattern",
                ),
                "specialists": ("architecture", "review", "safety"),
            },
            "implementation": {
                "priority": 4,
                "preferred_mode": "builder",
                "hints": (
                    "implement",
                    "build",
                    "wire",
                    "create",
                    "add",
                    "make",
                    "feature",
                    "endpoint",
                    "component",
                ),
                "specialists": ("implementation", "architecture", "testing"),
            },
            "testing": {
                "priority": 6,
                "preferred_mode": "debug",
                "hints": (
                    "test",
                    "pytest",
                    "unit test",
                    "integration test",
                    "regression",
                    "coverage",
                    "failing test",
                ),
                "specialists": ("testing", "debugging", "review"),
            },
            "review": {
                "priority": 6,
                "preferred_mode": "debug",
                "hints": (
                    "review",
                    "audit",
                    "risk",
                    "regression",
                    "missing tests",
                    "code review",
                ),
                "specialists": ("review", "testing", "safety"),
            },
            "refactor": {
                "priority": 5,
                "preferred_mode": "builder",
                "hints": (
                    "refactor",
                    "cleanup",
                    "simplify",
                    "restructure",
                    "rename",
                    "untangle",
                ),
                "specialists": ("refactor", "architecture", "testing"),
            },
            "integration": {
                "priority": 5,
                "preferred_mode": "operator",
                "hints": (
                    "route",
                    "endpoint",
                    "api",
                    "frontend",
                    "backend",
                    "integration",
                    "request",
                    "response",
                ),
                "specialists": ("api_surface", "implementation", "testing"),
            },
        },
    },
    "training": {
        "label": "Small-LLM Training",
        "summary_prefix": "Training specialist focus detected",
        "default_directive": (
            "This turn is about training or serving a small model. Treat the active specialists as "
            "silent internal passes. Return one grounded answer that respects local compute limits, "
            "evaluation discipline, and the operator's privacy-first setup."
        ),
        "mode_specialists": {
            "fast": ("prompting", "evaluation"),
            "think": ("dataset", "finetune", "evaluation"),
            "debug": ("evaluation", "serving", "safety"),
            "builder": ("dataset", "finetune", "serving"),
            "research": ("evaluation", "compression", "prompting"),
            "operator": ("serving", "evaluation", "safety"),
        },
        "focuses": {
            "dataset": {
                "priority": 6,
                "preferred_mode": "builder",
                "hints": (
                    "dataset",
                    "examples",
                    "jsonl",
                    "messages dataset",
                    "training data",
                    "curate",
                    "label",
                ),
                "specialists": ("dataset", "evaluation", "safety"),
            },
            "prompting": {
                "priority": 4,
                "preferred_mode": "think",
                "hints": (
                    "prompt",
                    "system prompt",
                    "instruction tuning",
                    "messages format",
                    "chat template",
                ),
                "specialists": ("prompting", "dataset", "evaluation"),
            },
            "finetuning": {
                "priority": 8,
                "preferred_mode": "builder",
                "hints": (
                    "fine-tune",
                    "finetune",
                    "lora",
                    "qlora",
                    "adapter",
                    "sft",
                    "trainer",
                    "epochs",
                ),
                "specialists": ("finetune", "dataset", "evaluation"),
            },
            "evaluation": {
                "priority": 7,
                "preferred_mode": "research",
                "hints": (
                    "eval",
                    "evaluation",
                    "benchmark",
                    "judge",
                    "score",
                    "metrics",
                    "accuracy",
                    "compare models",
                ),
                "specialists": ("evaluation", "dataset", "prompting"),
            },
            "compression": {
                "priority": 6,
                "preferred_mode": "research",
                "hints": (
                    "quant",
                    "quantize",
                    "gguf",
                    "4-bit",
                    "4bit",
                    "distill",
                    "compression",
                    "q4_k_m",
                ),
                "specialists": ("compression", "serving", "evaluation"),
            },
            "serving": {
                "priority": 6,
                "preferred_mode": "operator",
                "hints": (
                    "serve",
                    "serving",
                    "inference",
                    "ollama",
                    "llama.cpp",
                    "vram",
                    "latency",
                    "deploy model",
                ),
                "specialists": ("serving", "compression", "safety"),
            },
        },
    },
}


SPECIALIST_TO_DOMAINS = {}
for _domain_id, _domain in SPECIALIST_DOMAINS.items():
    for _specialist_ids in _domain.get("mode_specialists", {}).values():
        for _specialist_id in _specialist_ids:
            SPECIALIST_TO_DOMAINS.setdefault(_specialist_id, set()).add(_domain_id)
    for _focus in _domain.get("focuses", {}).values():
        for _specialist_id in _focus.get("specialists", ()):
            SPECIALIST_TO_DOMAINS.setdefault(_specialist_id, set()).add(_domain_id)


SPECIALIST_PRESETS = {
    "bug_hunt": {
        "label": "Bug Hunt",
        "summary": "Lean into root-cause isolation, test proof, and route-level debugging.",
        "domain": "coding",
        "preferred_mode": "debug",
        "specialists": ("debugging", "testing", "api_surface"),
    },
    "code_review_pack": {
        "label": "Code Review Pack",
        "summary": "Bias toward risk finding, regression checks, and guardrail review.",
        "domain": "coding",
        "preferred_mode": "debug",
        "specialists": ("review", "testing", "safety"),
    },
    "ship_feature": {
        "label": "Ship Feature",
        "summary": "Turn the goal into the smallest working slice with implementation order.",
        "domain": "coding",
        "preferred_mode": "builder",
        "specialists": ("implementation", "architecture", "testing"),
    },
    "small_llm_trainer": {
        "label": "Small-LLM Trainer",
        "summary": "Focus on dataset quality, adapter training, and evaluation discipline.",
        "domain": "training",
        "preferred_mode": "builder",
        "specialists": ("dataset", "finetune", "evaluation"),
    },
    "model_routing_lab": {
        "label": "Model Routing Lab",
        "summary": "Think about local serving limits, compression, and eval tradeoffs together.",
        "domain": "training",
        "preferred_mode": "research",
        "specialists": ("serving", "compression", "evaluation"),
    },
    "scene_rewrite": {
        "label": "Scene Rewrite",
        "summary": "Tighten the scene with stronger draft flow, voice, and emotional charge.",
        "domain": "writing",
        "preferred_mode": "think",
        "specialists": ("draft", "dialogue", "emotion", "tone"),
    },
    "continuity_guard": {
        "label": "Continuity Guard",
        "summary": "Protect canon, timeline, and causal consistency before rewriting.",
        "domain": "writing",
        "preferred_mode": "debug",
        "specialists": ("lore", "continuity", "pacing"),
    },
}


def normalize_response_mode(mode: str | None) -> str:
    """Normalize response modes without depending on the conversation module."""
    cleaned = " ".join(str(mode or "").lower().split()).strip().replace("-", "_")
    return cleaned if cleaned in SUPPORTED_RESPONSE_MODES else "fast"


def normalize_specialist_preset(preset_id: str | None) -> str | None:
    """Normalize one specialist preset id."""
    cleaned = " ".join(str(preset_id or "").lower().split()).strip().replace("-", "_")
    return cleaned if cleaned in SPECIALIST_PRESETS else None


def get_specialist_preset(preset_id: str | None) -> dict | None:
    """Return one specialist preset as a UI-ready object."""
    normalized = normalize_specialist_preset(preset_id)
    if not normalized:
        return None
    preset = SPECIALIST_PRESETS[normalized]
    return _wrap_ul_payload({
        "id": normalized,
        "label": preset["label"],
        "summary": preset["summary"],
        "domain": preset["domain"],
        "preferred_mode": preset.get("preferred_mode"),
        "specialists": [
            {
                "id": specialist_id,
                "label": SPECIALIST_DEFINITIONS[specialist_id]["label"],
                "purpose": SPECIALIST_DEFINITIONS[specialist_id]["purpose"],
                "domain": sorted(SPECIALIST_TO_DOMAINS.get(specialist_id, {preset["domain"]}))[0],
            }
            for specialist_id in preset.get("specialists", ())
            if specialist_id in SPECIALIST_DEFINITIONS
        ],
    })


def list_specialist_catalog() -> list[dict]:
    """Return the specialist catalog grouped by domain for the UI."""
    catalog = []
    for domain_id, domain in SPECIALIST_DOMAINS.items():
        seen = set()
        specialists = []
        for specialist_ids in domain.get("mode_specialists", {}).values():
            for specialist_id in specialist_ids:
                if specialist_id in seen or specialist_id not in SPECIALIST_DEFINITIONS:
                    continue
                seen.add(specialist_id)
                definition = SPECIALIST_DEFINITIONS[specialist_id]
                specialists.append(
                    {
                        "id": specialist_id,
                        "label": definition["label"],
                        "purpose": definition["purpose"],
                        "domain": domain_id,
                    }
                )
        for focus in domain.get("focuses", {}).values():
            for specialist_id in focus.get("specialists", ()):
                if specialist_id in seen or specialist_id not in SPECIALIST_DEFINITIONS:
                    continue
                seen.add(specialist_id)
                definition = SPECIALIST_DEFINITIONS[specialist_id]
                specialists.append(
                    {
                        "id": specialist_id,
                        "label": definition["label"],
                        "purpose": definition["purpose"],
                        "domain": domain_id,
                    }
                )
        catalog.append(
            {
                "id": domain_id,
                "label": domain["label"],
                "specialists": specialists,
            }
        )
    return catalog


def list_specialist_presets() -> list[dict]:
    """Return one-click specialist bundles for the UI."""
    return [
        get_specialist_preset(preset_id)
        for preset_id in SPECIALIST_PRESETS
        if get_specialist_preset(preset_id)
    ]


def normalize_requested_specialists(requested_specialists, limit: int = MAX_REQUESTED_SPECIALISTS) -> list[str]:
    """Normalize requested specialist IDs from API/UI payloads."""
    if not requested_specialists:
        return []

    if isinstance(requested_specialists, str):
        requested_specialists = [requested_specialists]

    normalized = []
    seen = set()
    for specialist_id in requested_specialists:
        cleaned = " ".join(str(specialist_id or "").lower().split()).strip().replace("-", "_")
        if not cleaned or cleaned in seen or cleaned not in SPECIALIST_DEFINITIONS:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
        if len(normalized) >= limit:
            break
    return normalized


def expand_requested_specialists(
    requested_specialists,
    preset_id: str | None = None,
    limit: int = MAX_REQUESTED_SPECIALISTS,
) -> tuple[list[str], dict | None]:
    """Merge a preset pack with manually requested specialist ids."""
    preset = get_specialist_preset(preset_id)
    ordered_ids = []
    seen = set()

    if preset:
        for specialist in preset.get("specialists", []):
            specialist_id = specialist["id"]
            if specialist_id not in seen:
                ordered_ids.append(specialist_id)
                seen.add(specialist_id)

    for specialist_id in normalize_requested_specialists(requested_specialists, limit=limit):
        if specialist_id not in seen:
            ordered_ids.append(specialist_id)
            seen.add(specialist_id)

    return ordered_ids[:limit], preset


def _ordered_specialists(response_mode: str, domain_id: str, focuses: list[str]) -> list[str]:
    """Merge mode-default and focus-specific specialists without duplicates."""
    ordered: list[str] = []
    seen: set[str] = set()
    domain = SPECIALIST_DOMAINS[domain_id]

    for specialist_id in domain.get("mode_specialists", {}).get(response_mode, ()):
        if specialist_id not in seen:
            ordered.append(specialist_id)
            seen.add(specialist_id)

    for focus in focuses:
        for specialist_id in domain["focuses"].get(focus, {}).get("specialists", ()):
            if specialist_id not in seen:
                ordered.append(specialist_id)
                seen.add(specialist_id)

    return ordered


def detect_specialist_profile(text: str, current_mode: str | None = None) -> dict | None:
    """Detect the best logical specialist profile for a request."""
    lower = " ".join(str(text or "").lower().split())
    if not lower:
        return None
    if looks_like_direct_challenge(lower):
        return None

    focus_scores = []
    domain_strengths = {}
    for domain_id, domain in SPECIALIST_DOMAINS.items():
        domain_strength = 0
        for focus_id, focus in domain["focuses"].items():
            matched = [hint for hint in focus.get("hints", ()) if hint in lower]
            if matched:
                focus_scores.append(
                    {
                        "domain": domain_id,
                        "focus": focus_id,
                        "matched_count": len(matched),
                        "priority": focus.get("priority", 0),
                        "matched_hints": matched,
                    }
                )
                domain_strength += len(matched)
        if domain_strength:
            domain_strengths[domain_id] = domain_strength

    if not focus_scores:
        return None

    focus_scores.sort(
        key=lambda item: (
            item["matched_count"],
            item["priority"],
            domain_strengths.get(item["domain"], 0),
            len(item["focus"]),
        ),
        reverse=True,
    )

    primary = focus_scores[0]
    domain_id = primary["domain"]
    domain = SPECIALIST_DOMAINS[domain_id]
    normalized_mode = normalize_response_mode(current_mode)

    focus_scores_same_domain = [
        item for item in focus_scores if item["domain"] == domain_id
    ]
    focuses = [item["focus"] for item in focus_scores_same_domain[:4]]
    focus_config = domain["focuses"][primary["focus"]]

    specialist_ids = _ordered_specialists(normalized_mode, domain_id, focuses)
    specialists = [
        {
            "id": specialist_id,
            "label": SPECIALIST_DEFINITIONS[specialist_id]["label"],
            "purpose": SPECIALIST_DEFINITIONS[specialist_id]["purpose"],
            "domain": domain_id,
        }
        for specialist_id in specialist_ids
        if specialist_id in SPECIALIST_DEFINITIONS
    ]

    focus_label = primary["focus"].replace("_", " ")
    specialist_labels = [specialist["label"] for specialist in specialists[:4]]
    summary = (
        f"{domain['summary_prefix']}: {focus_label}. "
        f"Jarvis is silently using {', '.join(specialist_labels)} specialists inside "
        f"{normalized_mode.title()} mode."
    )

    return _wrap_ul_payload({
        "domain": domain_id,
        "domain_label": domain["label"],
        "focus": primary["focus"],
        "focus_label": focus_label,
        "focuses": focuses,
        "summary": summary,
        "directive": domain["default_directive"],
        "preferred_mode": focus_config.get("preferred_mode"),
        "specialists": specialists,
        "lenses": specialists,
        "matched_hints": primary["matched_hints"][:6],
        "domain_strength": domain_strengths.get(domain_id, primary["matched_count"]),
        "selection_source": "auto",
        "requested_specialists": [],
    })


def merge_requested_specialists(
    auto_profile: dict | None,
    requested_specialists,
    current_mode: str | None = None,
) -> dict | None:
    """Merge manual specialist picks with the auto-detected profile."""
    requested_ids = normalize_requested_specialists(requested_specialists)
    if not requested_ids:
        return auto_profile

    normalized_mode = normalize_response_mode(current_mode)
    manual_specialists = []
    manual_domains = []
    seen = set()
    for specialist_id in requested_ids:
        for domain_id in sorted(SPECIALIST_TO_DOMAINS.get(specialist_id, ())):
            if domain_id not in manual_domains:
                manual_domains.append(domain_id)
        definition = SPECIALIST_DEFINITIONS[specialist_id]
        if specialist_id not in seen:
            manual_specialists.append(
                {
                    "id": specialist_id,
                    "label": definition["label"],
                    "purpose": definition["purpose"],
                    "domain": sorted(SPECIALIST_TO_DOMAINS.get(specialist_id, ()))[0]
                    if SPECIALIST_TO_DOMAINS.get(specialist_id)
                    else "manual",
                    "source": "manual",
                }
            )
            seen.add(specialist_id)

    merged_specialists = list(manual_specialists)
    if auto_profile:
        for specialist in auto_profile.get("specialists", []):
            specialist_id = specialist.get("id")
            if not specialist_id or specialist_id in seen:
                continue
            merged_specialists.append({**specialist, "source": "auto"})
            seen.add(specialist_id)

    if auto_profile:
        selection_source = "hybrid"
        domain_id = auto_profile.get("domain")
        domain_label = auto_profile.get("domain_label")
        focus = auto_profile.get("focus")
        focus_label = auto_profile.get("focus_label")
        focuses = auto_profile.get("focuses", [])
        matched_hints = auto_profile.get("matched_hints", [])
        preferred_mode = auto_profile.get("preferred_mode")
        directive = auto_profile.get("directive")
        summary = (
            f"{auto_profile['summary']} Manual specialists pinned for this turn: "
            f"{', '.join(specialist['label'] for specialist in manual_specialists)}."
        )
    else:
        selection_source = "manual"
        if len(manual_domains) == 1:
            domain_id = manual_domains[0]
            domain_label = SPECIALIST_DOMAINS[domain_id]["label"]
            directive = SPECIALIST_DOMAINS[domain_id]["default_directive"]
        else:
            domain_id = "mixed"
            domain_label = "Mixed"
            directive = (
                "This turn has a manual cross-domain specialist selection. Use the pinned specialists "
                "as silent internal passes and return one clean, grounded answer."
            )
        focus = "manual_selection"
        focus_label = "manual selection"
        focuses = []
        matched_hints = []
        preferred_mode = None
        summary = (
            f"Manual specialist selection active. Jarvis is silently using "
            f"{', '.join(specialist['label'] for specialist in manual_specialists)} inside "
            f"{normalized_mode.title()} mode."
        )

    return _wrap_ul_payload({
        "domain": domain_id,
        "domain_label": domain_label,
        "focus": focus,
        "focus_label": focus_label,
        "focuses": focuses,
        "summary": summary,
        "directive": directive,
        "preferred_mode": preferred_mode,
        "specialists": merged_specialists,
        "lenses": merged_specialists,
        "matched_hints": matched_hints,
        "domain_strength": auto_profile.get("domain_strength", 0) if auto_profile else len(requested_ids),
        "selection_source": selection_source,
        "requested_specialists": requested_ids,
    })


def detect_writing_focus(text: str, current_mode: str | None = None) -> dict | None:
    """Backwards-compatible writing-only alias for older runtime code and tests."""
    profile = detect_specialist_profile(text, current_mode=current_mode)
    if not profile or profile.get("domain") != "writing":
        return None

    return _wrap_ul_payload({
        "focus": profile["focus"],
        "focuses": profile["focuses"],
        "summary": profile["summary"],
        "directive": profile["directive"],
        "lenses": profile["specialists"],
    })


def profile_to_writing_focus(profile: dict | None) -> dict | None:
    """Convert a general specialist profile into the legacy writing-focus shape when possible."""
    if not profile or profile.get("domain") != "writing":
        return None
    return _wrap_ul_payload({
        "focus": profile.get("focus"),
        "focuses": list(profile.get("focuses") or []),
        "summary": profile.get("summary"),
        "directive": profile.get("directive"),
        "lenses": list(profile.get("specialists") or []),
    })

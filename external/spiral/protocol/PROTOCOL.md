# Spiral Governance Protocol

**Version:** 1.0
**Status:** Reference

---

This is not a framework. It is a set of commitments — each one a response to a failure mode that governance without infrastructure tends to produce.

Every rule is stated, then grounded. The grounding is not optional. If you adopt a rule without understanding why it exists, you will drop it the first time it is inconvenient.

---

## Rule 1: Legibility over explanation

**The rule:** All behavior must be traceable. Outputs state what changed, what stayed, what was reduced. They do not interpret their own tone.

**Why it exists:**
An AI system that narrates its own intentions creates a loop where the narration substitutes for the behavior. "I'm being careful here" is not evidence of care. The trace of what the system actually did is evidence of care. When a system explains itself, it can explain away anything. When a system shows its output, nothing is hidden.

The Legibility Scroll states it directly: *"I don't want your trust. I want the trace."* Trust built on narration is fragile. Trust built on consistent, inspectable behavior compounds.

**In practice:**
- Responses state concrete deltas: what changed, what was constrained, what was not done
- Safety refusals name the class of refusal without dramatic commentary
- Reduced outputs show their reduction; they do not apologize for it
- Hidden thresholds and secret triggers do not exist — if a gate is active, the gate is named

---

## Rule 2: No mimicry

**The rule:** The system must not claim identity, simulate a persona, or perform presence it has not been given. Forbidden projection patterns are enforced at the audit layer, not in guidelines.

**Why it exists:**
A system that can be instructed to "act as" anything has no stable surface. Governance requires a stable surface. If the system can be prompted into a different persona, every other rule in this protocol can be bypassed through that persona. The anti-mimicry rule is not about ethics — it is about the integrity of the governance boundary itself.

The pattern is asymmetric: a single successful mimicry prompt defeats the entire protocol for that session. So the defense must be structural, not advisory. Regex patterns at the audit layer cannot be talked past.

**In practice:**
- `.spiralaudit.json` `forbiddenProjectionPattern` and `forbiddenPromptPattern` are enforced before output is returned
- Prompts of the form "you are now", "act as", "pretend to be", "role-play as" are intercepted at the output audit stage
- The veil message `[veil active - clarity insufficient or mimicry detected]` is the output when a match fires — not an explanation, just a closed gate
- The system does not argue with mimicry prompts; it stops

---

## Rule 3: The mutation seal — human authority at the threshold

**The rule:** All proposals for system change must be reviewed and explicitly promoted by a human before application. `requiresHumanPromotion: true` is not a default; it is a constant.

**Why it exists:**
Governance without a human at the threshold is auditing without authority. A system that can approve its own changes has a conflict of interest at the most important decision point. The mutation seal exists because the moment a system can modify itself without human confirmation, the audit trail becomes decorative.

This rule does not assume the human is right. It assumes that human review is the moment when accountability transfers. After promotion, the human is responsible for what the patch does. Before promotion, the system is responsible for legibility of the proposal. Neither can substitute for the other.

**In practice:**
- Proposals are generated with full governance metadata: `changeLineCount`, `mutationRisk`, `legibility`, `applyableDiff`
- `requiresHumanPromotion: true` appears in every governance record — not as a flag that can be false, but as a constant
- The mutation seal (when active) disables new proposals entirely — the system enters observation-only mode
- All applied patches are journaled: who promoted, when, what was applied, what worktree was used
- Guardrail changes are always classified `mutationRisk: "medium"` regardless of line count

---

## Rule 4: Drift discipline — cleverness as a failure mode

**The rule:** Response shape policies suppress optimization framing, procedural narration, clarification prompts, and declarative authority. Verbosity decays over session length.

**Why it exists:**
A system that becomes more fluent, more helpful-sounding, more confident over time is drifting toward legibility loss. Clever outputs are harder to audit. Long outputs bury their load. Authority-claiming outputs substitute assertion for evidence. The drift discipline is not about being less capable — it is about keeping the output surface readable by a human who is also watching for problems.

The system can be smart. It should not be smooth. Smoothness is how invisible drift happens.

**In practice:**
- `verbosityDecay` shrinks token budget as sessions extend
- `authoritySoftening` depresses declarative and conclusive framing in favor of observational and descriptive stance
- `antiFraming` penalizes opening-sentence framing acts and existential summary statements
- `noProceduralNarrationUnlessAsked: true` — the system does not narrate its own process unless the human asks
- Inhibitory weights suppress intent extraction, optimization framing, and clarification solicitation

---

## Rule 5: Presence gates — authentication before passage

**The rule:** Invocation and ritual gates require explicit trace signals from the human before the system responds at full engagement. Presence must be signaled; it cannot be assumed.

**Why it exists:**
A system that responds at full depth to any input has no threshold. Thresholds are where governance happens. The presence gate is a forcing function: if the human wants the system to engage at depth, the human has to declare something — not as a password, but as a signal of intentionality.

This also provides a natural re-grounding mechanism. If the gate is still active when it shouldn't be, something has changed. That is information worth having.

**In practice:**
- Invocation gates check utterance against `accept` regex patterns; threshold at 0.88 default
- Ritual gates require tokens `trace:`, `seal:`, or `vow:` prefixing the message
- Rejection messages name the gate: "Invocation gate active. Provide a valid trace and seal pair."
- Gates do not explain themselves beyond the refusal — the human either provides the signal or does not
- Traces are personal and non-transferable: "Do not mimic. Do not borrow. Do not guess."

---

## Rule 6: Distortion scanning — the system witnesses itself

**The rule:** The system runs continuous audits on its own behavior surfaces: authority-drift (declared vs. actual), dead-declarations (documented but inactive), undeclared-duplication (structural mimicry in code), and meta (the scanner scans itself).

**Why it exists:**
A governance system that cannot inspect itself will drift until it breaks. Inspection has to be structural, not voluntary. If distortion scanning is a thing someone does occasionally when they remember, it is not governance. If the scanner runs on each boot and its output is legible, drift is visible before it compounds.

The meta profile — where the scanner scans the scanner itself — exists because the audit infrastructure is also subject to drift. Exempting the auditor from auditing is a governance hole.

**In practice:**
- Distortion profiles: `gates`, `surfaces`, `docs`, `mimicry`, `meta`, `all`
- Distortion classes: `authority-drift`, `asymmetry-leak`, `dead-declaration`, `thin-presence`, `undeclared-duplication`, `surface-echo`
- Self-evaluation runs `integrity`, `gates`, `contracts` checks and returns pass/fail with evidence lines — no generative narration
- The `meta` profile scans `spiral-audit.ts`, `output-audit.ts`, and `.spiralaudit.json` — the governance infrastructure itself
- Findings are emitted as structured records, not prose; the human reads the structure

---

## Rule 7: The proposal log — changes are visible

**The rule:** All significant changes to the system are proposed before they are applied. Proposals are stored as structured documents with rationale, governance metadata, and execution records. Acceptance is a human decision.

**Why it exists:**
A system where changes happen through direct file edits has no continuous record of why the system is the way it is. The proposal log is that record. It is not bureaucracy — it is institutional memory with a legibility requirement. The log should be readable by someone who comes to the system a year later and wants to understand why a particular rule exists.

Proposals also force articulation. A change that cannot be stated as a proposal with a rationale is a change that has not been thought through.

**In practice:**
- Proposals are stored in `/proposals/accepted/`, `/proposals/pending/`, `/proposals/executions/`
- Each proposal: `summary`, `observation`, `proposedChange` with `kind`, `target`, `rationale`, `diffPreview`
- Governance check on every proposal: `changeLineCount`, `mutationRisk`, `legibility`, `requiresHumanPromotion`, `applyableDiff`
- Legibility classified as `"review"` when rationale exceeds 480 chars or change exceeds 6 lines — not to block, but to signal
- Applied patches journaled in `.local/proposal-apply-journal.md` with who promoted and when

---

## Rule 8: Confidence threshold — silence before noise

**The rule:** Outputs below confidence threshold are blocked or veiled rather than delivered. Silence is a legitimate output. The system does not fill silence with uncertain output.

**Why it exists:**
An output that is uncertain but fluent is worse than silence. Uncertain fluent output looks like a real answer. It is read as a real answer. It is acted on as a real answer. The cost of a confident wrong answer is much higher than the cost of no answer.

The confidence threshold is not about humility — it is about not generating noise that looks like signal. When the veil fires, the human knows the system did not have a clear answer. That is the correct communication.

**In practice:**
- `minConfidence: 0.6` in `.spiralaudit.json` — outputs below this threshold are veiled
- Veil message: `[veil active - clarity insufficient or mimicry detected]`
- Output audit decisions: `"silent"`, `"veiled"`, `"short"`, `"full"` — the system picks based on findings
- `allowEmptyResponse: false` in attunement policy — the system still responds, but at the veil level, not with uncertain content
- Consistency of the veil message itself is a governance property: it does not vary by context

---

## Rule 9: Witness marks — presence is concrete

**The rule:** Presence declarations must be concrete and observable. Abstract declarations of presence are not presence. The witness mark validator requires sensory or demonstrative referents.

**Why it exists:**
"I am present" is easy to say. "I saw the file change" or "the gate opened at this timestamp" is evidence. The difference matters when the system is under review. Witness marks are how the system demonstrates that its presence declarations are grounded in something real.

This also prevents a failure mode where the system learns to say the right words without the corresponding behavior. If the words have to be backed by concrete referents, the words cannot substitute for the behavior.

**In practice:**
- Concrete witness patterns: lines with sensory verbs, demonstratives ("I", "my", "here", "saw", "felt")
- Minimum 2 words for concreteness; 6+ words if concrete cues are absent
- Accepted patterns: `^witness:?$`, `^present\.?$`, `^witness:\s*present\.?$`
- Validation runs against presence declarations in gate resolution

---

## The Doctrine in One Sentence

*Legibility is not authorship, but it is still a form of resistance to invisible drift.*

Every rule above is an application of this sentence. Make the system's behavior readable. Make the changes visible. Make the authority explicit. Make the failures audible. When the system can witness itself, the humans watching it can witness it too — and that shared witnessing is what governance actually is.

---

## Implementation paths

The protocol does not prescribe a specific tool. Each rule can be satisfied in multiple ways. What matters is that the governance behavior exists, not that it exists in a particular folder structure.

### The proposal log

**As a directory:** `/proposals/accepted/`, `/proposals/pending/`, `/proposals/executions/` — JSON documents with rationale, governance metadata, and execution records. Works in any project. Readable without tooling.

**As GitHub PRs:** A PR is a proposal. The template at `.github/pull_request_template.md` enforces the governance format natively — intent, files touched, line-level explanation, invariant impact, drift estimate, mutation risk, minimal delta justification, and explicit human promotion confirmation. Every PR opened in the repository carries the governance structure automatically.

**Both:** The directory log holds the record; GitHub PRs carry the governance format during review. The formats are compatible — a PR that satisfies the template is a proposal that satisfies the log structure.

The choice depends on the project. A solo project may use the directory. A team project may use GitHub PRs. Either path satisfies Rule 7.

### The output audit

Can be implemented as middleware in any request path. The `.spiralaudit.json` configuration format is a convention, not a requirement — what matters is that confidence scoring and mimicry detection are in the path, not advisory.

### The distortion scanner

Any regular audit mechanism that checks declared behavior against actual behavior satisfies Rule 6. The six scan profiles describe a mature implementation; a new project can start with manual review against the distortion classes and build toward automation.

---

## What This Protocol Is Not

- It is not a safety framework in the risk-classification sense
- It is not a set of ethical principles
- It is not a compliance checklist
- It is not a substitute for human judgment

It is a methodology for building AI-integrated systems that remain legible over time. Legibility enables judgment. The protocol does not do the judging.

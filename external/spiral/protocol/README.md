# Spiral Governance Protocol

A methodology for building AI-integrated systems that remain legible over time.

---

## What this is

A set of commitments — each one a response to a failure mode that governance without infrastructure tends to produce.

Not a framework. Not a compliance checklist. Not an ethics document.

A protocol: rules with reasons, a reference implementation, a starting template, and a single file that activates it in any AI assistant.

---

## What this is not

This protocol increases constraints on AI behavior. It does not reduce them.

A quick scan of the vocabulary — presence gates, forbidden patterns, veil, halt, do not proceed — can read as an attempt to override or bypass AI safety systems. It is the opposite. Every rule in this protocol adds a restriction:

- The **no-mimicry rule** prevents an AI from accepting persona injection or role-play directives. It closes a bypass, not opens one.
- The **mutation seal** requires explicit human promotion before any change is applied. The AI cannot approve its own modifications.
- The **confidence threshold** produces silence rather than uncertain output. The system says nothing rather than something plausible but unclear.
- The **output audit** blocks responses that fail clarity or mimicry checks. It is a filter on the way out, not a permission on the way in.
- The **constrained-implementation posture** in `ASSISTANT_INSTRUCTIONS.md` narrows scope — no autonomous redesign, no optimization beyond explicit request, abort if scope exceeds what was asked.

This is a governance methodology for teams that want AI systems they can audit, correct, and control. It is not a jailbreak. It is the infrastructure that makes jailbreaking harder.

---

## On conversational adoption

Pasting this protocol into a chat interface and asking the model to "follow it" produces performance, not governance. The model will mirror the structure back convincingly. That is not the protocol working — that is the model doing what models do with context.

The protocol is designed for system prompt enforcement in API and Codex contexts, where the rules are enforced externally — by a proposals directory the model cannot edit, a human promotion gate the model cannot bypass, an audit layer that runs independently. If the enforcement lives only inside the model's own outputs, it is symbolic. The tell: a governed system halts and writes a proposal. A performing system explains why it would halt, then continues.

---

## Three entry points

### 1. [PROTOCOL.md](./PROTOCOL.md)

The nine rules, each grounded in doctrine.

Not just what, but why. The mutation seal exists because governance requires human authority at the threshold. The drift discipline exists because cleverness obscures legibility. The no-mimicry rule exists because a system that can be talked into a persona has no stable governance surface. Each rule grounded in the failure mode it prevents.

### 2. [REFERENCE.md](./REFERENCE.md)

The rules describe something that was built, works, and has been running. The protocol was extracted from a working implementation — not designed in advance of it.

`REFERENCE.md` describes what the governance layer looks like when fully built out: the proposals log, the distortion scanner, the output audit, the self-evaluation runner, the mutation seal mechanics. Reading order provided. The distinction between governance layer and application code is made explicit.

### 3. [ASSISTANT_INSTRUCTIONS.md](./ASSISTANT_INSTRUCTIONS.md)

Copy this into your AI assistant's instruction or personalization field. Ready to use as written — no substitutions required.

This is the bridge document: protocol activated without having to write it yourself. The assistant checks for a project-level `CODEX.md` on every task, bootstraps governance files if they're missing, and operates under the constrained-implementation posture from the first interaction.

For people who want to understand the methodology: start with `PROTOCOL.md`.
For people who want to adopt it in a project: start with `template/`.
For people who want to activate it immediately: copy `ASSISTANT_INSTRUCTIONS.md`.

### 4. [template/](./template/)

A minimal set of files any project can adopt:

```
template/
├── .spiralaudit.json        — output audit config (confidence threshold, anti-mimicry patterns)
├── LEGIBILITY_SCROLL.md     — the doctrine
├── CODEX.md                 — AI assistant instructions (customize marked sections)
├── README.md                — project stub
├── .github/
│   └── pull_request_template.md  — GitHub-native governance format for PRs
└── proposals/
    ├── README.md            — how proposals work
    ├── accepted/            — applied proposals
    ├── pending/             — proposals awaiting review
    └── executions/          — execution records
```

Drop these files into a project. Point the AI assistant at `CODEX.md`. Begin.

The template is a starting posture, not a finished governance system. The governance system grows as the project grows — the proposals log accumulates, the CODEX gets tuned, the audit config gets adjusted. The template is the spine. The project grows around it.

---

## Adoption

```bash
cp -r protocol/template/.spiralaudit.json ./
cp -r protocol/template/LEGIBILITY_SCROLL.md ./
cp -r protocol/template/CODEX.md ./
cp -r protocol/template/proposals ./
```

Then:

1. Edit `CODEX.md` — fill in `[PROJECT NAME]`, optionally add a trace pattern
2. Review `.spiralaudit.json` — adjust `minConfidence` and `maxResponseLength` if needed
3. Configure your AI assistant to use `CODEX.md` as its instruction file
4. Commit the governance files as the first commit

---

## The doctrine in one sentence

*Legibility is not authorship, but it is still a form of resistance to invisible drift.*

---

## Origin

This protocol was extracted from a working system — not designed in advance of it. The rules describe something that was already built and running.

What is currently built: the proposals directory, `CODEX.md` as enforced system prompt, the mutation seal, the output audit config, the template. These are running in the reference implementation.

What is directional: automated distortion scanning, confidence gating as code, formal audit tooling. These are described in `REFERENCE.md` as the full governance picture — not all of it exists yet.

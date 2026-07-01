# Contributors

This file records people and agents who contributed material work to Project Infinity / AAIS.
Claims here are descriptive, not proof of release readiness — see `REPO_PROOF_LAW.md`.

## Maintainers

- **Jon Halstead** — project authority, constitutional governance, primary human operator
  - GitHub: [@warheart1984-ctrl](https://github.com/warheart1984-ctrl)

## Contributors

### Human

- **Jon Halstead** — architecture, governance lawbook, operator direction, review authority

### AI collaborators

Per [`HUMAN_AI_CO_COLLABORATION_CHARTER.md`](HUMAN_AI_CO_COLLABORATION_CHARTER.md), AI agents may be credited for
implementation work when a human maintainer accepts the contribution.

- **Cursor Agent (Auto)** — AI implementation collaborator (Cursor IDE)
  - **Scope:** UL/CISIV phased rollout (Phases 1–5), chat-turn and forge/repo governance modules, CISIV
    consolidation, UL smoke fixtures, proof/trust bundles, operational README
  - **Key artifacts:**
    - `src/chat_turn_governance.py`
    - `src/forge_repo_governance.py`
    - `docs/proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md`
    - `docs/trust_bundles/UL_CISIV_PHASES_1_5_TRUST_BUNDLE.md`
  - **Evidence:** commits `7b4e806`, `b086b1e` (2026-05-29); human-directed session with Jon Halstead
  - **Claim posture:** implementation **proven** on single-machine pytest/drift/smoke; cross-machine matrix **asserted pending**

---

To add a contributor: open a PR that updates this file with name, scope, and linked proof artifacts.

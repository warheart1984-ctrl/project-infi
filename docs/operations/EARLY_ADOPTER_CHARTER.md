# Early Adopter Charter — Project Infinity 1

**Knowledge is freely given. Trust is earned.**

Project Infinity 1 is a governed cognition runtime — not a black box. Early adopters receive the same contracts, gates, proof bundles, and operator runbooks we use internally. We do not ask you to trust marketing copy. We ask you to **verify**, **operate**, and **tell us what breaks**.

---

## What we give freely

| Category | Where to find it |
|----------|------------------|
| Install and first run | [AAIS Operator Guide](../operators/AAIS_OPERATOR_GUIDE.md) |
| Full production runbook | [AAIS Production Operator Runbook](./AAIS_PRODUCTION_OPERATOR_RUNBOOK.md) |
| Pilot stack (Platform + UGR + AAIS) | [INFINITY_PILOT_EARLY_ADOPTER.md](./INFINITY_PILOT_EARLY_ADOPTER.md) |
| Constitutional law and seams | [README](../../README.md) governance section |
| GA evidence and sign-off | [INFINITY_PILOT_GA_SIGNOFF.md](../audit/INFINITY_PILOT_GA_SIGNOFF.md) |
| Operator review protocol | [OPERATOR_GA_REVIEW_PROTOCOL.md](./OPERATOR_GA_REVIEW_PROTOCOL.md) |
| Reproduction commands | `make production-hardening-gate`, `make stack-pilot-gate`, `make infinity1-flagship-verification` |

Nothing in this list is paywalled or hidden behind a sales call. If a document is missing or stale, open an issue — that is how trust compounds.

---

## What we ask in return

1. **Run the gates** on your environment before you call it production.
2. **Record your sign-off** using the GA review protocol when you admit GA posture locally.
3. **Report seams** — places where observe, actuate, or admit paths disagree — with reproduction steps.
4. **Respect MA-13** — Platform autopilot is policy-bound ops routing; Jarvis remains executive for cognition. Do not bypass workflow approvals for governed execution.
5. **Keep keys local** — API keys and tenant data stay on your infrastructure unless you explicitly configure cloud providers.

Trust is not assumed. It is earned when your operators can reproduce our proof, run rollback, and read the ledger without calling us.

---

## Posture labels (use these honestly)

| Label | Meaning |
|-------|---------|
| **Exploring** | Mock or laptop preset; learning surfaces |
| **Pilot** | Docker compose stack + `stack-pilot-gate` green |
| **GA-ready (claimed)** | All production gates green + human sign-off per protocol |
| **Production (your org)** | Your SLOs, backups, on-call, and incident runbook — we supply the substrate, you own the ops contract |

Repository baseline is **GA-ready** as of 2026-06-06. Your deployment is production only when **your** operators sign off.

---

## Philosophy

- **Inspectable** — UL substrate, ledger, and operator dashboard expose state; secrets stay in env, not in chat.
- **Governed** — OTEM Level 10 and workflow approvals gate execution; chat proposes, workflows execute.
- **Incremental** — Start mock, add keys, add Platform membrane, add K8s when you need tenant isolation proof.
- **Honest debt** — Open items live in the baseline checklist and debt register; we close them in public commits.

Welcome aboard. Verify first. Operate second. Teach us third.

# UGR-AMENDMENT-S-SURVIVABILITY-v0

**Amendment type:** SURVIVABILITY REMEDIATION AMENDMENT  
**Constitutional linkage:** Article S, Article S-1, Article S-2, Article R

## Telic statement

A system is legitimate only if it can survive its creators. This amendment restores that legitimacy.

## Automatic open triggers

| Trigger | Condition |
|---------|-----------|
| `survivability_below_0.60` | System survivability score &lt; 0.60 |
| `steward_independence_below_0.60` | Steward independence score &lt; 0.60 |
| `founder_dependency_above_0.40` | Founder dependency index &gt; 0.40 |
| `fitness_failure` | Reconstructability fitness below completion threshold or failed surfaces |
| `cold_start_failure` | Cold-start steward test fails |
| `active_rf_threats_red_zone` | Active R-F threat surfaces ≥ 4 |

## Required structural remediation

- [ ] Knowledge Externalization
- [ ] Authority Transfer
- [ ] Steward Capability Replication
- [ ] Operational Automation
- [ ] Continuity Reinforcement

## Success criteria (amendment closes only when all met)

| Criterion | Target |
|-----------|--------|
| Survivability score | ≥ 0.70 |
| Steward independence score | ≥ 0.70 |
| Founder dependency index | ≤ 0.30 |
| Fitness score | ≥ 0.70 |
| Cold-start steward test | Pass |
| Red-zone R-F threats | 0 |

## Governance effect while open

- Constitutional governance gate blocks missions when Article S-1 is in breach
- High-impact missions require fitness assessment
- Succession requires Article S-2 checklist pass and fitness receipt
- Amendment remains open until survivability is restored to green band

## Runtime binding

- Template ID: `UGR-AMENDMENT-S-SURVIVABILITY-v0`
- Record type: `SurvivabilityAmendmentRecord`
- State key: `survivability_amendment__pending`
- Renderer: `constitutional.runtime.survivability_amendment.render_survivability_amendment_template`
- API: `GET /api/survivability/amendment-template`

# Opportunity runtime

## StateObjects

- **OpportunityState** — `opportunity_id`, `description`, `value`, `probability`, `decay_curve`, `deadline`, `status`
- **DependencyState** — `dependency_id`, `type`, `status`, `blocks_opportunities`
- **OpportunityPortfolioState** — `portfolio_id`, `opportunity_ids`, `risk_profile`

## Receipts

| Type | Kinds |
|------|-------|
| `OpportunityReceiptV2` | Discover, Qualify, Advance, Win, Lose, Abandon |
| `DependencyReceiptV2` | Add, Resolve, Fail |
| `OpportunityRemediationReceiptV2` | Closure |

## Invariants

- **OR-1:** No high-value opportunity expires without explicit Lose or Abandon receipt.
- **OR-2:** Dependencies tracked for all high-value opportunities.
- **OR-3:** Portfolio concentration risk visible.

## Remediation

**Trigger:** approaching deadlines, decaying probability, unresolved dependencies.

**Path:** Re-prioritize → Allocate time → Resolve dependencies → Decide explicitly.

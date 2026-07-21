# Sovereign Router X Pricing and Unit Economics Worksheet

**Release family:** CRK-1 companion specification  
**Purpose:** Define pricing tiers and a unit-economics worksheet for a constitutional orchestration product built on top of routed reasoning.

---

## 1. Pricing philosophy

Sovereign Router X should be priced as a governed orchestration product, not as raw token resale.

Pricing should reflect:

- platform subscription
- AI usage
- governance and assurance
- knowledge services
- enterprise services
- professional services

This makes the business durable even if inference costs continue to fall.

## 2. Revenue layers

| Layer | What it covers | Example charges |
|------|----------------|-----------------|
| Platform subscription | Governance, identity, workspace, administration | Monthly seat or tenant fee |
| AI usage | Requests, tokens, workflows | Per request, per token, per workflow step |
| Governance and assurance | Conformance, evidence, policy, audit | Compliance tier, assessment fee, evidence retention fee |
| Knowledge services | Knowledge graph, replay, provenance, storage | Storage, provenance, replay access, knowledge operations |
| Enterprise services | Private deployment, implementation profiles, support | Dedicated tenancy, private routing, enterprise support |
| Professional services | Consulting, training, implementation | Fixed-fee projects or hourly advisory |

## 3. Recommended pricing shape

| Tier | Intended customer | What it includes |
|------|-------------------|------------------|
| Individual | Solo builder or researcher | Lightweight subscription, low AI usage cap, basic governance and replay |
| Professional | Power user or specialist | Higher usage caps, workspace features, assurance add-ons |
| Team | Small production team | Shared billing, collaboration, evidence retention, workflow automation |
| Enterprise | Regulated or high-volume deployment | Dedicated tenancy, private deployment, advanced assurance, support |
| Public Sector | Government or public-interest deployment | Compliance-heavy governance, procurement-friendly packaging, audit support |

Suggested pricing components:

- base platform fee
- routed request usage fee
- replay storage fee
- premium profile fee
- governance and assurance fee
- enterprise support fee
- professional services fee

## 4. Chargeable units

| Unit | How it is measured | Why it matters |
|------|--------------------|----------------|
| Routed request | One packet passed through Sovereign Router X | Core orchestration event |
| Inference pass | One model invocation | Primary variable cost |
| Validated reply | One reply accepted by schema and policy | Replay-safe output |
| Replay record | One durable continuity record | Storage and audit cost |
| Evidence receipt | One recorded proof object | Governance overhead |
| Cluster route event | One routing decision involving cluster behavior | Higher operational complexity |
| Governance review | One policy/conformance review cycle | Assurance and compliance cost |
| Knowledge graph update | One durable knowledge mutation | Institutional memory cost |
| Professional service hour | One advisory or implementation hour | High-touch enablement cost |

## 5. Unit-economics worksheet

Use the following worksheet for each customer segment or workload class.

| Input | Symbol | Example value |
|-------|--------|---------------|
| Monthly customers | `C` | 100 |
| Average routed requests per customer per month | `R` | 250 |
| Average governance reviews per customer | `G` | 4 |
| Average knowledge updates per customer | `K` | 12 |
| Average professional service hours per customer | `H` | 1 |
| Average inference cost per routed request | `I` | $0.02 |
| Average validation and orchestration cost per request | `O` | $0.01 |
| Average replay and storage cost per request | `S` | $0.005 |
| Average governance and assurance cost per review | `A` | $6.00 |
| Average knowledge service cost per update | `N` | $0.15 |
| Average professional service cost per hour | `T` | $75.00 |
| Average support and observability cost per customer | `P` | $8.00 |
| Base platform subscription price per customer | `B` | $49.00 |
| Usage fee per routed request | `U` | $0.09 |
| Governance and assurance fee per review | `Q` | $10.00 |
| Knowledge services fee per update | `L` | $0.50 |
| Professional services revenue per hour | `M` | $125.00 |

### Formula

- `Monthly revenue = C * (B + R * U + G * Q + K * L + H * M)`
- `Monthly direct cost = C * (P + R * (I + O + S) + G * A + K * N + H * T)`
- `Gross margin = Monthly revenue - Monthly direct cost`
- `Gross margin percent = Gross margin / Monthly revenue`

### Example calculation

Using the example values above:

- `Monthly revenue = 100 * (49 + 250 * 0.09 + 4 * 10 + 12 * 0.50 + 1 * 125) = $20,810`
- `Monthly direct cost = 100 * (8 + 250 * 0.035 + 4 * 6 + 12 * 0.15 + 1 * 75) = $13,955`
- `Gross margin = $6,855`
- `Gross margin percent = 32.9%`

## 6. Segment model

| Segment | Typical buying motive | Pricing emphasis |
|---------|-----------------------|------------------|
| Individual | Personal productivity, learning, side projects | Low entry price, simple usage |
| Professional | Higher leverage and repeat workflows | Value-based subscription plus usage |
| Team | Shared work and governance | Seat-based subscription and workflow pricing |
| Enterprise | Scale, risk management, and controls | Platform plus assurance plus support |
| Public Sector | Policy compliance and stewardship | Procurement-friendly packaging, auditability, private deployment |

## 7. Scenario matrix

The matrix below compares the four primary commercial shapes side by side for each segment.

| Segment | Subscription-led | Usage-led | Assurance-led | Enterprise bundle | Target margin band |
|---------|------------------|-----------|---------------|-------------------|--------------------|
| Individual | Simple monthly plan with modest usage allowance | Small base fee plus metered requests | Optional governance add-on | Not the default fit | 55-70% |
| Professional | Tiered workspace plan with elevated usage caps | Lower base fee with metered bundles | Workflow assurance add-on | Consultant-grade premium package | 60-75% |
| Team | Seat-based team plan with shared admin | Seat minimum plus metered activity | Evidence and audit bundle | Team bundle with support and private routing | 62-78% |
| Enterprise | Annual commitment with platform access | Commitment plus overage | Conformance, policy, and audit bundle | Private deployment plus support and services | 70-85% |
| Public Sector | Contracted platform fee | Metered usage with spend controls | Compliance and audit package | Procurement-friendly all-in package | 65-80% |

### Packaging guidance

- Use subscription-led packaging where predictability and low-friction adoption matter most.
- Use usage-led packaging when workload volatility is the dominant buying constraint.
- Use assurance-led packaging when evidence, audit, or policy review is the value center.
- Use enterprise bundle packaging when procurement wants one accountable commercial wrapper.

## 8. Pricing controls

To protect margin and service quality, the product should enforce:

- request quotas
- burst limits
- replay storage caps
- tenant-specific routing policy
- model fallback policy
- overage pricing
- customer-segment-specific service limits
- minimum margin thresholds by segment

## 9. Margin guardrails

Recommended guardrails:

- keep direct inference cost below 35 percent of revenue for standard tiers
- keep storage and orchestration below 10 percent of revenue
- preserve a support buffer for enterprise escalation
- require higher minimums for custom compliance profiles
- require service-heavy tiers to cover professional services cost separately
- keep governance and assurance priced as a durable value layer, not a loss leader

## 10. Pricing strategies to compare

These strategies should be evaluated per segment:

- subscription-led
- usage-led
- assurance-led
- services-led
- hybrid platform-plus-usage
- enterprise bundle

## 11. Growth levers

The product can expand revenue without changing the constitutional core by adding:

- multi-node cluster routing
- failover automation
- audit exports
- compliance profiles
- premium research memory
- private deployment support
- advanced replay analytics

## 12. Pricing review checklist

Before changing pricing:

- confirm request and storage costs
- confirm model mix
- confirm segment mix
- measure replay retention pressure
- measure governance and assurance workload
- estimate support load
- check tenant compliance requirements
- validate margin under peak routing
- compare revenue layers by segment

## 13. Machine-readable pricing spec

The machine-readable pricing spec lives in [SOVEREIGN_ROUTER_X_PRICING.spec.json](./SOVEREIGN_ROUTER_X_PRICING.spec.json).

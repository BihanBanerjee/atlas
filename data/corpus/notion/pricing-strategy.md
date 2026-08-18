---
id: notion-pricing-strategy
source: notion
type: page
tier: supporting
title: "Pricing Strategy"
parent: "Company / Commercial"
created: 2026-05-14
updated: 2026-07-08
properties:
  owner: Marcus Oyelaran
  status: Active
---

# Pricing Strategy

## Current structure

| Tier | Price | Includes |
|---|---|---|
| Starter | $49/user/month | Load testing, 3 environments |
| Team | $99/user/month | Adds Watch, unlimited environments, CI integration |
| Enterprise | Custom, from $60k/yr | Adds SSO (when available), audit export, SLA, dedicated support |

Enterprise pricing is negotiated per account. Current enterprise ACVs range from $28,000 to $84,000.

## The June experiment

We restructured the pricing page mid-June to lead with annual pricing rather than monthly, on the theory that it would improve commitment quality.

Trial-to-paid conversion dropped from 6.3% to 5.4% within two weeks. Reverted on 29 June, conversion recovered to 6.6% by mid-July.

Lesson recorded in the Q2 retrospective: the experiment ran without an agreed success metric or a stop condition, which is why it took a fortnight to call.

## Open questions

**Should tracing be a separate module or included in Team?** Currently planned as included at GA, which leaves revenue on the table but simplifies the story. Revisit after GA lands.

**Enterprise floor.** $60k is where we set it in 2025 and the market has moved. Marcus's view is that $75k is defensible now given what enterprise accounts consume in support.

**Seat-based pricing at scale.** Northwind has gone from 40 to 58 seats without a commercial conversation, because their contract covers up to 40 with overage billed quarterly. Overage billing is confusing to customers and we should consider tiered bands instead.

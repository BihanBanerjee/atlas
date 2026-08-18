---
id: notion-roadmap-q2-2026
source: notion
type: page
tier: signal
title: "Product Roadmap — Q2 2026"
parent: "Product / Roadmap"
created: 2026-03-18
updated: 2026-06-28
properties:
  quarter: Q2 2026
  period: 2026-04-01..2026-06-30
  owner: Dana Whitfield
  status: Complete
facts:
  - Q2 2026 shipped onboarding v1, tracing private beta, pricing experiment
  - Tracing GA was scheduled into Q3, not Q2
---

# Product Roadmap — Q2 2026

**Owner:** Dana Whitfield · **Status:** Complete · **Period:** April – June 2026

## Committed

| Item | Target | Status | Notes |
|---|---|---|---|
| First-run onboarding simplification | April | Shipped | Cut three steps from setup. Trial-to-paid moved 4.1% → 6.3%. |
| Distributed tracing — private beta | April | Shipped | Opened to 8 accounts by end of month. |
| Results diffing in CI | April | Shipped | Carried over from Q1, three accounts using it in pipelines. |
| Infrastructure cost reduction | May | Shipped | Our own load-test workloads cut roughly 45%. |
| Pricing page experiment | June | Reverted | Conversion dropped 6.3% → 5.4%. Reverted 29 June. |

## Deferred out of Q2

| Item | Moved to | Reason |
|---|---|---|
| Distributed tracing GA | Q3 | Beta feedback surfaced two blocking issues in the sampling path. |
| Billing revamp | Q3 | Sequenced behind tracing. |

## Retrospective

Onboarding was the highest-leverage thing we did all quarter and it was also the smallest. Worth remembering when we're weighing large bets next quarter.

The pricing experiment was run without a clear success metric agreed up front, which is why it took two weeks to decide it had failed. Not repeating that.

Enterprise requirements came up in two lost or stalled deals this quarter — one on identity, one on data residency. Neither is scheduled anywhere yet. Flagging for Q3 planning.

---
id: notion-roadmap-q1-2026
source: notion
type: page
tier: supporting
title: "Product Roadmap — Q1 2026"
parent: "Product / Roadmap"
created: 2025-12-16
updated: 2026-03-31
properties:
  quarter: Q1 2026
  period: 2026-01-01..2026-03-31
  owner: Dana Whitfield
  status: Complete
---

# Product Roadmap — Q1 2026

**Owner:** Dana Whitfield · **Status:** Complete

## Committed

| Item | Target | Status |
|---|---|---|
| Results diffing in CI | February | Shipped |
| Scheduled test runs | February | Shipped |
| Three integrations — Slack, Jira, PagerDuty | March | Shipped |
| Distributed tracing — design and prototype | March | Shipped |

## Not committed, discussed

| Item | Outcome |
|---|---|
| Federated identity | Raised, not scoped. No customer had made it a condition at this point. |
| EU data residency | Raised in one deal. Not scoped. |
| Mobile client | Explored, dropped. |

## Retrospective

Results diffing was the quarter's win and is now the single most-cited reason
customers give for renewing.

The tracing prototype took longer than planned because we underestimated the
sampling problem, which then went on to be the blocking issue in beta as well.
A pattern worth noticing.

Two enterprise-shaped requests surfaced this quarter — identity and residency —
and we scoped neither. At the time that was the right call. Recording it here
so the decision is traceable if it turns out not to have been.

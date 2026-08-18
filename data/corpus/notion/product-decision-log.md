---
id: notion-product-decision-log
source: notion
type: page
tier: supporting
title: "Product Decision Log"
parent: "Product / Decisions"
created: 2026-01-15
updated: 2026-08-01
properties:
  owner: Dana Whitfield
  status: Active
---

# Product Decision Log

Decisions, when they were made, and why. Reversals are recorded rather than
edited over.

| Date | Decision | Reasoning |
|---|---|---|
| 15 Jan 2026 | Results diffing before tracing | Diffing is two weeks, tracing is a quarter. Ship the thing customers can feel first. |
| 3 Feb 2026 | No mobile client | Explored for a week. Nobody asked for it. Dropped. |
| 20 Mar 2026 | Tracing beta limited to eight accounts | Enough signal, small enough to support manually. |
| 14 Apr 2026 | Onboarding rebuild ahead of roadmap items | Conversion flat for six months. Two days of work. Obvious in hindsight. |
| 6 May 2026 | Engineering compensation bands to 60th percentile | Two offers declined on comp, six weeks lost per attempt. |
| 2 Jun 2026 | Pricing page annual-first | Hypothesis: annual improves commitment quality. |
| 29 Jun 2026 | Pricing page reverted | Conversion 6.3% → 5.4%. Hypothesis wrong. Ran without a stop condition, which is the actual lesson. |
| 24 Jun 2026 | Identity deferred to Q4 | Q3 capacity consumed by tracing GA and billing. Identity is 5–7 weeks with an auth migration that cannot run alongside a GA. |
| 14 Jul 2026 | Audit log export scoped to twelve months retention | Matches the stated customer requirement. Twenty-four available for enterprise. |
| 1 Aug 2026 | Tracing included in Team tier at GA | Simpler story, gives every Team customer a reason to re-engage. Revenue left on the table, accepted. |

## Reversals

**Pricing page annual-first** — decided 2 June, reversed 29 June. Twenty-seven
days. The reversal was correct; the absence of a pre-agreed stop condition is
what made it take four weeks instead of one.

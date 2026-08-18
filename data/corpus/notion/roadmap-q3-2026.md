---
id: notion-roadmap-q3-2026
source: notion
type: page
tier: signal
load_bearing: true
title: "Product Roadmap — Q3 2026"
parent: "Product / Roadmap"
created: 2026-06-24
updated: 2026-07-02
properties:
  quarter: Q3 2026
  period: 2026-07-01..2026-09-30
  owner: Dana Whitfield
  status: In progress
facts:
  - Q3 2026 contains tracing GA, onboarding v2, billing revamp, audit log export
  - Audit log export targets end of August 2026
  - SAML SSO is NOT scheduled in Q3 — deferred to Q4
  - Page last updated 2026-07-02, three weeks after SSO was promised to Northwind for 15 September
---

# Product Roadmap — Q3 2026

**Owner:** Dana Whitfield · **Status:** In progress · **Period:** July – September 2026

## Committed

| Item | Target | Status | Owner |
|---|---|---|---|
| Distributed tracing — GA | Mid-August | On track | Dana |
| Self-serve onboarding v2 | July | Shipped | Dana |
| Billing revamp | September | Not started | Dana |
| Audit log export (12-month retention) | End of August | In progress | Dana |

Audit log export is scoped against Northwind's compliance requirement. Twelve months retention, customer-initiated export, CSV and JSON.

## Deferred to Q4

| Item | Reason |
|---|---|
| SAML SSO / enterprise identity | Tracing GA and the billing work consume the quarter. Identity is a multi-week build with an auth-path migration we don't want to run alongside a GA. Scheduled Q4 — see Q4 roadmap. |
| Data residency (EU) | Dependent on infrastructure work not yet scoped. |
| Role-based access control | Sequenced behind SSO. |

## Capacity notes

Six engineers this quarter. Tracing GA takes roughly three of them through mid-August, and the billing revamp is a two-engineer effort for most of September. That leaves one engineer of genuine slack across the quarter, which is why the deferred list is as long as it is.

We are still without a Head of Engineering. Until that role is filled, Dana is the single point of sequencing for everything on this page.

## Open risks

- Tracing GA slipping would push billing into Q4 and compress everything behind it.
- Enterprise identity being out of this quarter is a known commercial exposure. Sales has been told the Q4 timeline.

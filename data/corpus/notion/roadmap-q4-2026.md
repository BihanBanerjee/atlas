---
id: notion-roadmap-q4-2026
source: notion
type: page
tier: signal
load_bearing: true
title: "Product Roadmap — Q4 2026"
parent: "Product / Roadmap"
created: 2026-07-02
updated: 2026-07-29
properties:
  quarter: Q4 2026
  period: 2026-10-01..2026-12-31
  owner: Dana Whitfield
  status: Planned
facts:
  - SAML SSO scheduled October–November 2026
  - This is 6-8 weeks after the 15 September date promised to Northwind
  - SSO ships after the Northwind renewal date of 30 September
---

# Product Roadmap — Q4 2026

**Owner:** Dana Whitfield · **Status:** Planned · **Period:** October – December 2026

Draft. Sequencing assumes a Head of Engineering is in seat by early October.

## Planned

| Item | Window | Notes |
|---|---|---|
| **SAML SSO — enterprise identity** | **October – November** | Okta and Azure AD. Includes auth-path migration for existing accounts. Estimated 5–7 weeks. |
| Role-based access control | November | Depends on SSO landing first. |
| SOC 2 Type II — evidence collection | October – December | Auditor selected, observation window starts October. |
| Data residency (EU) | December | Scoping only in Q4, build in Q1 2027. |

## SAML SSO — scope

The largest item of the quarter and the one carrying the most commercial weight.

- SAML 2.0, Okta first, Azure AD in the same build
- SCIM provisioning is explicitly out of scope for this pass
- Auth-path migration for existing accounts is the risk — every current user is on individual credentials and there is no clean cutover without a maintenance window
- Estimate 5–7 weeks with two engineers. October start puts completion in mid-to-late November.

## Notes

Enterprise identity has now been deferred out of two consecutive quarters. It was raised in the Q2 retrospective as an unscheduled blocker, deferred again in Q3 planning on capacity grounds, and is now the anchor item for Q4.

Sales has been asked to set expectations accordingly on any deal where identity is a gating requirement.

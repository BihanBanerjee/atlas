---
id: notion-engineering-oncall
source: notion
type: page
tier: supporting
title: "On-call Rotation and Escalation"
parent: "Engineering / Operations"
created: 2026-01-28
updated: 2026-06-30
properties:
  owner: Dana Whitfield
  status: Active
---

# On-call Rotation and Escalation

## Current rotation

Six engineers, one week each, Monday to Monday. Dana is the permanent secondary, which is a known problem and one of the reasons the Head of Engineering role exists.

## Severity definitions

| Level | Definition | Response |
|---|---|---|
| Sev-1 | Service unavailable or data at risk | 15 min ack, all hands |
| Sev-2 | Major feature degraded, workaround exists | 1 hour ack, business hours |
| Sev-3 | Minor degradation or single-customer issue | Next business day |

Customer-facing commitment is four hours for Sev-1 under the standard MSA. Internal target is fifteen minutes because the two are not the same thing.

## Escalation

Primary → secondary after 15 minutes unacknowledged → Dana → Ravi if customer communication is required.

For accounts above $50k ACV, Marcus is notified on any Sev-1 regardless of duration.

## Incident history 2026

| Date | Severity | Duration | Cause |
|---|---|---|---|
| 14 Feb | Sev-1 | 47 min | Load generator fleet exhausted region capacity |
| 3 Apr | Sev-2 | 3h 20m | Results ingestion lag under peak concurrency |
| 22 May | Sev-2 | 1h 05m | Dashboard timeouts, query regression |
| 11 Jun | Sev-3 | — | Single customer, webhook delivery failures |

One Sev-1 in the last twelve months, disclosed to affected customers at the time.

## Known gaps

No formal follow-the-sun coverage. Everyone is in one timezone, which means overnight Sev-1s depend on someone waking up.

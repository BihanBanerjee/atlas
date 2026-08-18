---
id: notion-noise-runbook-results-ingestion-lag
source: notion
type: page
tier: noise
title: "Runbook — Results ingestion lag"
parent: "Engineering / Runbooks"
created: 2026-04-07
updated: 2026-04-07
---

# Runbook — Results ingestion lag

**Trigger:** ingestion queue depth growing

## Steps

1. Acknowledge the alert in the on-call channel.
2. Check the service dashboard for the affected component.
3. Confirm scope — one customer or all customers.
4. If scope is all customers, escalate to secondary immediately.
5. Apply the mitigation below.
6. Record start and end times for the incident log.

## Mitigation

Follow the standard procedure for this component. If the standard procedure
does not resolve within fifteen minutes, escalate rather than continuing to
investigate alone.

## After

Raise a follow-up ticket. If customer-facing, notify the account owner.

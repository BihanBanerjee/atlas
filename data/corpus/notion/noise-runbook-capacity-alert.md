---
id: notion-noise-runbook-capacity-alert
source: notion
type: page
tier: noise
title: "Runbook — Capacity alert"
parent: "Engineering / Runbooks"
created: 2026-02-23
updated: 2026-02-23
---

# Runbook — Capacity alert

**Trigger:** generator fleet capacity below threshold

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

---
id: notion-spec-audit-log-export
source: notion
type: page
tier: supporting
title: "Spec — Audit Log Export"
parent: "Product / Specs"
created: 2026-06-22
updated: 2026-07-14
properties:
  status: In progress — Q3
  owner: Dana Whitfield
---

# Spec — Audit Log Export

**Status:** in progress, targeting end of August 2026.

## Problem

We log access events and retain them for ninety days internally. Customers
cannot see them, export them, or configure retention.

Northwind's security review flagged this as a remediation item. Their
requirement is twelve months of retention with customer-initiated export in a
machine-readable format.

## Scope

**Events captured**

| Event | Detail |
|---|---|
| Authentication | sign-in, sign-out, failed attempt |
| Account management | user added, removed, role changed |
| Test lifecycle | run created, started, cancelled, deleted |
| Configuration | settings changed, integrations added or removed |
| Data access | results viewed, exported |

**Retention.** Twelve months default. Configurable to twenty-four for
enterprise accounts.

**Export.** Admin-initiated, CSV and JSON, asynchronous with a download link on
completion. Date range filter, event type filter.

**Out of scope for this pass:** streaming to a customer SIEM, real-time
webhooks on audit events.

## Implementation notes

Events already exist in the application log. The work is a durable audit store
separate from application logging, because application logs rotate and audit
records cannot.

Writing to ClickHouse alongside results data. Audit volume is small relative to
results, so no capacity concern.

## Estimate

Three weeks, one engineer. Sprint plan places completion in the final week of
August.

## Acceptance

An account admin can export twelve months of audit events for their account in
under five minutes, without contacting support.

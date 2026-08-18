---
id: notion-spec-tracing-ga
source: notion
type: page
tier: supporting
title: "Spec — Distributed Tracing GA"
parent: "Product / Specs"
created: 2026-04-08
updated: 2026-07-30
properties:
  status: In progress — GA 14 August
  owner: Dana Whitfield
---

# Spec — Distributed Tracing GA

**Status:** in progress. GA 14 August 2026.

## What changes at GA

Beta has run with eight accounts since April. GA means general availability to
all Team-tier customers at no additional cost, with support commitments and
documented limits.

## Blocking issues from beta — both resolved

**1. Sampling under burst load.** Head-based sampling at a fixed rate meant a
sudden traffic spike produced either an unusable sample or an unaffordable
volume. Resolved with adaptive sampling — rate adjusts to hold a target span
volume per minute.

**2. Trace-to-run correlation.** Traces produced during a load run were not
reliably attributed to that run when the run spanned a deploy. Resolved by
stamping run identity at generation rather than inferring it at ingest.

## Limits at GA

| | |
|---|---|
| Span retention | 14 days |
| Max spans per trace | 5,000 |
| Ingest rate | 50,000 spans/sec per account |
| Instrumentation | OpenTelemetry |

## Pricing

Included in Team tier. No separate SKU.

Decision recorded 1 August: including it simplifies the story and gives every
existing Team customer a reason to re-engage in launch month. The revenue left
on the table is accepted.

## Launch sequence

| Date | Action |
|---|---|
| 11 Aug | Beta accounts moved to GA build |
| 12 Aug | Documentation and changelog live |
| 14 Aug | General availability, in-app announcement |

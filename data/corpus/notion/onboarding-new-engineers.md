---
id: notion-onboarding-new-engineers
source: notion
type: page
tier: supporting
title: "Onboarding — New Engineers"
parent: "Engineering / Handbook"
created: 2025-11-12
updated: 2026-05-19
properties:
  owner: Dana Whitfield
  status: Active
---

# Onboarding — New Engineers

## Week one

**Day 1** — accounts, hardware, repository access. Pair with your onboarding buddy for the afternoon.

**Day 2** — local environment. If this takes more than half a day, the setup docs are wrong and fixing them is your first contribution.

**Day 3–5** — ship something small to production. Anything. The point is proving the path from your machine to production works and that you've done it once before it matters.

## Week two

Read the architecture overview, then have the architecture conversation with Dana. In that order — the document is deliberately incomplete and the conversation fills the gaps.

Shadow an on-call shift. You won't be primary for at least two months.

## Architecture, briefly

Three services. The API, the scheduler, and the load generator fleet.

The fleet is the interesting one. It scales to several thousand concurrent generators and the coordination problem — making distributed generators produce a coherent load profile — is most of the engineering difficulty in the product.

Postgres for everything transactional. ClickHouse for results. The results volume is the reason for the split.

## Conventions

- Trunk-based, short-lived branches, no long-running feature branches
- Every PR gets a performance test run automatically. We use our own product, and when it breaks we find out first.
- Deploys are continuous. If you're afraid to deploy on a Friday, say so in the retro rather than waiting until Monday.

## Who to ask

| Topic | Person |
|---|---|
| Architecture, anything ambiguous | Dana |
| Customer context, why a feature exists | Marcus |
| Anything commercial or company-level | Ravi |

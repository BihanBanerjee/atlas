---
id: notion-spec-saml-sso
source: notion
type: page
tier: supporting
title: "Spec — SAML SSO"
parent: "Product / Specs"
created: 2026-05-29
updated: 2026-06-16
properties:
  status: Draft — not scheduled
  owner: Dana Whitfield
---

# Spec — SAML SSO

> **Status: draft. Not scheduled.** Written to size the work, not to commit to it.
> See the quarterly roadmaps for when this is actually planned.

## Problem

Every user authenticates directly against Tensile with an individual account.
For customers consolidating identity onto an IdP, this means we are the vendor
that gets written up in their access audit.

Raised by Northwind in the May security review, by Calder in the context of
seat expansion, and by two prospects in Q2.

## Scope

**In scope**
- SAML 2.0 service-provider-initiated flow
- Okta and Azure AD as verified IdPs
- Just-in-time provisioning on first sign-in
- Domain-based account routing
- Enforcement setting — allow, prefer, or require SSO per account

**Out of scope**
- SCIM provisioning
- OIDC
- Directory sync of groups or roles
- Multi-IdP per account

## The hard part

Every existing user has a password. Migration is the risk, not the SAML
implementation itself.

Options considered:

1. **Hard cutover.** Account admin enables SSO, all users forced through IdP on
   next sign-in. Simple, but locks out anyone not in the IdP.
2. **Dual-path with grace period.** Both methods valid for a configurable
   window, then password auth disabled. More code, far fewer support tickets.
3. **Opt-in per user.** Users choose. Never converges — some accounts would run
   both indefinitely.

**Recommendation: option 2**, 30-day default grace period.

## Estimate

| Component | Effort |
|---|---|
| SAML integration and IdP verification | 1.5 weeks |
| JIT provisioning and domain routing | 1 week |
| Migration path and grace period | 2 weeks |
| Admin UI and enforcement settings | 1 week |
| Testing against both IdPs | 1 week |
| **Total** | **5–7 weeks, two engineers** |

## Dependencies

None technically. The constraint is entirely capacity — this cannot run
alongside a GA release, because both need the same two engineers and the auth
migration needs undivided attention.

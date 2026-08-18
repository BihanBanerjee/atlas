---
id: gmail-prospect-vellum
source: gmail
type: thread
tier: supporting
subject: "Evaluating Tensile"
thread_id: t-0785
date: 2026-06-30
participants:
  - Isabel Ferreira <i.ferreira@vellumworks.com>
  - Marcus Oyelaran <marcus@tensile.dev>
---

## Message 1 — 26 June 2026, 11:15

**From:** Isabel Ferreira <i.ferreira@vellumworks.com>
**To:** hello@tensile.dev
**Subject:** Evaluating Tensile

Hello,

We're comparing Tensile against Surge Labs. 45 engineers, mostly Go and Kubernetes.

The deciding factor for us is CI integration — we want performance gates on every PR, not a separate testing exercise.

Can we get a trial with support?

Isabel Ferreira
Vellum Works

---

## Message 2 — 30 June 2026, 09:00

**From:** Marcus Oyelaran <marcus@tensile.dev>
**To:** Isabel Ferreira <i.ferreira@vellumworks.com>
**Subject:** Re: Evaluating Tensile

Isabel,

Trial set up, thirty days, no card required. I've enabled the CI integration on your account so you can wire it up immediately.

On the comparison: CI gating is where we're strongest and where Surge is weakest — their integration is a plugin that reports results, ours blocks the merge on a regression against your last known good. That difference is the whole reason we exist.

Where they're stronger: they have a SOC 2 and we don't until 2027. If that's a gate for you, better to know now.

Marcus

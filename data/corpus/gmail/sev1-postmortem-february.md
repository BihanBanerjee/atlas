---
id: gmail-sev1-postmortem-february
source: gmail
type: email
tier: supporting
subject: "Postmortem — 14 Feb capacity incident"
thread_id: t-0601
date: 2026-02-18
participants:
  - Dana Whitfield <dana@tensile.dev>
  - team@tensile.dev
---

**From:** Dana Whitfield <dana@tensile.dev>
**To:** team@tensile.dev
**Date:** 18 February 2026, 10:30
**Subject:** Postmortem — 14 Feb capacity incident

Team,

Postmortem for Friday's Sev-1. Blameless as always — the interesting question is what the system allowed, not who did what.

**What happened.** Between 13:42 and 14:29 on 14 February, the load generator fleet was unable to schedule new runs. Forty-seven minutes. Roughly sixty percent of active customers were affected.

**Cause.** Three large customers started substantial runs within four minutes of each other. Our fleet autoscaler requests capacity in the region, and eu-west-2 had no spare instances of the type we request. We had no fallback instance type configured.

**Why it wasn't caught.** Our capacity alerting fires on utilisation above 85%. We went from 71% to unschedulable in under two minutes, because the three runs requested their full fleet allocation up front rather than ramping.

**What we've changed.**

1. Fallback instance types configured, three alternatives in priority order
2. Alerting now fires on rate of change, not just absolute utilisation
3. Large runs ramp their fleet request over ninety seconds rather than requesting it whole
4. Reserved a baseline capacity floor so we're never starting from zero

**What we haven't fixed.** We are single-region. A regional capacity event still takes us out entirely. That's a larger piece of work and it isn't scheduled.

Customers were notified the same day. No data exposure at any point.

Dana

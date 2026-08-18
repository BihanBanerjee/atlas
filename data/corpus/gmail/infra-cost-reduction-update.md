---
id: gmail-infra-cost-reduction-update
source: gmail
type: email
tier: supporting
subject: "Infra costs — where we landed"
thread_id: t-0748
date: 2026-06-05
participants:
  - Dana Whitfield <dana@tensile.dev>
  - Ravi Menon <ravi@tensile.dev>
---

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Ravi Menon <ravi@tensile.dev>
**Date:** 5 June 2026, 11:20
**Subject:** Infra costs — where we landed

Ravi,

Closing this out. The reduction work is done.

**Before:** our own load-generation and CI workloads were running at roughly $31,000 per month, about 22% of revenue.

**After:** $17,000 per month, roughly 18% of revenue at current ARR.

Where it came from:

- Spot instances for our internal test fleet — we were paying on-demand for workloads that can be interrupted without consequence. That's about half the saving.
- Result retention. We were keeping full-fidelity results for every internal run indefinitely. Now seven days full, then downsampled.
- Killed two staging environments nobody had used since January.

Gross margin should show 80% for June, up from 78%.

The one I didn't do: moving ClickHouse to reserved capacity would save another $2,000 a month but locks us in for a year, and I'd rather keep the flexibility until we know what the enterprise workload profile looks like.

Dana

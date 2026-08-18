---
id: gmail-northwind-support-dashboard
source: gmail
type: thread
tier: supporting
subject: "Dashboards timing out"
thread_id: t-0725
date: 2026-05-22
participants:
  - Linda Marsh <linda.marsh@northwindlogistics.com>
  - Dana Whitfield <dana@tensile.dev>
---

## Message 1 — 22 May 2026, 09:12

**From:** Linda Marsh <linda.marsh@northwindlogistics.com>
**To:** support@tensile.dev
**Subject:** Dashboards timing out

Results dashboards have been timing out since about 08:30 this morning. Three of my team seeing it, all on the main results view. Test runs themselves seem fine.

Linda

---

## Message 2 — 22 May 2026, 10:20

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Subject:** Re: Dashboards timing out

Linda,

Confirmed and resolved as of 10:17. A query regression went out in yesterday's deploy that hit accounts with large result histories hardest, which is why you saw it and most didn't.

Total impact 1 hour 5 minutes. Logging it as a Sev-2 and you'll get the postmortem within three working days.

The regression is reverted and there's now a test covering the query path at your data volume specifically.

Dana

---

## Message 3 — 22 May 2026, 11:04

**From:** Linda Marsh <linda.marsh@northwindlogistics.com>
**To:** Dana Whitfield <dana@tensile.dev>
**Subject:** Re: Dashboards timing out

Appreciated, that was quick. No need for the postmortem unless you want to send it.

Linda

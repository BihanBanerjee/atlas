---
id: gmail-calder-support-escalation
source: gmail
type: thread
tier: supporting
subject: "Runs queuing"
thread_id: t-0714
date: 2026-05-06
participants:
  - Priyanka Rao <p.rao@caldersystems.com>
  - Dana Whitfield <dana@tensile.dev>
---

## Message 1 — 6 May 2026, 08:20

**From:** Priyanka Rao <p.rao@caldersystems.com>
**To:** support@tensile.dev
**Subject:** Runs queuing

Runs have been sitting in the queue for eight to ten minutes before starting since yesterday. Normally near-instant. Nothing changed our side.

Priyanka

---

## Message 2 — 6 May 2026, 09:45

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Priyanka Rao <p.rao@caldersystems.com>
**Subject:** Re: Runs queuing

Priyanka,

Not an incident — it's your own usage. Your team went from about 40 runs a day to 190 after the CI integration went in last week, and our per-account concurrency limit is 12 simultaneous runs. You're hitting the ceiling and queuing behind yourselves.

Raised your limit to 30. Queue should clear within the hour.

Worth flagging that this is the kind of growth that changes what tier makes sense for you, but that's Marcus's conversation and not one for a support ticket.

Dana

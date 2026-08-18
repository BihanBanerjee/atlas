---
id: gmail-meridian-feature-request
source: gmail
type: thread
tier: supporting
subject: "Scheduled test windows"
thread_id: t-0801
date: 2026-07-08
participants:
  - Sam Okafor <s.okafor@meridiangrid.com>
  - Dana Whitfield <dana@tensile.dev>
---

## Message 1 — 7 July 2026, 13:20

**From:** Sam Okafor <s.okafor@meridiangrid.com>
**To:** Dana Whitfield <dana@tensile.dev>
**Subject:** Scheduled test windows

Dana,

Marcus said to raise this with you directly.

We want heavy load runs constrained to a window — say 22:00 to 06:00. Right now anyone can trigger a full-scale run at any time and twice this quarter someone has done it during business hours against an environment shared with our staging traffic.

We can solve it with process. I'd rather solve it with the product.

Sam

---

## Message 2 — 8 July 2026, 09:40

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Sam Okafor <s.okafor@meridiangrid.com>
**Subject:** Re: Scheduled test windows

Sam,

Reasonable request and you're the third customer to ask.

Honest position: it's on the backlog and it isn't scheduled. Q3 is fully committed and Q4 has a large piece of identity work in it. Realistically this is Q1 next year unless something changes.

What I can offer now: run-level tags plus a webhook, so you could reject out-of-window runs with a check on your side. Not the product solving it, but it's this week rather than next year.

Dana

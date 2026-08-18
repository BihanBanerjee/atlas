---
id: gmail-northwind-support-webhooks
source: gmail
type: thread
tier: supporting
subject: "Webhook deliveries failing"
thread_id: t-0771
date: 2026-06-12
participants:
  - Linda Marsh <linda.marsh@northwindlogistics.com>
  - Dana Whitfield <dana@tensile.dev>
---

## Message 1 — 11 June 2026, 16:40

**From:** Linda Marsh <linda.marsh@northwindlogistics.com>
**To:** support@tensile.dev
**Subject:** Webhook deliveries failing

Our Slack notifications stopped yesterday afternoon. Nothing changed on our side that I'm aware of. Low urgency but it's how the team finds out about failed runs.

Linda

---

## Message 2 — 12 June 2026, 09:30

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Subject:** Re: Webhook deliveries failing

Linda,

Found it. Your endpoint started returning 429s on Tuesday and our retry logic gives up after five attempts, then disables the webhook silently. The silent part is our bug — you should have been told.

Re-enabled. I've raised a fix so that a disabled webhook sends an email rather than just stopping.

Sev-3, single customer. No postmortem but it's in the log.

Dana

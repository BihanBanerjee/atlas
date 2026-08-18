---
id: gmail-ravelin-support-escalation
source: gmail
type: thread
tier: supporting
subject: "Results missing from yesterday"
thread_id: t-0679
date: 2026-04-09
participants:
  - Nour Haddad <n.haddad@ravelinhealth.com>
  - Dana Whitfield <dana@tensile.dev>
---

## Message 1 — 8 April 2026, 17:10

**From:** Nour Haddad <n.haddad@ravelinhealth.com>
**To:** support@tensile.dev
**Subject:** Results missing from yesterday

We ran a full suite yesterday afternoon and about a third of the results aren't showing. The runs completed — we can see them in the run list — but the detailed results are empty.

Nour

---

## Message 2 — 9 April 2026, 10:30

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Nour Haddad <n.haddad@ravelinhealth.com>
**Subject:** Re: Results missing from yesterday

Nour,

Found and fixed. Results ingestion backed up for about three hours yesterday afternoon under peak concurrency and a portion of writes were dropped rather than retried. Your data is not recoverable for those runs, which I'm sorry about.

Logged as a Sev-2, 3 hours 20 minutes. Roughly a dozen accounts affected.

The fix is a proper retry queue rather than the fire-and-forget path we had. Shipping this week.

Postmortem to follow within three working days.

Dana

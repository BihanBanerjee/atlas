---
id: gmail-partner-integration-inquiry
source: gmail
type: thread
tier: supporting
subject: "Integration partnership"
thread_id: t-0768
date: 2026-06-16
participants:
  - Gita Ramachandran <gita@pipelinehq.com>
  - Dana Whitfield <dana@tensile.dev>
---

## Message 1 — 15 June 2026, 10:45

**From:** Gita Ramachandran <gita@pipelinehq.com>
**To:** partnerships@tensile.dev
**Subject:** Integration partnership

Hello,

I lead partnerships at PipelineHQ. We're a CI platform with around 4,000 engineering teams, and performance testing is the most requested integration we don't have.

We'd want a native Tensile step in our pipeline builder — configure a test, see results inline, block on regression. We'd build and maintain it if you'll give us API access and some engineering time for questions.

We list partners in our marketplace, which drives meaningful volume.

Gita Ramachandran
PipelineHQ

---

## Message 2 — 16 June 2026, 14:20

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Gita Ramachandran <gita@pipelinehq.com>
**Subject:** Re: Integration partnership

Gita,

Interested, and the shape you're proposing — you build, we support — is the right one for us. We're fourteen people and we can't staff an integration.

Our public API covers everything you'd need for configure, trigger, and fetch results. Blocking on regression would use the diffing endpoint, which is documented but hasn't been used externally, so expect some rough edges and tell me about them.

I can offer a standing thirty minutes a week for questions for as long as the build takes.

One thing to flag early: we don't currently support service accounts, so your integration would authenticate as a user. That's workable but not ideal, and it changes in Q4 when we do the identity work.

Dana

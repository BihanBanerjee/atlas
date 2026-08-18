---
id: gmail-northwind-security-review
source: gmail
type: thread
tier: signal
subject: "Security questionnaire — Tensile"
thread_id: t-0729
date: 2026-05-27
date_range: 2026-05-19..2026-05-27
participants:
  - Karin Holt <karin.holt@northwindlogistics.com>
  - Dana Whitfield <dana@tensile.dev>
  - Linda Marsh <linda.marsh@northwindlogistics.com>
facts:
  - Northwind security review conducted May 2026, ahead of the June requirements thread
  - Tensile has no SOC 2 report; observation window starts October 2026
  - Review flagged SSO and audit log export as gaps
  - Karin Holt is Information Security at Northwind Logistics
---

## Message 1 — 19 May 2026, 14:33

**From:** Karin Holt <karin.holt@northwindlogistics.com>
**To:** Dana Whitfield <dana@tensile.dev>
**Cc:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Subject:** Security questionnaire — Tensile

Dana,

Attached is our standard vendor security questionnaire. We run this annually against every vendor with access to production telemetry, and Tensile is in scope this year because usage has grown past our internal threshold.

Sections 1 through 6 are the usual — encryption, key management, incident response, subprocessors. Section 7 covers access control and section 9 covers audit and logging. Those two tend to be where smaller vendors have gaps, so start there if you're triaging.

We'd like it back within two weeks if that's workable.

Karin Holt
Information Security, Northwind Logistics

---

## Message 2 — 26 May 2026, 18:02

**From:** Dana Whitfield <dana@tensile.dev>
**To:** Karin Holt <karin.holt@northwindlogistics.com>
**Cc:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Subject:** Re: Security questionnaire — Tensile

Karin,

Completed questionnaire attached. I've answered everything honestly, including where we fall short, because I'd rather you find the gaps from me than from the document.

The parts you'll care about:

**Encryption and key management** — AES-256 at rest, TLS 1.3 in transit, keys in AWS KMS with annual rotation. No concerns here.

**Incident response** — documented process, 24-hour customer notification commitment. We've had one Sev-1 in the last twelve months, disclosed at the time.

**Section 7, access control** — this is a gap. We support individual accounts with enforced MFA, but we do not support SAML or any external identity provider today. Every user authenticates directly against us.

**Section 9, audit and logging** — partial. We log access events and retain them for ninety days internally, but there is no customer-facing export and no configurable retention.

**SOC 2** — we don't have a report. We've selected an auditor and the Type II observation window starts in October, which puts a report roughly mid-2027.

I'd rather set expectations correctly than have this come back as a surprise in six months.

Dana Whitfield
CTO, Tensile

---

## Message 3 — 27 May 2026, 09:50

**From:** Karin Holt <karin.holt@northwindlogistics.com>
**To:** Dana Whitfield <dana@tensile.dev>
**Cc:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Subject:** Re: Security questionnaire — Tensile

Dana,

Appreciated — that's a more useful response than most.

Assessment: no blocking findings for continued use this term. Two items go on our remediation register.

1. **Federated identity (SAML).** Our tenant-wide Okta consolidation completes at the end of Q3. Vendors without SAML get written up in the quarterly access audit from that point.
2. **Audit log export.** Twelve months retention, customer-initiated, machine-readable.

The absent SOC 2 is noted but not blocking given the compensating controls you've described.

Linda will pick up timelines with your commercial team — this is a requirements conversation now, not a security one.

Karin

---
id: drive-northwind-security-questionnaire
source: gdrive
type: document
tier: supporting
title: "Northwind Vendor Security Questionnaire — Completed"
file_type: pdf
folder: "Legal / Contracts / Northwind"
created: 2026-05-26
updated: 2026-05-26
owner: Dana Whitfield
---

# Vendor Security Questionnaire — Tensile, Inc.

**Completed by:** Dana Whitfield, CTO
**Returned:** 26 May 2026
**Requested by:** Karin Holt, Information Security, Northwind Logistics

---

## Section 1 — Encryption

**1.1 Data at rest?** AES-256. AWS EBS and S3 with SSE-KMS.

**1.2 Data in transit?** TLS 1.3 minimum. TLS 1.2 rejected at the load balancer.

**1.3 Key management?** AWS KMS, customer-managed keys not currently offered. Annual rotation.

---

## Section 2 — Infrastructure

**2.1 Hosting?** AWS, eu-west-2 (London).

**2.2 Multi-tenancy?** Logical isolation with row-level tenant scoping. No physical isolation offered.

**2.3 Backups?** Daily, thirty-five day retention, quarterly restore testing.

---

## Section 3 — Incident response

**3.1 Documented process?** Yes.

**3.2 Notification commitment?** 24 hours from becoming aware of a personal data breach.

**3.3 Incidents in last 12 months?** One Sev-1, 14 February 2026, 47 minutes, capacity exhaustion in the load generator fleet. No data exposure. Affected customers notified same day.

---

## Section 4 — Subprocessors

AWS (hosting), Stripe (payments), Postmark (transactional email), Sentry (error tracking). Published list maintained, thirty days notice of additions.

---

## Section 5 — Personnel

**5.1 Background checks?** Yes, for all employees with production access.

**5.2 Security training?** Annual, mandatory.

**5.3 Offboarding?** Access revoked within 4 hours of departure.

---

## Section 6 — Business continuity

RTO 4 hours, RPO 1 hour. Tested quarterly.

---

## Section 7 — Access control ⚠️

**7.1 Federated identity (SAML/OIDC)?** **Not supported.** All users authenticate directly against Tensile.

**7.2 MFA?** Enforced on all accounts. TOTP and WebAuthn.

**7.3 Role-based access control?** Partial. Two roles — admin and member. Granular permissions not available.

**7.4 SCIM provisioning?** Not supported.

---

## Section 8 — Vulnerability management

**8.1 Penetration testing?** Annual, third party. Last conducted November 2025, no critical or high findings outstanding.

**8.2 Dependency scanning?** Automated, on every build.

---

## Section 9 — Audit and logging ⚠️

**9.1 Access events logged?** Yes.

**9.2 Retention?** Ninety days, internal only.

**9.3 Customer-accessible export?** **Not available.**

**9.4 Configurable retention?** Not available.

---

## Section 10 — Certifications

**10.1 SOC 2?** No report. Type II observation window begins October 2026. Report expected mid-2027.

**10.2 ISO 27001?** No.

**10.3 GDPR?** Yes — DPA available, data hosted in EU, sub-processor list published.

---

*Answers provided in good faith. Sections 7 and 9 identify known gaps; we would rather disclose them than have them discovered.*

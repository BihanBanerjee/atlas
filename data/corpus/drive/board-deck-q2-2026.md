---
id: drive-board-deck-q2-2026
source: gdrive
type: document
tier: signal
load_bearing: true
title: "Tensile — Q2 2026 Board Meeting"
file_type: google_doc
folder: "Board / 2026"
created: 2026-06-14
updated: 2026-06-17
owner: Ravi Menon
facts:
  - Q2 board meeting held 18 June 2026
  - May actuals presented — ARR $860,000, cash $1.90M, 52 customers, 13 people
  - Series A formally approved at $12M target
  - $190,000 of ARR identified as at risk from identity and compliance gaps
  - Northwind at $84,000 is the largest single exposure
---

# Tensile — Q2 2026 Board Meeting

**18 June 2026** · Prepared by Ravi Menon
Attending: Ravi Menon, Dana Whitfield, Nadia Osei

---

## 1. Headline

| | May 2026 | Change vs Feb 2026 |
|---|---|---|
| ARR | $860,000 | +39% |
| MRR | $71,700 | |
| Customers | 52 | +14 |
| Net revenue retention | 118% | +4pts |
| Net burn | $175,000 / mo | +$20k |
| Cash | $1.90M | |
| Runway | 11 months | −4 months |
| Headcount | 13 | +2 |

---

## 2. Financial detail

Burn up $20,000 per month since February, driven by the two hires and the compensation band adjustment made in May. Infrastructure cost reduction delivered as planned — our own workloads are down roughly 45% and gross margin recovered to 80%.

Runway is 11 months. This is the number that sets the timeline for everything else in this document.

---

## 3. Series A — approval requested

**Requesting formal approval to raise $12M.**

At planned burn, $12M funds approximately 24 months. That period covers:

| Use | Amount | Rationale |
|---|---|---|
| Engineering — 5 hires incl. Head of Engineering | ~$4.4M | Enterprise build and delivery capacity |
| Go-to-market — 3 hires | ~$2.6M | Enterprise motion requires people who have run one |
| Enterprise readiness — SOC 2, identity, residency | ~$1.2M | Currently a revenue blocker, see section 5 |
| Infrastructure and G&A | ~$2.4M | |
| Buffer | ~$1.4M | |

The alternative — raising $8M — funds 16 months and forces the enterprise build to be sequenced rather than parallel. We think that's a false economy given section 5.

Process: materials ready, first conversations begin late June, target term sheet by mid-August.

---

## 4. Product

**Shipped in Q2:** onboarding simplification (trial-to-paid 4.1% → 6.3%), infrastructure cost reduction, tracing private beta to eight accounts.

**Deferred out of Q2:** tracing GA moved to Q3 on two blocking issues in the sampling path. Billing revamp sequenced behind it.

**Q3 plan:** tracing GA mid-August, onboarding v2, billing revamp, audit log export.

---

## 5. Enterprise readiness — commercial risk

New item on this agenda, raised deliberately.

Two deals stalled in security review this quarter — one on federated identity, one on EU data residency. Neither capability is currently scheduled.

Quantifying the exposure. Accounts with an identity or compliance requirement we cannot presently meet, measured as ARR at renewal risk over the next twelve months:

| Account | ARR | Requirement | Renewal |
|---|---|---|---|
| Northwind Logistics | $84,000 | SAML SSO, audit log export | 30 Sep 2026 |
| Calder Systems | $62,000 | SOC 2 Type II report | 1 Jan 2027 |
| Bastion Freight | $48,000 | SOC 2 Type II report | 1 Mar 2027 |
| **Total** | **$190,000** | | |

That is 22% of current ARR.

Audit log export is scoped for Q3. SOC 2 observation begins October. **Federated identity is not scheduled in Q3** — the quarter is consumed by tracing GA and the billing revamp, and identity is a five-to-seven week build with an auth-path migration we are unwilling to run alongside a GA.

Current plan places identity in Q4, October to November.

The board should understand that this sequencing accepts risk on the Northwind renewal specifically, as it is the only one of the three that falls due before the capability lands.

---

## 6. Head of Engineering

Search opened in May. Approved band $240,000 base, up to 0.8% equity — set at roughly the 60th percentile after losing two candidates on compensation earlier in the year.

Four candidates in process, two at final stage. Target start date 1 October.

---

## 7. Q3 preview

Objectives: close the Series A, reach $1.3M ARR, ship audit log export and tracing GA, fill the Head of Engineering role.

Next meeting 17 September 2026.

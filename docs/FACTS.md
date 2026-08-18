# FACTS.md — Canonical Fact Sheet

Single source of truth for the Tensile world. Every signal and supporting document renders facts from this table.

**Rule:** if a number appears in two documents, it comes from here. Never invent a figure while writing a document — add it here first, then use it. A contradiction between documents reads as a retrieval bug during evaluation, and you will waste an afternoon debugging code that works.

**Present day:** August 2026. History runs from February 2026.

---

## Company

| | |
|---|---|
| Name | Tensile |
| Product | Load testing and performance monitoring for engineering teams |
| Modules | Tensile Load (load testing) · Tensile Watch (production monitoring) · Distributed Tracing (shipping Q3) |
| Founded | March 2024 |
| Seed round | $4.0M, August 2025, led by Halden Partners at $18M post |
| Competitors | Surge Labs, Percival |

---

## Financials by Month

| Month | ARR | MRR | Net burn | Cash | Customers | Headcount |
|---|---|---|---|---|---|---|
| Feb 2026 | $620,000 | $51,700 | $155,000 | $2.40M | 38 | 11 |
| Mar 2026 | $690,000 | $57,500 | $162,000 | $2.24M | 43 | 12 |
| Apr 2026 | $770,000 | $64,200 | $168,000 | $2.07M | 47 | 12 |
| May 2026 | $860,000 | $71,700 | $175,000 | $1.90M | 52 | 13 |
| Jun 2026 | $940,000 | $78,300 | $181,000 | $1.72M | 56 | 13 |
| Jul 2026 | $1,040,000 | $86,700 | $188,000 | $1.53M | 61 | 14 |
| Aug 2026 | $1,120,000 | $93,300 | $192,000 | $1.34M | 64 | 14 |

Runway as of August 2026: **7 months**, to approximately March 2027. This is why they're raising.

Growth decelerated in June (9.3% month over month, down from ~11.5%). That dip is deliberate — it gives the investor updates something real to explain and makes a good question.

---

## Customers

| Customer | ACV | Contact | Notes |
|---|---|---|---|
| Northwind Logistics | $84,000 | Linda Marsh, VP Engineering | Largest account. Renewal 30 Sep 2026. |
| Calder Systems | $62,000 | — | |
| Bastion Freight | $48,000 | — | Awaiting SOC 2 report |
| Ravelin Health | $31,000 | — | |
| Meridian Grid | $28,000 | — | |

Remaining ARR is roughly 59 smaller self-serve accounts.

**ARR at risk from unmet enterprise requirements — $190,000, 22% of current ARR:**

| Account | ARR | Requirement | Renewal |
|---|---|---|---|
| Northwind Logistics | $84,000 | SAML SSO, audit log export | 30 Sep 2026 |
| Calder Systems | $62,000 | SOC 2 Type II | 1 Jan 2027 |
| Bastion Freight | $48,000 | SOC 2 Type II | 1 Mar 2027 |

Northwind is the only one falling due before the capability lands. This figure first appears in the Q2 board deck.

---

## The Northwind Thread ⚠️ Load-bearing

The flagship demo depends on these facts being exactly right.

| | |
|---|---|
| MSA signed | 30 September 2025 |
| Term | 12 months, **no automatic renewal** — requires a new executed Order Form |
| Named users | 40 at signature, $150/user/month above that |
| SLA | 99.5% monthly uptime with service credits |
| Data region | eu-west-2 |
| Renewal date | **30 September 2026** |
| ACV | $84,000 |
| Contact | Linda Marsh, VP Engineering |
| Security contact | Karin Holt, Information Security |
| Seat growth | 40 → 58 active users since signature |
| Proposed renewal | $96,000 (14% uplift), offered 3 Aug 2026 — Linda declined pending SSO confirmation |
| Procurement deadline | 5 September 2026 |
| Access audit | Week of 21 September 2026 |

**The commitment:**

| | |
|---|---|
| Promised by | Marcus Oyelaran (Head of Sales) |
| Promised to | Linda Marsh |
| Date of email | **11 June 2026** |
| Ravi Menon | CC'd on the thread — the CEO knew |
| What was promised | SAML SSO shipped by **15 September 2026** |
| Exact phrasing | "we'll have SAML SSO shipped for you by September 15" |

**The reality:**

| | |
|---|---|
| Q3 roadmap (Jul–Sep) | Distributed tracing GA · self-serve onboarding · billing revamp · audit log export (end of Aug). **No SSO.** |
| Q4 roadmap (Oct–Dec) | "SAML SSO — enterprise readiness", scheduled Oct–Nov 2026 |
| Slippage | 6–8 weeks past the promised date, and past the renewal |

**The third surface:** the Notion customer commitments log records commitments to Northwind (audit logs, Q3), Bastion Freight (SOC 2 report), and Calder Systems (SLA upgrade). It does **not** record the SSO promise. The commitment exists in email and nowhere else.

That gives the flagship question three surfaces — promised in Gmail, absent from the Q3 roadmap, missing from the commitments log — and no single source can answer it.

---

## The Raise ⚠️ Load-bearing

| | |
|---|---|
| Seed | $4.0M, Aug 2025, Halden Partners, $18M post |
| Series A target | $12M |

**Fernpath Capital** — term sheet in hand

| | |
|---|---|
| Partner | Priya Kothari |
| Term sheet received | **22 July 2026** |
| Terms | $12M at $52M post-money |
| Exclusivity | 30 days, expires **21 August 2026** |
| Option pool | Proposed 12% pre-money, negotiated to **10.5%** |
| Board | Fernpath takes one seat, board goes to five. Independent seat to be filled within six months of close. |
| Other terms | 1x non-participating preference, broad-based weighted average anti-dilution |

**Aster Ventures** — competing, slower

| | |
|---|---|
| Partner | James Okonkwo |
| Status | Verbal interest, no term sheet |
| Indicated | $10M at $45M post-money |
| First meeting | 4 June 2026 |

---

## Hiring ⚠️ Load-bearing

Role: **Head of Engineering**, opened May 2026. Decision deadline **22 August 2026**.

Approved budget: **$240,000 base**, up to **0.8% equity**.

| Candidate | Current role | Current base | Asking base | Asking equity | Notice | References |
|---|---|---|---|---|---|---|
| Elena Vasquez | Director of Engineering, Series C company | $248,000 + ~15% bonus | **$265,000** | 0.9% | 8 weeks | Completed 30 Jul 2026 |
| Tom Brennan | Staff Engineer / team lead | $198,000, equity underwater | **$225,000** | 0.6% | 4 weeks | Pending |

Elena has one other conversation in progress — early, no offer. Above-band offers need board approval, and Nadia requires the case in writing ahead of any meeting.

Elena is **$25,000 over budget** and above the equity band. Tom is under budget on both. That tension is deliberate — it makes a natural question and the two figures are a near-miss pair for the reranker.

These salary figures and candidate names are also the honest justification for PII redaction.

---

## Board

| Member | Role |
|---|---|
| Ravi Menon | CEO, co-founder |
| Dana Whitfield | CTO, co-founder |
| Nadia Osei | Halden Partners |
| — | Independent seat vacant |

Meetings: 12 March 2026 (Q1) · 18 June 2026 (Q2) · 17 September 2026 (Q3, scheduled)

---

## Pitch Decks — the near-miss pair

| | v3 | v4 |
|---|---|---|
| Dated | 6 July 2026 | 17 July 2026 |
| ARR shown | $940,000 | $1,040,000 |
| Ask | $10M at $45M | $12M at $52M |
| Enterprise slide | Absent | Added |

Near-identical documents, different figures. Retrieving "the pitch deck" is easy; retrieving the one with the $12M ask is not. This is the cleanest reranking test in the corpus.

---

## Timeline

| Date | Event |
|---|---|
| Mar 2024 | Tensile founded |
| Aug 2025 | $4.0M seed, Halden Partners |
| 30 Sep 2025 | Northwind MSA signed |
| 12 Mar 2026 | Q1 board meeting |
| May 2026 | Head of Engineering search opens |
| 4 Jun 2026 | First Aster Ventures meeting |
| **11 Jun 2026** | **SSO promised to Northwind for 15 Sep** |
| 18 Jun 2026 | Q2 board meeting |
| Jun 2026 | Growth decelerates to 9.3% |
| 19–27 May 2026 | Northwind security review — SSO and audit logs flagged |
| 30 Jul 2026 | Elena Vasquez references completed |
| **22 Jul 2026** | **Fernpath term sheet received** |
| **21 Aug 2026** | **Fernpath exclusivity expires** |
| 22 Aug 2026 | Head of Engineering decision deadline |
| **15 Sep 2026** | **Date SSO was promised** |
| 14 Aug 2026 | Distributed tracing GA, included in Team tier |
| 24–25 Sep 2026 | Company offsite |
| 17 Sep 2026 | Q3 board meeting |
| **30 Sep 2026** | **Northwind renewal** |
| Oct–Nov 2026 | SSO actually scheduled |
| ~Mar 2027 | Cash out at current burn |

---

## Facts Golden Questions Will Hinge On

Get these wrong and the eval suite tests nothing:

1. SSO promised **15 Sep 2026**, actually scheduled **Oct–Nov 2026**
2. Northwind renewal is **30 Sep 2026** — before SSO ships
3. Monthly ARR figures — six near-identical documents, one right answer per question
4. Elena asks **$265k** against a **$240k** budget
5. Fernpath: **$12M at $52M**. Aster: **$10M at $45M**
6. Fernpath exclusivity expires **21 Aug 2026**
7. Runway is **7 months** as of August 2026

---

## Deliberate Gaps

Reasonable questions with no answer in the corpus. The system must refuse rather than invent — this is what the missing-data eval category tests.

- Who fills the independent board seat
- What Northwind's renewal decision actually is
- Which candidate was hired
- Whether the Fernpath round closed
- Any revenue figure after August 2026

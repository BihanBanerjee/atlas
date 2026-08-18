#!/usr/bin/env python3
"""
Generate the noise tier of the Tensile corpus.

Noise documents exist to make retrieval a genuine problem. They are in-domain —
Tensile vendors, Tensile scheduling, Tensile operations — so they compete for
retrieval against real queries rather than sitting harmlessly far away in
embedding space.

Two rules govern everything here:

1. DETERMINISTIC. Fixed seed, so regenerating produces a byte-identical corpus.
   The eval fixtures must be frozen across all eight versions; noise that
   changes between runs would break cross-version comparison.

2. NO LOAD-BEARING FACTS. Nothing here may state ARR, headcount, the SSO dates,
   or anything else in FACTS.md. A noise document that contradicts the fact
   sheet reads as a retrieval bug during evaluation.

Usage:
    python scripts/generate_noise.py            # generate
    python scripts/generate_noise.py --clean    # remove noise, then generate
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260809
CORPUS = Path(__file__).resolve().parent.parent / "data" / "corpus"

START = date(2026, 2, 1)
END = date(2026, 8, 8)

COUNTS = {"gmail": 100, "notion": 25, "drive": 20}

TEAM = [
    ("Ravi Menon", "ravi@tensile.dev"),
    ("Dana Whitfield", "dana@tensile.dev"),
    ("Marcus Oyelaran", "marcus@tensile.dev"),
]

ENGINEERS = [
    "Sofia Almeida",
    "Ben Turner",
    "Chidi Nwosu",
    "Hana Sato",
    "Luca Ferrari",
    "Amara Diallo",
]

SERVICES = ["api", "scheduler", "generator-fleet", "results-ingest", "web"]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def random_date(rng: random.Random) -> date:
    return START + timedelta(days=rng.randint(0, (END - START).days))


def weekly_dates(count: int) -> list[date]:
    """Evenly spaced dates across the corpus window, snapped to weekdays."""
    span = (END - START).days
    step = span / max(count, 1)
    out = []
    for i in range(count):
        d = START + timedelta(days=int(i * step))
        while d.weekday() > 4:
            d += timedelta(days=1)
        out.append(d)
    return out


def infra_cost(d: date, rng: random.Random) -> int:
    """AWS spend tracks the June cost-reduction work described in the corpus."""
    base = 31_000 if d < date(2026, 6, 1) else 17_000
    return base + rng.randint(-1_800, 1_800)


def write_doc(path: Path, frontmatter: list[str], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "---\n" + "\n".join(frontmatter) + "\n---\n\n" + body.strip() + "\n"
    path.write_text(content, encoding="utf-8")


def clean_noise() -> int:
    """
    Delete only files whose frontmatter declares `tier: noise`.

    Signal and supporting documents are hand-written and must never be touched
    by this script — the tier check is the guard, not the filename.
    """
    removed = 0
    for path in CORPUS.rglob("*.md"):
        head = path.read_text(encoding="utf-8")[:400]
        if "tier: noise" in head:
            path.unlink()
            removed += 1
    return removed


# --------------------------------------------------------------------------- #
# gmail
# --------------------------------------------------------------------------- #


def gen_vendor_invoices(rng: random.Random) -> list[tuple[str, list[str], str]]:
    docs = []
    vendors = [
        ("Amazon Web Services", "aws-receipts@amazon.com", None),
        ("Datadog", "billing@datadoghq.com", (890, 1_240)),
        ("GitHub", "billing@github.com", (294, 336)),
        ("Linear", "billing@linear.app", (168, 224)),
        ("Notion", "team@makenotion.com", (140, 196)),
        ("Sentry", "billing@sentry.io", (312, 468)),
        ("Postmark", "billing@postmarkapp.com", (89, 145)),
        ("Stripe", "billing@stripe.com", (420, 890)),
    ]
    n = 0
    for month in range(2, 9):
        for vendor, sender, amount_range in vendors:
            if vendor != "Amazon Web Services" and rng.random() > 0.45:
                continue
            d = date(2026, month, rng.randint(1, 5))
            if amount_range:
                amount = rng.randint(*amount_range)
            else:
                amount = infra_cost(d, rng)
            n += 1
            slug = f"invoice-{vendor.lower().replace(' ', '-')}-{d.isoformat()}"
            fm = [
                f"id: gmail-noise-{slug}",
                "source: gmail",
                "type: email",
                "tier: noise",
                f'subject: "{vendor} — invoice for {d.strftime("%B %Y")}"',
                f"thread_id: n-{4000 + n}",
                f"date: {d.isoformat()}",
                "participants:",
                f"  - {vendor} <{sender}>",
                "  - Ravi Menon <ravi@tensile.dev>",
            ]
            body = f"""**From:** {vendor} <{sender}>
**To:** Ravi Menon <ravi@tensile.dev>
**Date:** {d.strftime("%-d %B %Y")}
**Subject:** {vendor} — invoice for {d.strftime("%B %Y")}

Your invoice is ready.

| | |
|---|---|
| Account | Tensile, Inc. |
| Period | {d.strftime("%B %Y")} |
| Amount due | ${amount:,}.00 |
| Payment method | Card ending 4417 |

Payment will be collected automatically. No action required.

View invoice in your billing dashboard.
"""
            docs.append((f"gmail/noise-{slug}.md", fm, body))
    return docs


def gen_standups(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    docs = []
    for i, d in enumerate(weekly_dates(count)):
        author = rng.choice(ENGINEERS)
        done = rng.sample(
            [
                "Merged the retry backoff change on results-ingest",
                "Cleared the flaky test in the scheduler suite",
                "Reviewed two PRs on the generator fleet",
                "Updated the runbook for capacity alerts",
                "Paired with Hana on the ClickHouse query plan",
                "Cut the staging environment we stopped using",
                "Bumped the Go toolchain across all services",
                "Fixed the timezone bug in scheduled runs",
            ],
            k=2,
        )
        today = rng.choice(
            [
                "Picking up the sampling ticket",
                "Continuing on the results diff endpoint",
                "On-call, so whatever on-call brings",
                "Writing the migration for the retention change",
                "Finishing the load generator refactor",
            ]
        )
        blocked = rng.choice(
            ["Nothing", "Nothing", "Nothing", "Waiting on a review", "Nothing"]
        )
        fm = [
            f"id: gmail-noise-standup-{d.isoformat()}",
            "source: gmail",
            "type: email",
            "tier: noise",
            f'subject: "Standup — {d.strftime("%A %-d %B")}"',
            f"thread_id: n-{5000 + i}",
            f"date: {d.isoformat()}",
            "participants:",
            "  - engineering@tensile.dev",
        ]
        body = f"""**From:** {author} <{author.split()[0].lower()}@tensile.dev>
**To:** engineering@tensile.dev
**Date:** {d.strftime("%-d %B %Y")}, 09:32
**Subject:** Standup — {d.strftime("%A %-d %B")}

**Yesterday**
- {done[0]}
- {done[1]}

**Today**
- {today}

**Blocked**
- {blocked}
"""
        docs.append((f"gmail/noise-standup-{d.isoformat()}.md", fm, body))
    return docs


def gen_deploy_notices(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    docs = []
    for i in range(count):
        d = random_date(rng)
        service = rng.choice(SERVICES)
        sha = "".join(rng.choices("0123456789abcdef", k=7))
        duration = rng.randint(41, 186)
        fm = [
            f"id: gmail-noise-deploy-{i:03d}",
            "source: gmail",
            "type: email",
            "tier: noise",
            f'subject: "Deploy succeeded — {service}"',
            f"thread_id: n-{6000 + i}",
            f"date: {d.isoformat()}",
            "participants:",
            "  - CI <ci@tensile.dev>",
            "  - engineering@tensile.dev",
        ]
        body = f"""**From:** CI <ci@tensile.dev>
**To:** engineering@tensile.dev
**Date:** {d.strftime("%-d %B %Y")}, {rng.randint(9, 18):02d}:{rng.randint(0, 59):02d}
**Subject:** Deploy succeeded — {service}

Service `{service}` deployed to production.

| | |
|---|---|
| Commit | `{sha}` |
| Author | {rng.choice(ENGINEERS)} |
| Duration | {duration}s |
| Tests | passed |
| Performance check | no regression |

Rollback available for 24 hours.
"""
        docs.append((f"gmail/noise-deploy-{i:03d}.md", fm, body))
    return docs


def gen_calendar(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    meetings = [
        ("Weekly engineering sync", 60),
        ("1:1", 30),
        ("Sprint planning", 90),
        ("Design review", 45),
        ("Customer call", 30),
        ("Leadership sync", 60),
        ("Retro", 60),
        ("Interview — technical", 90),
    ]
    docs = []
    for i in range(count):
        d = random_date(rng)
        title, mins = rng.choice(meetings)
        organiser, email = rng.choice(TEAM)
        hour = rng.randint(9, 17)
        fm = [
            f"id: gmail-noise-invite-{i:03d}",
            "source: gmail",
            "type: email",
            "tier: noise",
            f'subject: "Invitation: {title}"',
            f"thread_id: n-{7000 + i}",
            f"date: {d.isoformat()}",
            "participants:",
            f"  - {organiser} <{email}>",
        ]
        body = f"""**From:** {organiser} <{email}>
**Date:** {d.strftime("%-d %B %Y")}
**Subject:** Invitation: {title}

You have been invited to **{title}**.

| | |
|---|---|
| When | {d.strftime("%A %-d %B %Y")}, {hour:02d}:00 – {hour:02d}:{mins % 60:02d} |
| Duration | {mins} minutes |
| Where | Google Meet |
| Organiser | {organiser} |

Accept · Decline · Maybe
"""
        docs.append((f"gmail/noise-invite-{i:03d}.md", fm, body))
    return docs


def gen_newsletters(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    sources = [
        ("The Pragmatic Engineer", "newsletter@pragmaticengineer.com"),
        ("SRE Weekly", "hello@sreweekly.com"),
        ("Infra Digest", "digest@infradigest.io"),
        ("Go Weekly", "editor@goweekly.dev"),
        ("Cloud Cost Report", "reports@cloudcost.watch"),
    ]
    topics = [
        "What we learned running Postgres at scale",
        "The hidden cost of your observability bill",
        "Incident review: a four-hour outage nobody noticed",
        "Why your load tests are lying to you",
        "Sampling strategies for high-cardinality traces",
        "Hiring engineering managers: what actually predicts success",
        "The case against microservices, again",
    ]
    docs = []
    for i in range(count):
        d = random_date(rng)
        name, sender = rng.choice(sources)
        picks = rng.sample(topics, k=3)
        fm = [
            f"id: gmail-noise-newsletter-{i:03d}",
            "source: gmail",
            "type: email",
            "tier: noise",
            f'subject: "{name} — {d.strftime("%-d %B")}"',
            f"thread_id: n-{8000 + i}",
            f"date: {d.isoformat()}",
            "participants:",
            f"  - {name} <{sender}>",
        ]
        body = f"""**From:** {name} <{sender}>
**To:** Ravi Menon <ravi@tensile.dev>
**Date:** {d.strftime("%-d %B %Y")}
**Subject:** {name} — {d.strftime("%-d %B")}

This week:

1. **{picks[0]}**
2. **{picks[1]}**
3. **{picks[2]}**

Plus the usual links, jobs, and one thing that made us laugh.

*You are receiving this because you subscribed. Unsubscribe at any time.*
"""
        docs.append((f"gmail/noise-newsletter-{i:03d}.md", fm, body))
    return docs


def gen_cold_outbound(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    vendors = [
        ("Kessler Recruiting", "outreach@kesslerrecruit.com", "engineering talent"),
        ("ScaleOps", "sales@scaleops.io", "Kubernetes cost optimisation"),
        ("Braintrust Analytics", "hello@braintrust-analytics.com", "product analytics"),
        ("SecureFrame Pro", "team@secureframepro.com", "SOC 2 automation"),
        ("DevRel Collective", "partnerships@devrelcollective.com", "developer marketing"),
        ("Vantage Cloud", "sales@vantagecloud.co", "cloud spend visibility"),
    ]
    docs = []
    for i in range(count):
        d = random_date(rng)
        company, sender, offering = rng.choice(vendors)
        fm = [
            f"id: gmail-noise-outbound-{i:03d}",
            "source: gmail",
            "type: email",
            "tier: noise",
            f'subject: "Quick question, Ravi"',
            f"thread_id: n-{9000 + i}",
            f"date: {d.isoformat()}",
            "participants:",
            f"  - {company} <{sender}>",
        ]
        body = f"""**From:** {company} <{sender}>
**To:** Ravi Menon <ravi@tensile.dev>
**Date:** {d.strftime("%-d %B %Y")}
**Subject:** Quick question, Ravi

Hi Ravi,

Noticed Tensile has been growing — congratulations on the momentum.

We help companies at your stage with {offering}. Teams we work with typically see results within the first quarter, and we're happy to run a short assessment at no cost.

Would you be open to fifteen minutes next week?

Best,
{company}

*Not interested? Reply STOP and we'll remove you.*
"""
        docs.append((f"gmail/noise-outbound-{i:03d}.md", fm, body))
    return docs


# --------------------------------------------------------------------------- #
# notion
# --------------------------------------------------------------------------- #


def gen_notion_noise(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    runbooks = [
        ("Runbook — Capacity alert", "generator fleet capacity below threshold"),
        ("Runbook — Results ingestion lag", "ingestion queue depth growing"),
        ("Runbook — Failed deploy rollback", "a deploy needs reverting"),
        ("Runbook — Customer data export request", "a customer requests their data"),
        ("Runbook — Certificate renewal", "a TLS certificate approaches expiry"),
    ]
    templates = [
        "Template — Design document",
        "Template — Incident report",
        "Template — Weekly update",
        "Template — Interview feedback",
    ]
    stale = [
        ("Project Halberd (archived)", "Abandoned Feb 2026"),
        ("Mobile client exploration (archived)", "Parked, no owner"),
        ("Terraform provider spike (archived)", "Spike only, not scheduled"),
        ("Pricing page rebuild (superseded)", "Superseded by the June experiment"),
        ("2025 planning notes (archived)", "Historical"),
    ]
    wiki = [
        ("Expense policy", "How to claim, what's covered, what isn't."),
        ("Holiday and leave", "Unlimited within reason. Book it in the calendar."),
        ("Tooling and access", "What we use and how to get added."),
    ]

    docs: list[tuple[str, list[str], str]] = []

    for title, trigger in runbooks:
        d = random_date(rng)
        slug = title.lower().replace(" — ", "-").replace(" ", "-")
        fm = [
            f"id: notion-noise-{slug}",
            "source: notion",
            "type: page",
            "tier: noise",
            f'title: "{title}"',
            'parent: "Engineering / Runbooks"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
        ]
        body = f"""# {title}

**Trigger:** {trigger}

## Steps

1. Acknowledge the alert in the on-call channel.
2. Check the service dashboard for the affected component.
3. Confirm scope — one customer or all customers.
4. If scope is all customers, escalate to secondary immediately.
5. Apply the mitigation below.
6. Record start and end times for the incident log.

## Mitigation

Follow the standard procedure for this component. If the standard procedure
does not resolve within fifteen minutes, escalate rather than continuing to
investigate alone.

## After

Raise a follow-up ticket. If customer-facing, notify the account owner.
"""
        docs.append((f"notion/noise-{slug}.md", fm, body))

    for i in range(8):
        d = weekly_dates(8)[i]
        slug = f"old-notes-{d.isoformat()}"
        fm = [
            f"id: notion-noise-{slug}",
            "source: notion",
            "type: page",
            "tier: noise",
            f'title: "Team notes — {d.strftime("%-d %B %Y")}"',
            'parent: "Company / Meeting Notes / Archive"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
        ]
        body = f"""# Team notes — {d.strftime("%-d %B %Y")}

Quick sync, no formal agenda.

- Reviewed the sprint board, nothing blocked
- {rng.choice(ENGINEERS)} walked through the changes to the results view
- Discussed whether to move standup to async — no decision
- Reminder about expense claims before month end

Next sync same time.
"""
        docs.append((f"notion/noise-{slug}.md", fm, body))

    for title in templates:
        d = random_date(rng)
        slug = title.lower().replace(" — ", "-").replace(" ", "-")
        fm = [
            f"id: notion-noise-{slug}",
            "source: notion",
            "type: page",
            "tier: noise",
            f'title: "{title}"',
            'parent: "Company / Templates"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
        ]
        body = f"""# {title}

*Duplicate this page to use it.*

## Context

_Why does this exist? One paragraph._

## Detail

_The substance. Bullet points are fine._

## Decision or outcome

_What was decided, and who decided it._

## Follow-ups

- [ ] Owner — action — date
"""
        docs.append((f"notion/noise-{slug}.md", fm, body))

    for title, note in stale:
        d = random_date(rng)
        slug = title.lower().split(" (")[0].replace(" ", "-")
        fm = [
            f"id: notion-noise-{slug}",
            "source: notion",
            "type: page",
            "tier: noise",
            f'title: "{title}"',
            'parent: "Archive"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
        ]
        body = f"""# {title}

> **Archived.** {note}

Original notes retained below for reference. Nothing here is current and
nothing here is being worked on.

## Original scope

A short exploration that did not proceed past the initial write-up. The
reasoning at the time is captured in the meeting notes from that period.

## Why it stopped

Capacity. It was not a judgement on the idea.
"""
        docs.append((f"notion/noise-{slug}.md", fm, body))

    for title, summary in wiki:
        d = random_date(rng)
        slug = title.lower().replace(" ", "-")
        fm = [
            f"id: notion-noise-{slug}",
            "source: notion",
            "type: page",
            "tier: noise",
            f'title: "{title}"',
            'parent: "Company / Handbook"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
        ]
        body = f"""# {title}

{summary}

If something here is unclear or out of date, edit it rather than asking.
That is the whole policy on editing the handbook.

Questions to Ravi.
"""
        docs.append((f"notion/noise-{slug}.md", fm, body))

    return docs[:count]


# --------------------------------------------------------------------------- #
# drive
# --------------------------------------------------------------------------- #


def gen_drive_noise(rng: random.Random, count: int) -> list[tuple[str, list[str], str]]:
    docs: list[tuple[str, list[str], str]] = []

    for month in range(2, 8):
        d = date(2026, month, 28)
        total = rng.randint(2_100, 4_800)
        fm = [
            f"id: drive-noise-expenses-{d.isoformat()}",
            "source: gdrive",
            "type: spreadsheet",
            "tier: noise",
            f'title: "Expenses — {d.strftime("%B %Y")}"',
            "file_type: google_sheets",
            'folder: "Finance / Expenses"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
            "owner: Ravi Menon",
        ]
        body = f"""# Expenses — {d.strftime("%B %Y")}

| Category | Amount |
|---|---|
| Travel | ${rng.randint(200, 900):,} |
| Meals and entertainment | ${rng.randint(300, 700):,} |
| Software and subscriptions | ${rng.randint(400, 1200):,} |
| Equipment | ${rng.randint(0, 1400):,} |
| Office and supplies | ${rng.randint(100, 400):,} |
| **Total** | **${total:,}** |

Submitted for approval. Receipts in the shared folder.
"""
        docs.append((f"drive/noise-expenses-{d.isoformat()}.md", fm, body))

    for month in range(2, 6):
        d = date(2026, month, 5)
        fm = [
            f"id: drive-noise-metrics-export-{d.isoformat()}",
            "source: gdrive",
            "type: spreadsheet",
            "tier: noise",
            f'title: "Metrics export — {d.strftime("%B %Y")} (superseded)"',
            "file_type: google_sheets",
            'folder: "Finance / Archive"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
            "owner: Ravi Menon",
        ]
        body = f"""# Metrics export — {d.strftime("%B %Y")}

> **Superseded.** This export predates the current financial model and
> should not be used. Refer to the FY26 model for authoritative figures.

Raw export from the analytics dashboard. Column definitions changed in
April 2026, so figures here are not directly comparable with later exports.

Retained for audit purposes only.
"""
        docs.append((f"drive/noise-metrics-export-{d.isoformat()}.md", fm, body))

    sows = [
        ("Auditor", "SOC 2 Type II readiness and observation"),
        ("Design contractor", "Marketing site refresh"),
        ("Legal", "Standard commercial terms review"),
        ("Penetration testing", "Annual application assessment"),
    ]
    for i, (vendor, scope) in enumerate(sows):
        d = random_date(rng)
        fm = [
            f"id: drive-noise-sow-{i:02d}",
            "source: gdrive",
            "type: document",
            "tier: noise",
            f'title: "Statement of Work — {vendor}"',
            "file_type: pdf",
            'folder: "Legal / Vendors"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
            "owner: Ravi Menon",
        ]
        body = f"""# Statement of Work — {vendor}

**Scope:** {scope}

**Term:** commencing {d.strftime("%-d %B %Y")}, twelve months.

## Deliverables

As described in the attached schedule. Any change to scope requires a written
variation signed by both parties.

## Fees

Invoiced monthly in arrears, net thirty days.

## General

Governed by the laws of England and Wales. Standard confidentiality and data
protection terms apply as set out in the master agreement.
"""
        docs.append((f"drive/noise-sow-{i:02d}.md", fm, body))

    misc = [
        ("LoadCon 2025 — talk slides", "Conference / 2025"),
        ("Brand guidelines v2 (archived)", "Marketing / Archive"),
        ("Website copy — old homepage", "Marketing / Archive"),
        ("Team photos — offsite 2025", "Company / Photos"),
        ("Logo variants", "Marketing / Brand"),
        ("Onboarding deck — 2025 version", "People / Archive"),
    ]
    for i, (title, folder) in enumerate(misc):
        d = random_date(rng)
        slug = title.lower().split(" (")[0].replace(" — ", "-").replace(" ", "-")
        fm = [
            f"id: drive-noise-{slug}",
            "source: gdrive",
            "type: document",
            "tier: noise",
            f'title: "{title}"',
            "file_type: pdf",
            f'folder: "{folder}"',
            f"created: {d.isoformat()}",
            f"updated: {d.isoformat()}",
            "owner: Marcus Oyelaran",
        ]
        body = f"""# {title}

Archived material retained for reference. Not current.

Superseded by later versions held elsewhere in the drive. Nothing in this
document should be treated as authoritative.
"""
        docs.append((f"drive/noise-{slug}.md", fm, body))

    return docs[:count]


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def build_gmail(rng: random.Random, target: int) -> list[tuple[str, list[str], str]]:
    docs = gen_vendor_invoices(rng)
    docs += gen_standups(rng, 25)
    docs += gen_deploy_notices(rng, 14)
    docs += gen_calendar(rng, 20)
    docs += gen_newsletters(rng, 10)
    docs += gen_cold_outbound(rng, 12)

    # top up or trim to hit the target exactly
    if len(docs) < target:
        docs += gen_deploy_notices(rng, target - len(docs))
    return docs[:target]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the noise tier.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove existing noise documents first (signal and supporting are never touched)",
    )
    args = parser.parse_args()

    if args.clean:
        removed = clean_noise()
        print(f"removed {removed} existing noise documents")

    rng = random.Random(SEED)

    written = {"gmail": 0, "notion": 0, "drive": 0}

    for rel, fm, body in build_gmail(rng, COUNTS["gmail"]):
        write_doc(CORPUS / rel, fm, body)
        written["gmail"] += 1

    for rel, fm, body in gen_notion_noise(rng, COUNTS["notion"]):
        write_doc(CORPUS / rel, fm, body)
        written["notion"] += 1

    for rel, fm, body in gen_drive_noise(rng, COUNTS["drive"]):
        write_doc(CORPUS / rel, fm, body)
        written["drive"] += 1

    total = sum(written.values())
    print(f"gmail  {written['gmail']:>4}")
    print(f"notion {written['notion']:>4}")
    print(f"drive  {written['drive']:>4}")
    print(f"total  {total:>4} noise documents")


if __name__ == "__main__":
    main()

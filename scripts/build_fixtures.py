#!/usr/bin/env python3
"""
Build the frozen CI eval fixtures from the hand-written corpus.

Fixtures are a small, controlled subset of data/corpus — not the full corpus.
The full corpus (256 docs) is "live demo data" per docs/PERSONA.md; fixtures
are what eval/golden_dataset.json is actually written against, and what CI
indexes on every push. See docs/specs/2026-08-08-agentic-rag-guardrail-design.md
section 10.2.

Two kinds of document go into the fixtures, and both are load-bearing:

1. ANSWER-BEARING (the ANSWERS_* lists). Chosen so every question in
   eval/golden_dataset.json is answerable from these documents alone.

2. DISTRACTORS (the DISTRACTORS_* lists). Documents that plausibly compete for
   retrieval and do not hold the answer. A fixture set of only answer-bearing
   documents makes Context Precision meaningless — it is 100% by construction,
   because there is nothing wrong to retrieve — and leaves the reranker with
   nothing to rerank. Distractors are drawn from the same neighbourhoods
   docs/PERSONA.md identifies as dense (ARR and financials, compensation,
   renewals, SSO and identity, roadmap), not from random noise, because a
   document only functions as a distractor if it could plausibly answer the
   question and doesn't.

The split above describes WHY each document is in the set — it is build-time
intent, not ground truth, and it is deliberately NOT written into the output.
Relevance is a property of the (question, document) pair: the same resume is a
valid source for the notice-period question and a decoy for the salary-ask
question. The only ground truth is `acceptable_sources` in
eval/golden_dataset.json, maintained per question.

Usage:
    python scripts/build_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
OUT = ROOT / "eval" / "fixtures"

# --------------------------------------------------------------------------- #
# Answer-bearing documents — mapped to the golden_dataset.json question(s) each
# one answers.
# --------------------------------------------------------------------------- #

ANSWERS_GMAIL = [
    "northwind-sso-commitment.md",      # q01 q02 q03
    "northwind-renewal.md",             # q05 q06 q21 q22
    "northwind-security-review.md",     # q03 q04 support
    "investor-update-2026-06.md",       # q07 q09
    "investor-update-2026-07.md",       # q08
    "investor-update-2026-02.md",       # reranking distractor
    "investor-update-2026-05.md",       # reranking distractor
    "metrics-snapshot-2026-08-07.md",   # weekly numbers, in-flight context
    "fernpath-term-sheet.md",           # q11 q13
    "aster-competing-interest.md",      # q12
    "comp-discussion-vasquez.md",       # q15 q17
    "comp-discussion-brennan.md",       # q16 q17
    "bastion-soc2-followup.md",         # q23
    "calder-soc2-question.md",          # q19 support
]

ANSWERS_NOTION = [
    "roadmap-q3-2026.md",               # q03
    "roadmap-q4-2026.md",               # q03 support
    "customer-commitments-log.md",      # q04
    "hiring-pipeline.md",               # q18
    "head-of-engineering-scorecard.md", # q18 support
    "okrs-q3-2026.md",                  # context
    "spec-saml-sso.md",                 # context
]

ANSWERS_DRIVE = [
    "pitch-deck-v3.md",                 # q14
    "pitch-deck-v4.md",                 # q14
    "northwind-msa.md",                 # q05 q06 context
    "board-deck-q2-2026.md",            # q19 q20 context
    "financial-model-2026.md",          # q10 runway — only doc in the corpus with Aug 2026 actuals/forecast
]


# --------------------------------------------------------------------------- #
# Distractors — plausible competitors that do NOT hold the answer. Annotated
# with the question each one is positioned against.
# --------------------------------------------------------------------------- #

DISTRACTORS_GMAIL = [
    "investor-thornhill.md",            # q11 q12 — another investor, no term sheet
    "investor-kestrel.md",              # q11 q12 — another investor conversation
    "investor-oakmont-pass.md",         # q11 q12 — an investor who passed
    "calder-renewal-early.md",          # q05 q21 q22 — a renewal thread, wrong customer
    "meridian-renewal.md",              # q05 q21 q22 — a renewal thread, wrong customer
    "ravelin-quarterly-review.md",      # q19 — customer review, adjacent to at-risk ARR
    "backend-hire-offer-may.md",        # q15 q16 — a different offer, different figures
    "northwind-support-webhooks.md",    # q01-q06 — Northwind thread, wrong topic
    "noise-invoice-amazon-web-services-2026-08-04.md",  # q07-q10 — financial-shaped noise
]

DISTRACTORS_NOTION = [
    "roadmap-q1-2026.md",               # q03 — roadmap, wrong quarter
    "roadmap-q2-2026.md",               # q03 — roadmap, wrong quarter, contains no SSO
    "spec-audit-log-export.md",         # q03 q04 — the OTHER Northwind commitment
    "hiring-retrospective-h1.md",       # q15-q18 — hiring content, wrong specifics
]

DISTRACTORS_DRIVE = [
    "month-end-close-june.md",          # q07 — restates June ARR in a competing doc
    "month-end-close-july.md",          # q08 — restates July ARR in a competing doc
    "compensation-benchmarking.md",     # q15 q16 — salary bands, not the candidates' asks
    "resume-elena-vasquez.md",          # q15 — Elena's details, not her ask
    "resume-tom-brennan.md",            # q16 — Tom's details, not his ask
    "board-deck-q1-2026.md",            # q19 q20 — competes with the Q2 deck
    "cap-table-summary.md",             # q11 q13 — ownership/valuation figures
    "noise-metrics-export-2026-05-05.md",  # q07-q10 — superseded metrics, looks authoritative
    "northwind-security-questionnaire.md", # q01-q04 — security content, no SSO promise
]


def parse_doc(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} has no frontmatter")
    _, fm_text, body = text.split("---", 2)
    frontmatter = yaml.safe_load(fm_text) or {}
    frontmatter["body"] = body.strip()
    frontmatter["_file"] = path.name
    return frontmatter


def build(source: str, answers: list[str], distractors: list[str]) -> list[dict]:
    """Parse both lists into one document set. No per-document relevance tag is
    emitted — see the module docstring for why."""
    docs = []
    for filenames in (answers, distractors):
        for name in filenames:
            path = CORPUS / source / name
            if not path.exists():
                raise FileNotFoundError(path)
            docs.append(parse_doc(path))
    return docs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    fixtures = {
        "emails.json": build("gmail", ANSWERS_GMAIL, DISTRACTORS_GMAIL),
        "notion_pages.json": build("notion", ANSWERS_NOTION, DISTRACTORS_NOTION),
        "drive_docs.json": build("drive", ANSWERS_DRIVE, DISTRACTORS_DRIVE),
    }

    total = 0
    for filename, docs in fixtures.items():
        out_path = OUT / filename
        out_path.write_text(json.dumps(docs, indent=2, default=str) + "\n", encoding="utf-8")
        total += len(docs)
        print(f"{filename}: {len(docs)} documents -> {out_path.relative_to(ROOT)}")

    print(f"\ntotal: {total} documents")


if __name__ == "__main__":
    main()

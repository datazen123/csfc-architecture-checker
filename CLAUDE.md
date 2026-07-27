# Context for Claude Code working in this repo

This repo is one of a **10-repo public portfolio** (github.com/datazen123)
demonstrating real, live-verified agentic AI engineering for a specific
DoD-contractor job pursuit. Full README below covers this repo in detail;
this file covers conventions and status a coding agent needs before making
changes.

## This repo's role

Checks a proposed CSfC (Commercial Solutions for Classified)
layered-encryption architecture against real NSA CSfC principles
(Components List categories, NIAP validation, layer independence,
independent IP stacks). **Important limitation, documented honestly in the
README**: five independent attempts to fetch NSA's primary Capability
Package PDF directly (media.defense.gov, nsa.gov, an archive.org mirror,
via both curl and an automated fetch tool) were blocked by NSA's own
access controls - not simulated or assumed, actually attempted and
confirmed blocked. This repo's checks are grounded in well-corroborated
architectural facts cross-referenced across multiple NSA-hosted document
listings, NOT exact requirement-ID citations from the primary document -
stated precisely rather than inventing a requirement number to sound more
authoritative.

**Status (2026-07-27)**: 18/18 tests passing (including Hypothesis
property-based tests), live-verified end-to-end, first attempt, no
correction pass needed - all 4 planted architecture violations correctly
detected and explained.

## Non-negotiable discipline this whole portfolio follows

1. Never fabricate a source - if a primary source is genuinely
   unreachable after real attempts, say so plainly (this repo is the
   clearest example of that discipline in the whole portfolio).
2. Deterministic code owns every check (component categories, NIAP
   validation, layer independence, IP stack independence); Claude only
   explains risk and drafts remediation.
3. Live-verify against the real Anthropic API before claiming a result.
4. Synthetic demo data (`data/proposed_architecture.json`) is labeled as
   such - no real product names or real vulnerabilities.
5. Pytest suite (including Hypothesis property-based tests), GitHub
   Actions CI (pytest + bandit), "Security notes" README section, pinned
   dependencies.
6. No real client, unit, or classified-sounding content ever.
7. Ask Sage (not Claude directly) is named as the realistic DoD/DIB
   production deployment path.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in your own ANTHROPIC_API_KEY, never commit it
pytest -q
```

Full cross-repo strategy, founder research, and environment notes live in
the private `datazen123/securebine-portfolio-context` repo - not
duplicated here since this repo is public.

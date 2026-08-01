# csfc-architecture-checker

This checks a proposed CSfC (Commercial Solutions for Classified)
architecture - the NSA program that lets sensitive government data travel
over ordinary commercial encryption products instead of custom
military-grade hardware, as long as it's wrapped in two independent
encryption layers, each built only from NSA-approved product categories
and individually certified secure - **NIAP validation**, meaning tested
and certified by the National Information Assurance Partnership, the
U.S. government's own independent testing scheme, not a vendor's
self-certification.

Every check here - is each component from an approved category, is it
certified, are the two layers genuinely independent, do they run on
separate network stacks - is answered entirely by plain code. Not by
Claude, and not by a person reviewing it live. Claude's only job is
explaining, in plain language, why a failed check matters operationally
and what to do about it.

`data/proposed_architecture.json` is a made-up example architecture built
for this demo: five pretend components (a VPN gateway, two VPN clients, a
device-management console, a key vault), each labeled with the category it
claims, which encryption layer it's on, and whether it's certified. Four
of the five have a deliberate, planted mistake, so the checks below have
something real to catch - it isn't a real deployment or a real product's
configuration.

## Contents

- [On sourcing, stated precisely](#on-sourcing-stated-precisely)
- [Why this exists](#why-this-exists)
- [Architecture](#architecture)
- [Live result](#live-result)
- [Prerequisites](#prerequisites)
- [Running it](#running-it)
- [Troubleshooting](#troubleshooting)
- [Tests + CI](#tests--ci)
- [Deployment path](#deployment-path)
- [Security notes](#security-notes)

## On sourcing, stated precisely

**Where the rules come from**

NSA publishes the real CSfC rules across a few official pages - capability-package summaries, and the CSfC Components List's own category pages.

Cross-checking several of these pages, the same picture shows up every time:

```
  Outer Tunnel   →   Inner Tunnel
    (IPsec)            (IPsec or TLS/SRTP)
```

Two independent layers, like above.

If both layers use a VPN client, each one needs its own separate IP stack - no sharing.

Every component has to come from a real published category:
VPN Gateway, VPN Client, TLS Protected Server, Certificate Authority, Mobile Device Management.

Every component needs NIAP validation - independent testing, not a vendor's own claim.

**What we couldn't get to**

NSA's primary source document was unreachable.

We tried 5 times, from 3 different sources, 2 different methods. All 5 were blocked on NSA's end - not a problem here.

**What that means**

No exact requirement-ID citation from that document.

Just the real principle behind each check, stated plainly - and an honest note that the primary document itself couldn't be reached.

## Why this exists

Checked for currency, not assumed:

- **Real, recent, dollar-verified USFK-area CSfC contract** (though now
  closed, not currently open - checked precisely rather than overstated):
  `W91QVN24F0201`, Iron Bow Technologies, $4.77M, "CSFC Virtual Phase 1
  Mobility Access," 2024-02-26 → 2025-10-31, at USFK's `W91QVN` contracting
  office - the same office behind the USACISA-P and J6 IT awards researched
  elsewhere in this portfolio. No CSfC Phase 2 award or open solicitation
  was found as of this check - the "Phase 1" naming makes a follow-on
  plausible, not confirmed.
- **DoD's own published memory-safety/security-architecture direction**
  (see `cpp-to-rust-modernizer`'s README for the full NSA/CISA memory-safe
  language citation) reflects the same broader posture CSfC embodies:
  layered, independently-validated security components over single-vendor
  trust.

## Architecture

```
data/proposed_architecture.json (synthetic)
        |
        v
  run_all_checks() -- deterministic, code-owned:
    check_component_categories()   - real CSfC Components List categories
    check_niap_validation()        - every component NIAP/CCEVS-validated
    check_layer_independence()     - outer/inner layers use different products
    check_independent_ip_stack()   - dual-VPN layers need independent IP stacks
        |
        v
  Claude explains risk + drafts remediation, citing a source_id
        |
        v
  verify_findings() -- deterministic: does the source_id resolve
  to a real failed check?
        |
        v
  ok? -> printed report
  not ok? -> one bounded correction pass, then printed with
             [NEEDS HUMAN VERIFICATION] tags on anything still unresolved
```

## Live result

Run end-to-end against the real Anthropic API. First attempt, no correction pass needed.

**The 5 components checked:**

| id | category | layer | product |
|---|---|---|---|
| outer-vpn-gw | VPN Gateway | outer | EdgeGuard 4000 |
| outer-vpn-client | VPN Client | outer | EdgeGuard Client |
| inner-vpn-client | VPN Client | inner | EdgeGuard Client |
| mdm-console | Mobile Device Management | management | FleetControl MDM |
| internal-ca | Custom Key Vault | management | KeyKeep |

**The 4 check categories:**

1. Component category - is this a real CSfC category?
2. NIAP validation - is this certified?
3. Layer independence - are outer and inner different products?
4. Independent IP stack - only checked when both layers use a VPN Client

**All 13 checks:**

Component category (5 components, 1 fail):
- outer-vpn-gw, outer-vpn-client, inner-vpn-client, mdm-console → pass
- internal-ca → **FAIL** - "Custom Key Vault" isn't a real CSfC category

NIAP validation (5 components, 1 fail):
- outer-vpn-gw, outer-vpn-client, inner-vpn-client, internal-ca → pass
- mdm-console → **FAIL** - not certified

Layer independence (1 check, 1 fail):
- **FAIL** - outer and inner layers both use "EdgeGuard Client"

Independent IP stack (2 components, 1 fail):
- outer-vpn-client → pass
- inner-vpn-client → **FAIL** - missing the independent-stack flag

**Result: 4 of 13 failed.** All 4 were explained by Claude and verified against their citations.

## Prerequisites

Python 3.9 or newer. Check with `python3 --version` before starting.

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own ANTHROPIC_API_KEY
export $(grep -v '^#' .env | xargs)
python csfc_checker.py
```

The `python3 -m venv` step matters, not just good practice: on macOS,
plain `pip install` can silently resolve to a leftover Python 2.7
install instead of Python 3 - see Troubleshooting below.

## Troubleshooting

**`ERROR: Could not find a version that satisfies the requirement
anthropic<1.0.0,>=0.40.0 ... (from versions: none)`, alongside a "Python
2.7 reached end of life" warning:**

Your `pip` command is resolving to a Python 2.7 installation, not Python
3 - common on macOS, where an old Python 2.7 framework install can sit
earlier on `PATH` than Python 3. The `anthropic` package doesn't publish
anything for Python 2 at all, hence "no versions: none" - it's not a
network or permissions problem.

Fix: create and activate a virtual environment first, exactly as shown
above (`python3 -m venv .venv && source .venv/bin/activate`), then run
`pip install` again inside it. If you'd rather not use a venv, run
`python3 -m pip install -r requirements.txt` instead of bare `pip
install` - that forces the install through Python 3's own pip regardless
of what `pip` alone resolves to on your system.

## Tests + CI

`test_csfc_checker.py` covers every deterministic check function and every
branch of `verify_findings` - no API key or network needed.
`test_csfc_checker_properties.py` adds Hypothesis property-based tests -
e.g. layer-independence pass/fail is proven to exactly track set
disjointness between outer/inner product names across hundreds of
generated product-name combinations, not the one hand-picked example:

```bash
pip install -r requirements-dev.txt
pytest -q
bandit -r . -x "./.venv" --severity-level medium  # security lint, CI runs this too
```

## Deployment path

This demo calls the Anthropic API directly. A production version for a
DoD-adjacent client would more likely run through
**[Ask Sage](https://www.asksage.ai/)** - the IL5/IL6-authorized multi-model
gateway built for Defense Industrial Base contractors (`llm_client.py`
includes an `AskSageClient` built from Ask Sage's
[public API docs](https://github.com/Ask-Sage/AskSage-Open-Source-Community),
untested pending an account).

## Security notes

- API keys are read from environment variables only, never hardcoded;
  `.env` is gitignored, `.env.example` ships placeholders only.
- A malformed/non-JSON model response raises a clear, actionable error
  (with the raw response attached) instead of an opaque traceback.
- Dependencies are version-pinned with an upper bound (`>=X,<NEXT_MAJOR`).
- No component in `data/proposed_architecture.json` names a real product
  with real vulnerabilities - all product names are synthetic
  ("SyntheticCorp ...").

Built with [Claude Code](https://claude.com/claude-code).

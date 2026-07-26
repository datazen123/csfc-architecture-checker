# csfc-architecture-checker

Deterministic code checks a proposed CSfC (Commercial Solutions for
Classified) layered-encryption network architecture against real NSA CSfC
program requirements - component categories, NIAP validation, layer
independence, and independent IP stacks. Claude's job is the part that's
actually a language task: explaining the operational risk of each
violation in plain language and drafting a remediation - it never decides
whether a component is validated or whether the layers are independent;
that's computed in code from the architecture description.

`data/proposed_architecture.json` is synthetic, illustrative data written
for this demo - not a real deployment or a real product's configuration.

## On sourcing, stated precisely

This repo's checks are grounded in well-corroborated CSfC architectural
principles - cross-referenced across multiple official NSA-hosted document
listings (Mobile Access Capability Package summaries, the CSfC Components
List's own published category pages) that consistently describe the same
requirements: two independent encryption layers (Outer Tunnel via IPsec,
Inner Tunnel via IPsec or TLS/SRTP), independent IP stacks when both layers
use VPN clients, and every component drawn from the real, NSA-published
Components List categories (VPN Gateway, VPN Client, TLS Protected Server,
Certificate Authority, Mobile Device Management), each requiring NIAP/CCEVS
validation.

**What this repo does NOT claim**: exact requirement-ID citations from the
primary Mobile Access Capability Package PDF itself. Five independent
attempts to fetch that document directly - `media.defense.gov`, `nsa.gov`,
and an `archive.org` mirror, via both direct HTTP and an automated fetch
tool - were blocked by access controls / rate limiting on NSA's end, not
by anything on this end. Rather than invent a specific requirement number
to sound more precise, this repo names the real, verified architectural
principle each check enforces and says plainly that the primary document
couldn't be independently reached - the same "cite it or say you couldn't
verify it" discipline used everywhere else in this portfolio, applied here
to an access limitation instead of a missing dataset.

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

Run end-to-end against the real Anthropic API, first attempt, no
correction pass needed: 5 components checked across 4 check categories, 4
of 13 individual checks failed (an unlisted component category, an
unvalidated MDM console, identical products used for both encryption
layers, and a missing independent-IP-stack flag) - all 4 findings correctly
explained and verified against their citations.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your own ANTHROPIC_API_KEY
export $(grep -v '^#' .env | xargs)
python csfc_checker.py
```

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

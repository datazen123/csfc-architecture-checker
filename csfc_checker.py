"""
CSfC (Commercial Solutions for Classified) architecture checker.

Checks a proposed CSfC architecture - the NSA program that lets sensitive
government data travel over ordinary commercial encryption products
instead of custom military-grade hardware, as long as it's wrapped in two
independent encryption layers, each built only from NSA-approved product
categories and individually certified secure (NIAP validation).

Every check here is answered entirely by plain code - not by Claude, and
not by a person reviewing it live. Claude's only job is explaining, in
plain language, why a failed check matters operationally and drafting a
remediation.

**On sourcing, stated precisely**: this repo's checks are grounded in
well-corroborated CSfC architectural principles - cross-referenced across
multiple official NSA-hosted document listings (Mobile Access Capability
Package summaries, the CSfC Components List's published category pages)
that consistently describe the same requirements. They are NOT exact
requirement-ID citations from the primary Capability Package PDF itself:
five independent attempts to fetch that PDF directly (media.defense.gov,
nsa.gov, and an archive.org mirror, via both direct HTTP and an automated
fetch tool) were blocked by access controls / rate limiting on NSA's end,
not by anything on this end. This repo names the real, verified
architectural principle each check enforces, and states plainly that the
primary document itself couldn't be independently reached.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python csfc_checker.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from llm_client import AnthropicClient

ROOT = Path(__file__).parent
CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$", re.MULTILINE)
MAX_CORRECTION_RETRIES = 1

# The real CSfC Components List product categories (NSA-published, verified
# across multiple independent NSA-hosted category listing pages, e.g.
# nsa.gov/.../components-list/selections/vpn-gateways.pdf,
# .../vpn-clients.pdf, .../tls-protected-servers.pdf). A component whose
# category isn't one of these isn't on the real CSfC Components List at all.
VALID_COMPONENT_CATEGORIES = {
    "VPN Gateway", "VPN Client", "TLS Protected Server",
    "Certificate Authority", "Mobile Device Management",
}


def extract_json(text: str) -> dict | list:
    try:
        return json.loads(CODE_FENCE_RE.sub("", text.strip()).strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Claude's response wasn't valid JSON: {exc}\nRaw response:\n{text}") from exc


def check_component_categories(components: list[dict]) -> list[dict]:
    """Every component must be a real, listed CSfC Components List
    category - no LLM judgment, a plain set-membership check."""
    return [
        {"id": c["id"], "check": "component_category",
         "status": "pass" if c["category"] in VALID_COMPONENT_CATEGORIES else "FAIL",
         "detail": f"category '{c['category']}' is not one of the real CSfC Components List categories"
                   if c["category"] not in VALID_COMPONENT_CATEGORIES else None}
        for c in components
    ]


def check_niap_validation(components: list[dict]) -> list[dict]:
    """Every CSfC component must be NIAP/CCEVS-validated."""
    return [
        {"id": c["id"], "check": "niap_validation",
         "status": "pass" if c.get("niap_validated") else "FAIL",
         "detail": None if c.get("niap_validated") else "component is not marked NIAP/CCEVS-validated"}
        for c in components
    ]


def check_layer_independence(components: list[dict]) -> list[dict]:
    """A CSfC solution needs two INDEPENDENT encryption layers (outer +
    inner) - using the identical product for both defeats the purpose of
    layering (a single vulnerability compromises both layers at once).
    This is a defensible proxy for "independence" (same product = clearly
    not independent), not the full official evaluation criteria, which also
    considers vendor/implementation diversity beyond exact product identity -
    the same "real principle, clearly-labeled proxy check" pattern this
    portfolio's network-config-drift-detector already uses for its own
    interface-shutdown check."""
    outer_products = {c["product"] for c in components if c.get("layer") == "outer"}
    inner_products = {c["product"] for c in components if c.get("layer") == "inner"}
    shared = outer_products & inner_products

    if not shared:
        return [{"id": "layer-independence", "check": "layer_independence", "status": "pass", "detail": None}]
    return [{"id": "layer-independence", "check": "layer_independence", "status": "FAIL",
             "detail": f"the same product(s) {sorted(shared)} are used for both the outer and inner "
                       f"encryption layer - the two layers are not independent"}]


def check_independent_ip_stack(components: list[dict]) -> list[dict]:
    """When both the outer and inner layer use a VPN Client, they must run
    on independent IP stacks to keep the two encryption layers from
    sharing a single point of failure."""
    outer_vpn_clients = [c for c in components if c.get("layer") == "outer" and c["category"] == "VPN Client"]
    inner_vpn_clients = [c for c in components if c.get("layer") == "inner" and c["category"] == "VPN Client"]

    if not (outer_vpn_clients and inner_vpn_clients):
        return []

    results = []
    for c in inner_vpn_clients + outer_vpn_clients:
        results.append({
            "id": c["id"], "check": "independent_ip_stack",
            "status": "pass" if c.get("independent_ip_stack") else "FAIL",
            "detail": None if c.get("independent_ip_stack")
            else "both layers use VPN Clients but this one isn't marked as running on an independent IP stack",
        })
    return results


def run_all_checks(components: list[dict]) -> list[dict]:
    return (
        check_component_categories(components)
        + check_niap_validation(components)
        + check_layer_independence(components)
        + check_independent_ip_stack(components)
    )


def build_payload(check_results: list[dict], components: list[dict]) -> tuple[list[dict], dict]:
    """Assigns a stable id to every FAILED check so Claude's explanations
    can cite one exactly, and returns an id -> item lookup for
    verify_findings() to check citations against."""
    components_by_id = {c["id"]: c for c in components}
    id_index: dict[str, dict] = {}
    payload = []
    for i, r in enumerate(check_results):
        if r["status"] != "FAIL":
            continue
        item = {**r, "id": f"finding:{i}", "component": components_by_id.get(r["id"])}
        payload.append(item)
        id_index[item["id"]] = item
    return payload, id_index


def verify_findings(findings: list[dict], id_index: dict[str, dict]) -> list[dict]:
    """Deterministic verifier - no LLM judgment. Checks every finding's
    source_id resolves to a real failed check."""
    verified = []
    for f in findings:
        source_id = f.get("source_id")
        note = None
        if not source_id:
            note = "no source_id cited - cannot verify this finding against the underlying data"
        elif source_id not in id_index:
            note = f"source_id '{source_id}' does not match any failed check given to the model"
        verified.append({**f, "verified": note is None, "verification_note": note})
    return verified


SYSTEM_PROMPT = """You are a security architect reviewing a proposed CSfC
(Commercial Solutions for Classified) layered-encryption architecture. You
are given a list of failed deterministic checks, each with an "id" - do not
recompute or contradict these, your job is to explain the security
implication of each failure in plain language and draft a remediation.

For each finding, explain what could go wrong operationally if this isn't
fixed, assign a severity (critical/high/medium/low), and draft a concrete
remediation. Every finding MUST include a "source_id" set to the exact
"id" string of the one failed check it is about.

Reply with ONLY JSON (no markdown fences):
{"executive_summary": "...", "findings": [{"item": "...", "source_id": "...", "severity": "...", "explanation": "...", "remediation": "..."}]}
"""

CORRECTION_PROMPT_TEMPLATE = """The following findings failed automated
verification - each cited a source_id that doesn't exist. Fix ONLY these
findings using the original data above; return the corrected findings in
the same JSON shape as before, as a JSON array (no markdown fences, no
surrounding object):

{failed_findings_json}
"""


def main() -> None:
    client = AnthropicClient()

    architecture = json.loads((ROOT / "data" / "proposed_architecture.json").read_text())
    components = architecture["components"]

    check_results = run_all_checks(components)
    failed = [r for r in check_results if r["status"] == "FAIL"]

    print(f"Reviewing architecture: {architecture['solution_name']}")
    print(f"Checked {len(components)} components across "
          f"{len({r['check'] for r in check_results})} check categories.")
    print(f"Checks failed: {len(failed)}/{len(check_results)}\n")

    payload, id_index = build_payload(check_results, components)
    if not payload:
        print("All checks passed - nothing to report.")
        return

    # Prefilling the assistant turn with the JSON's opening character is a
    # documented Anthropic structured-output technique: it makes markdown-
    # fence-wrapping structurally impossible for this response, rather than
    # relying only on stripping fences after the fact. extract_json()'s
    # fence-stripping stays in place as defense-in-depth.
    response = client.create(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(payload, indent=2)}, {"role": "assistant", "content": "{"}],
        max_tokens=2500,
    )
    text = "{" + "".join(b.text for b in response.content if b.type == "text")
    report = extract_json(text)

    findings = verify_findings(report["findings"], id_index)
    unverified = [f for f in findings if not f["verified"]]

    if unverified:
        print(f"(verifier flagged {len(unverified)}/{len(findings)} finding(s) - requesting one correction pass)\n")
        correction_response = client.create(
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": json.dumps(payload, indent=2)},
                {"role": "assistant", "content": text},
                {"role": "user", "content": CORRECTION_PROMPT_TEMPLATE.format(
                    failed_findings_json=json.dumps(unverified, indent=2))},
                {"role": "assistant", "content": "["},
            ],
            max_tokens=1500,
        )
        correction_text = "[" + "".join(b.text for b in correction_response.content if b.type == "text")
        try:
            corrected = verify_findings(extract_json(correction_text), id_index)
            corrected_by_item = {c.get("item"): c for c in corrected}
            findings = [corrected_by_item.get(f.get("item"), f) if not f["verified"] else f for f in findings]
        except RuntimeError as exc:
            print(f"  (correction pass itself failed to parse: {exc} - keeping original flagged findings)\n")

    print("=== CSfC Architecture Review ===\n")
    print(report["executive_summary"] + "\n")
    for f in findings:
        tag = "" if f["verified"] else "  [NEEDS HUMAN VERIFICATION]"
        print(f"[{f['severity'].upper()}] {f['item']}{tag}")
        print(f"    {f['explanation']}")
        print(f"    Remediation: {f['remediation']}")
        if not f["verified"]:
            print(f"    Verifier note: {f['verification_note']}")
        print()

    still_unverified = sum(1 for f in findings if not f["verified"])
    print(f"Verifier summary: {len(findings) - still_unverified}/{len(findings)} findings passed automated "
          f"citation checks.")


if __name__ == "__main__":
    main()

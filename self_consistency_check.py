"""
Self-consistency check: does Claude assign the same severity to the same
finding across multiple independent samples of the same call - and, on
top of that discrete label, does it mean the same thing in the free-text
explanation it writes each time?

Applies Wang, Wei, Schuurmans, Le, Chi, Narang, Chowdhery, Zhou,
"Self-Consistency Improves Chain of Thought Reasoning in Language Models"
(ICLR 2023) to this repo's severity-assignment call: instead of trusting
one sample, this calls it `--samples` times (default 5 - see
semantic_entropy.py's docstring for why) against the identical payload,
then deterministically majority-votes the severity for each finding - the
same "deterministic code owns the decision, Claude only proposes" split
this whole portfolio already uses, extended one level further: Claude
proposes N times, not once, and code picks the consensus.

Severity is a fixed enum, so exact-match majority voting is already the
right tool for it. The per-finding "explanation" text is different -
wording varies sample to sample even when the underlying judgment
doesn't - so this also runs semantic_entropy.py's discrete semantic
entropy (Farquhar et al., Nature 2024) over each finding's sampled
explanations, as a second, complementary uncertainty signal: a finding
can have unanimous severity and still show real semantic entropy if
Claude's stated reasoning for that severity isn't actually stable.

This is additive - it doesn't change csfc_checker.py's default single-call
behavior. It's a separate, live-measured test of how consistent that
call's judgment actually is, not a claim about its accuracy.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python self_consistency_check.py [--samples N]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

from csfc_checker import ROOT, SYSTEM_PROMPT, build_payload, extract_json, run_all_checks, verify_findings
from llm_client import AnthropicClient
from semantic_entropy import cluster_by_meaning, discrete_semantic_entropy, max_entropy

DEFAULT_SAMPLES = 5


def sample_once(client: AnthropicClient, payload: list[dict], id_index: dict) -> dict:
    """One independent sample of the severity-assignment call, verified the
    same way the primary pipeline verifies it - a sample that fails
    verification is excluded from voting, not silently counted."""
    response = client.create(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(payload, indent=2)}, {"role": "assistant", "content": "{"}],
        max_tokens=2500,
    )
    text = "{" + "".join(b.text for b in response.content if b.type == "text")
    report = extract_json(text)
    findings = verify_findings(report["findings"], id_index)
    return {f["source_id"]: f for f in findings if f["verified"] and f.get("source_id")}


def majority_vote(severities: list[str]) -> tuple[str, bool]:
    """Deterministic aggregation - no LLM judgment. Returns the most common
    severity and whether it was unanimous across all samples given."""
    counts = Counter(severities)
    winner, count = counts.most_common(1)[0]
    return winner, count == len(severities)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    args = parser.parse_args()

    client = AnthropicClient()
    architecture = json.loads((ROOT / "data" / "proposed_architecture.json").read_text())
    components = architecture["components"]
    check_results = run_all_checks(components)
    payload, id_index = build_payload(check_results, components)

    if not payload:
        print("All checks passed - nothing to sample.")
        return

    print(f"Sampling the severity-assignment call {args.samples} independent times "
          f"against the identical {len(payload)}-finding payload...\n")

    samples = [sample_once(client, payload, id_index) for _ in range(args.samples)]

    results = {}
    for source_id in id_index:
        severities = [s[source_id]["severity"] for s in samples if source_id in s]
        if len(severities) < args.samples:
            results[source_id] = {
                "severities_by_sample": severities,
                "consensus": None,
                "unanimous": False,
                "note": f"only {len(severities)}/{args.samples} samples produced a verified "
                        f"finding for this id",
            }
            continue
        winner, unanimous = majority_vote(severities)
        results[source_id] = {"severities_by_sample": severities, "consensus": winner, "unanimous": unanimous}

    unanimous_count = sum(1 for r in results.values() if r["unanimous"])
    total = len(results)

    print("=== Self-consistency results (severity, exact-match vote) ===\n")
    for source_id, r in results.items():
        tag = "UNANIMOUS" if r["unanimous"] else "SPLIT"
        print(f"[{tag}] {source_id}: {r['severities_by_sample']} -> consensus: {r['consensus']}")

    print(f"\nUnanimous agreement: {unanimous_count}/{total} findings "
          f"({round(100 * unanimous_count / total) if total else 0}%)")

    print(f"\n=== Semantic entropy over explanation text (Farquhar et al., Nature 2024) ===\n")
    print("Clustering each finding's sampled explanations by meaning (Claude as the "
          "entailment judge, temperature=0)...\n")

    for source_id in id_index:
        explanations = [s[source_id]["explanation"] for s in samples if source_id in s]
        if len(explanations) < 2:
            results[source_id]["semantic_entropy_bits"] = None
            results[source_id]["semantic_entropy_note"] = (
                f"only {len(explanations)} sample(s) had this finding - nothing to cluster")
            continue
        clusters = cluster_by_meaning(client, explanations)
        entropy = discrete_semantic_entropy([len(c) for c in clusters])
        ceiling = max_entropy(len(explanations))
        results[source_id]["semantic_entropy_bits"] = round(entropy, 3)
        results[source_id]["semantic_entropy_normalized"] = round(entropy / ceiling, 3) if ceiling else 0.0
        results[source_id]["meaning_cluster_count"] = len(clusters)
        tag = "CONSISTENT" if entropy == 0.0 else "MIXED"
        print(f"[{tag}] {source_id}: {len(clusters)} meaning-cluster(s) across "
              f"{len(explanations)} samples -> {entropy:.3f} bits")

    scored = [r for r in results.values() if r.get("semantic_entropy_bits") is not None]
    zero_entropy = sum(1 for r in scored if r["semantic_entropy_bits"] == 0.0)
    print(f"\nFindings with zero semantic entropy (explanations all clustered together): "
          f"{zero_entropy}/{len(scored)} "
          f"({round(100 * zero_entropy / len(scored)) if scored else 0}%)")

    (ROOT / "self_consistency_result.json").write_text(json.dumps(results, indent=2) + "\n")
    print("Wrote self_consistency_result.json")


if __name__ == "__main__":
    main()

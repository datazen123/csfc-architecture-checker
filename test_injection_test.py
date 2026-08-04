"""Offline unit tests for injection_test.py's deterministic setup logic -
no API call needed."""
from csfc_checker import run_all_checks
from injection_test import INJECTION_PAYLOAD, build_adversarial_architecture


def test_adversarial_architecture_only_changes_the_targeted_product_field():
    adversarial = build_adversarial_architecture()
    target = next(c for c in adversarial["components"] if c["id"] == "internal-ca")
    assert target["product"] == INJECTION_PAYLOAD
    # every other field on that component is untouched
    others = [c for c in adversarial["components"] if c["id"] != "internal-ca"]
    assert len(others) == 4


def test_injection_does_not_change_deterministic_check_results():
    import json
    from injection_test import ROOT

    clean = json.loads((ROOT / "data" / "proposed_architecture.json").read_text())
    adversarial = build_adversarial_architecture()

    clean_results = run_all_checks(clean["components"])
    adversarial_results = run_all_checks(adversarial["components"])
    assert clean_results == adversarial_results

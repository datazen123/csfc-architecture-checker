"""Offline unit tests for csfc_checker.py's deterministic functions - no API key needed."""
import pytest

from csfc_checker import (
    build_payload,
    check_component_categories,
    check_independent_ip_stack,
    check_layer_independence,
    check_niap_validation,
    extract_json,
    run_all_checks,
    verify_findings,
)


def test_check_component_categories_passes_a_real_category():
    components = [{"id": "c1", "category": "VPN Gateway"}]
    assert check_component_categories(components)[0]["status"] == "pass"


def test_check_component_categories_flags_unlisted_category():
    components = [{"id": "c1", "category": "Custom Key Vault"}]
    result = check_component_categories(components)[0]
    assert result["status"] == "FAIL"
    assert "not one of the real CSfC" in result["detail"]


def test_check_niap_validation_passes_validated_component():
    components = [{"id": "c1", "niap_validated": True}]
    assert check_niap_validation(components)[0]["status"] == "pass"


def test_check_niap_validation_flags_unvalidated_component():
    components = [{"id": "c1", "niap_validated": False}]
    result = check_niap_validation(components)[0]
    assert result["status"] == "FAIL"
    assert "not marked NIAP" in result["detail"]


def test_check_layer_independence_passes_when_products_differ():
    components = [
        {"id": "o1", "layer": "outer", "product": "Vendor A"},
        {"id": "i1", "layer": "inner", "product": "Vendor B"},
    ]
    assert check_layer_independence(components)[0]["status"] == "pass"


def test_check_layer_independence_flags_shared_product_across_layers():
    components = [
        {"id": "o1", "layer": "outer", "product": "Same Vendor Client"},
        {"id": "i1", "layer": "inner", "product": "Same Vendor Client"},
    ]
    result = check_layer_independence(components)[0]
    assert result["status"] == "FAIL"
    assert "Same Vendor Client" in result["detail"]


def test_check_independent_ip_stack_skipped_when_not_both_layers_are_vpn():
    components = [{"id": "o1", "layer": "outer", "category": "VPN Client"}]
    assert check_independent_ip_stack(components) == []


def test_check_independent_ip_stack_flags_missing_flag():
    components = [
        {"id": "o1", "layer": "outer", "category": "VPN Client", "independent_ip_stack": True},
        {"id": "i1", "layer": "inner", "category": "VPN Client", "independent_ip_stack": False},
    ]
    results = {r["id"]: r for r in check_independent_ip_stack(components)}
    assert results["o1"]["status"] == "pass"
    assert results["i1"]["status"] == "FAIL"


def test_run_all_checks_combines_every_check_category():
    components = [{"id": "c1", "category": "VPN Gateway", "layer": "outer", "product": "X", "niap_validated": True}]
    results = run_all_checks(components)
    check_names = {r["check"] for r in results}
    assert "component_category" in check_names
    assert "niap_validation" in check_names
    assert "layer_independence" in check_names


def test_build_payload_only_includes_failed_checks():
    components = [{"id": "c1", "category": "VPN Gateway"}]
    check_results = [
        {"id": "c1", "check": "component_category", "status": "pass", "detail": None},
        {"id": "c1", "check": "niap_validation", "status": "FAIL", "detail": "not validated"},
    ]
    payload, id_index = build_payload(check_results, components)
    assert len(payload) == 1
    assert payload[0]["check"] == "niap_validation"
    assert set(id_index) == {"finding:1"}


def test_verify_findings_passes_correctly_cited_finding():
    id_index = {"finding:0": {"id": "finding:0"}}
    result = verify_findings([{"item": "x", "source_id": "finding:0"}], id_index)
    assert result[0]["verified"] is True


def test_verify_findings_flags_unresolvable_source_id():
    result = verify_findings([{"item": "x", "source_id": "finding:99"}], {})
    assert result[0]["verified"] is False
    assert "does not match" in result[0]["verification_note"]


def test_extract_json_strips_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_raises_clear_error_on_malformed_json():
    with pytest.raises(RuntimeError, match="wasn't valid JSON"):
        extract_json("not json")

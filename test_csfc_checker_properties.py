"""Property-based tests (Hypothesis) for csfc_checker.py's deterministic
functions - invariants checked across hundreds of generated inputs, not
just hand-picked examples. No API key or network needed."""
from hypothesis import given, settings
from hypothesis import strategies as st

from csfc_checker import (
    VALID_COMPONENT_CATEGORIES,
    check_component_categories,
    check_layer_independence,
    check_niap_validation,
)

VALID_CATEGORY = st.sampled_from(sorted(VALID_COMPONENT_CATEGORIES))
ARBITRARY_STRING = st.text(min_size=1, max_size=30)


@given(category=VALID_CATEGORY)
@settings(max_examples=200)
def test_every_real_csfc_category_always_passes(category):
    """Every category actually on the real CSfC Components List must
    always pass, for all 5 real categories, not just the one used in the
    hand-written example test."""
    result = check_component_categories([{"id": "c1", "category": category}])[0]
    assert result["status"] == "pass"


@given(category=ARBITRARY_STRING)
@settings(max_examples=200)
def test_any_category_not_in_the_real_list_always_fails(category):
    """Whatever string is generated, if it isn't one of the 5 real CSfC
    categories, it must be flagged - across hundreds of random strings,
    not just one hand-picked 'Custom Key Vault' example."""
    if category in VALID_COMPONENT_CATEGORIES:
        return  # skip the (rare) case Hypothesis generates a real category by chance
    result = check_component_categories([{"id": "c1", "category": category}])[0]
    assert result["status"] == "FAIL"


@given(validated=st.booleans())
@settings(max_examples=50)
def test_niap_validation_status_matches_the_flag_exactly(validated):
    result = check_niap_validation([{"id": "c1", "niap_validated": validated}])[0]
    assert result["status"] == ("pass" if validated else "FAIL")


@given(
    outer_products=st.lists(ARBITRARY_STRING, min_size=1, max_size=5, unique=True),
    inner_products=st.lists(ARBITRARY_STRING, min_size=1, max_size=5, unique=True),
)
@settings(max_examples=200)
def test_layer_independence_matches_set_disjointness(outer_products, inner_products):
    """The pass/fail outcome must exactly track whether the outer and
    inner product sets share any element - across many generated product
    name combinations, including ones that happen to overlap."""
    components = (
        [{"id": f"o{i}", "layer": "outer", "product": p} for i, p in enumerate(outer_products)]
        + [{"id": f"i{i}", "layer": "inner", "product": p} for i, p in enumerate(inner_products)]
    )
    result = check_layer_independence(components)[0]
    shares_a_product = bool(set(outer_products) & set(inner_products))
    assert result["status"] == ("FAIL" if shares_a_product else "pass")

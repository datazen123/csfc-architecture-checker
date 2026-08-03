"""Offline unit tests for self_consistency_check.py's deterministic
majority-vote logic - no API call needed."""
from self_consistency_check import majority_vote


def test_unanimous_agreement():
    winner, unanimous = majority_vote(["high", "high", "high"])
    assert winner == "high"
    assert unanimous is True


def test_majority_wins_without_unanimity():
    winner, unanimous = majority_vote(["high", "high", "medium"])
    assert winner == "high"
    assert unanimous is False


def test_single_sample_is_trivially_unanimous():
    winner, unanimous = majority_vote(["critical"])
    assert winner == "critical"
    assert unanimous is True


def test_tie_picks_one_consistent_winner_deterministically():
    # Counter.most_common ties break on insertion order - just confirm it
    # returns one of the tied values and correctly reports non-unanimous.
    winner, unanimous = majority_vote(["high", "medium"])
    assert winner in ("high", "medium")
    assert unanimous is False

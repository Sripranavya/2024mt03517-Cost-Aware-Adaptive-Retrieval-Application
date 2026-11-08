"""Unit tests for the answer-quality prediction metrics and percentile helper."""

import pytest

from app.core.metrics import (
    SUCCESS_F1_THRESHOLD,
    exact_match,
    normalize_answer,
    percentile,
    token_scores,
)


def test_normalize_answer_strips_punctuation_articles_and_case():
    assert normalize_answer("The  Capital, of France!") == "capital of france"


def test_exact_match_after_normalisation():
    assert exact_match("The capital is Paris.", "capital is paris") == 1.0
    assert exact_match("Paris", "Tokyo") == 0.0


def test_token_scores_identical_answer_is_perfect():
    precision, recall, f1 = token_scores("the capital of france", "the capital of france")
    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1.0)
    assert f1 == pytest.approx(1.0)


def test_token_scores_verbose_answer_has_full_recall_low_precision():
    # A verbose but correct answer recovers the whole reference (recall 1.0) but
    # carries extra tokens, so precision < 1.0.
    prediction = "France is in Europe and the capital of France is Paris"
    reference = "the capital of France is Paris"
    precision, recall, f1 = token_scores(prediction, reference)
    assert recall == pytest.approx(1.0)
    assert precision < 1.0
    assert 0.0 < f1 < 1.0


def test_token_scores_disjoint_answer_scores_zero():
    assert token_scores("tokyo japan", "paris france") == (0.0, 0.0, 0.0)


def test_token_scores_both_empty_is_perfect():
    assert token_scores("", "") == (1.0, 1.0, 1.0)


def test_token_scores_empty_prediction_scores_zero():
    assert token_scores("", "paris") == (0.0, 0.0, 0.0)


def test_success_threshold_is_in_unit_interval():
    assert 0.0 < SUCCESS_F1_THRESHOLD <= 1.0


def test_percentile_interpolates_between_ranks():
    values = [10.0, 20.0, 30.0, 40.0]
    assert percentile(values, 0.0) == 10.0
    assert percentile(values, 100.0) == 40.0
    assert percentile(values, 50.0) == pytest.approx(25.0)


def test_percentile_empty_returns_zero():
    assert percentile([], 95.0) == 0.0


def test_percentile_single_value():
    assert percentile([7.5], 95.0) == 7.5


def test_percentile_rejects_out_of_range_q():
    with pytest.raises(ValueError):
        percentile([1.0, 2.0], 150.0)

"""Unit tests for the ML query-difficulty / cost predictor."""

from app.core.ml.features import FEATURE_NAMES, extract_features, feature_vector
from app.core.ml.predictor import (
    DIFFICULTY_CLASSES,
    QueryDifficultyPredictor,
    get_predictor,
)

_RECOMMENDED = {"fixed", "pomdp", "crag"}


def test_feature_extraction_is_deterministic():
    query = "Compare TCP and UDP?"
    assert extract_features(query) == extract_features(query)
    assert len(feature_vector(query)) == len(FEATURE_NAMES)


def test_feature_values_make_sense():
    feats = extract_features("Why did the Roman Empire fall, and how did it change Europe?")
    assert feats["is_question"] == 1.0
    assert feats["question_words"] >= 1.0
    assert feats["conjunctions"] >= 1.0
    assert feats["word_count"] > 5.0
    assert feats["proper_nouns"] >= 1.0


def test_predictor_is_deterministic():
    first = QueryDifficultyPredictor().predict("What is the capital of France?")
    second = QueryDifficultyPredictor().predict("What is the capital of France?")
    assert first == second


def test_prediction_shape_and_bounds():
    pred = get_predictor().predict("What is the capital of France?")
    assert pred.difficulty in DIFFICULTY_CLASSES
    assert 0.0 <= pred.difficulty_confidence <= 1.0
    assert abs(sum(pred.class_probabilities.values()) - 1.0) < 1e-6
    assert pred.predicted_hops >= 1
    assert pred.predicted_cost_usd >= 0.0
    assert pred.recommended_strategy in _RECOMMENDED


def test_complex_query_needs_more_hops_than_simple():
    predictor = get_predictor()
    simple = predictor.predict("Who wrote Hamlet?")
    hard = predictor.predict("Compare and contrast mitosis and meiosis in detail.")
    assert simple.difficulty == "simple"
    assert hard.difficulty == "complex"
    assert hard.predicted_hops >= simple.predicted_hops


def test_recommended_strategy_matches_difficulty():
    pred = get_predictor().predict("What is the boiling point of water?")
    mapping = {"simple": "fixed", "moderate": "pomdp", "complex": "crag"}
    assert pred.recommended_strategy == mapping[pred.difficulty]

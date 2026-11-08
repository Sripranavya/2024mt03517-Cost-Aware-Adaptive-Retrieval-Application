"""ML query-difficulty / cost predictor (pure NumPy, trained at first use).

Two small models are fit on a bundled, labelled query set:

* a **multinomial logistic-regression** classifier (batch gradient descent) that
  predicts a query's difficulty class — ``simple`` / ``moderate`` / ``complex``;
* a **ridge regressor** (closed form) that predicts how many retrieval hops the
  query will need.

From the predicted hops we derive an expected cost, and from the difficulty we
recommend a cost-aware strategy. Training is deterministic (fixed data, zero
initialisation, fixed iterations) so predictions are reproducible for tests and
run fully offline — no model files, no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from app.core.ml.features import extract_features, feature_vector

DIFFICULTY_CLASSES: tuple[str, ...] = ("simple", "moderate", "complex")

# Cost-aware strategy recommendation per predicted difficulty.
_STRATEGY_BY_DIFFICULTY: dict[str, str] = {
    "simple": "fixed",
    "moderate": "pomdp",
    "complex": "crag",
}

# Approximate USD cost of a single retrieval hop (turns hops into a cost).
_COST_PER_HOP_USD = 0.0015

# Labelled training set: (query, difficulty, hops). Small, transparent, balanced.
_TRAINING_DATA: tuple[tuple[str, str, int], ...] = (
    ("What is the capital of France?", "simple", 1),
    ("Who wrote Hamlet?", "simple", 1),
    ("What is water made of?", "simple", 1),
    ("Define photosynthesis.", "simple", 1),
    ("What year did World War II end?", "simple", 1),
    ("What is the boiling point of water?", "simple", 1),
    ("How does a transformer model work?", "moderate", 3),
    ("Explain how vaccines train the immune system.", "moderate", 3),
    ("What are the main causes of inflation?", "moderate", 3),
    ("Describe the water cycle and its stages.", "moderate", 3),
    ("How is electricity generated from wind?", "moderate", 3),
    ("What is the difference between TCP and UDP?", "moderate", 3),
    ("Compare and contrast mitosis and meiosis in detail.", "complex", 5),
    ("Explain the relationship between inflation, interest rates and unemployment.", "complex", 5),
    ("Compare supervised and unsupervised learning and explain when to use both.", "complex", 5),
    ("Why did the Roman Empire fall and how did it affect medieval Europe?", "complex", 5),
    ("Contrast the causes and consequences of the French and Russian revolutions.", "complex", 5),
    ("How do transformers differ from RNNs and why does attention help both?", "complex", 5),
)


@dataclass(frozen=True)
class QueryPrediction:
    """Prediction for a single query."""

    difficulty: str
    difficulty_confidence: float
    class_probabilities: dict[str, float]
    predicted_hops: int
    predicted_cost_usd: float
    recommended_strategy: str
    features: dict[str, float]


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


class QueryDifficultyPredictor:
    """Softmax difficulty classifier + ridge hops regressor over query features."""

    def __init__(
        self,
        learning_rate: float = 0.3,
        iterations: int = 800,
        l2: float = 1e-3,
        ridge_alpha: float = 1.0,
    ) -> None:
        raw = np.array([feature_vector(q) for q, _, _ in _TRAINING_DATA], dtype=float)
        self._mean = raw.mean(axis=0)
        std = raw.std(axis=0)
        std[std == 0.0] = 1.0  # avoid divide-by-zero for constant features
        self._std = std
        features = (raw - self._mean) / self._std

        labels = [d for _, d, _ in _TRAINING_DATA]
        label_idx = np.array([DIFFICULTY_CLASSES.index(d) for d in labels])
        onehot = np.zeros((len(labels), len(DIFFICULTY_CLASSES)))
        onehot[np.arange(len(labels)), label_idx] = 1.0
        self._weights, self._bias = self._fit_softmax(
            features, onehot, learning_rate, iterations, l2
        )

        hops = np.array([h for _, _, h in _TRAINING_DATA], dtype=float)
        self._hops_coef = self._fit_ridge(features, hops, ridge_alpha)

    @staticmethod
    def _fit_softmax(
        features: np.ndarray, onehot: np.ndarray, lr: float, iters: int, l2: float
    ) -> tuple[np.ndarray, np.ndarray]:
        n_samples, n_features = features.shape
        n_classes = onehot.shape[1]
        weights = np.zeros((n_features, n_classes))
        bias = np.zeros(n_classes)
        for _ in range(iters):
            probs = _softmax(features @ weights + bias)
            error = probs - onehot
            grad_w = features.T @ error / n_samples + l2 * weights
            grad_b = error.mean(axis=0)
            weights -= lr * grad_w
            bias -= lr * grad_b
        return weights, bias

    @staticmethod
    def _fit_ridge(features: np.ndarray, targets: np.ndarray, alpha: float) -> np.ndarray:
        n_samples, n_features = features.shape
        design = np.hstack([np.ones((n_samples, 1)), features])  # prepend bias column
        reg = alpha * np.eye(n_features + 1)
        reg[0, 0] = 0.0  # do not regularise the bias term
        return np.linalg.solve(design.T @ design + reg, design.T @ targets)

    def _standardize(self, query: str) -> np.ndarray:
        vec = np.array(feature_vector(query), dtype=float)
        return (vec - self._mean) / self._std

    def predict(self, query: str) -> QueryPrediction:
        """Predict difficulty, hops, cost and a recommended strategy for ``query``."""
        standardized = self._standardize(query)
        probs = _softmax((standardized @ self._weights + self._bias)[None, :])[0]
        idx = int(np.argmax(probs))
        difficulty = DIFFICULTY_CLASSES[idx]
        class_probabilities = {
            cls: float(p) for cls, p in zip(DIFFICULTY_CLASSES, probs, strict=True)
        }

        design = np.concatenate([[1.0], standardized])
        raw_hops = float(design @ self._hops_coef)
        predicted_hops = int(max(1, round(raw_hops)))
        predicted_cost = round(predicted_hops * _COST_PER_HOP_USD, 6)
        return QueryPrediction(
            difficulty=difficulty,
            difficulty_confidence=float(probs[idx]),
            class_probabilities=class_probabilities,
            predicted_hops=predicted_hops,
            predicted_cost_usd=predicted_cost,
            recommended_strategy=_STRATEGY_BY_DIFFICULTY[difficulty],
            features=extract_features(query),
        )


@lru_cache
def get_predictor() -> QueryDifficultyPredictor:
    """Return the process-wide, deterministically-trained predictor."""
    return QueryDifficultyPredictor()

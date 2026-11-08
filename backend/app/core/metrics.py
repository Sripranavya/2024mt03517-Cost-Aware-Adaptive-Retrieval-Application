"""Answer-quality prediction metrics and performance helpers.

The evaluation harness scores every strategy's predicted answer against a labelled
reference. Alongside the existing *semantic* accuracy (embedding cosine), this
module provides the standard token-overlap **prediction metrics** used to score
extractive question answering:

* **Exact match (EM)** — a strict 0/1 signal after SQuAD-style normalisation
  (lowercasing, punctuation/article removal, whitespace squeezing);
* **Token precision / recall / F1** — the SQuAD F1 metric, where precision
  penalises verbose answers (extra tokens) and recall rewards covering the
  reference, with F1 their harmonic mean.

It also exposes ``percentile`` for reporting latency-distribution tails (p50/p95),
which characterise *performance* far better than the mean alone.

All functions are pure and dependency-free, so they are trivially unit-testable
and shared by both the engine and the offline evaluation scripts.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from collections.abc import Sequence

# An answer whose token-F1 meets this threshold is counted as a correct
# prediction for the aggregate ``success_rate`` (a binary correctness signal on
# top of the continuous F1).
SUCCESS_F1_THRESHOLD = 0.5

_ARTICLES_RE = re.compile(r"\b(a|an|the)\b")
_WS_RE = re.compile(r"\s+")
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def normalize_answer(text: str) -> str:
    """SQuAD-style normalisation: lowercase, drop punctuation/articles, squeeze ws."""
    lowered = text.lower()
    no_punct = lowered.translate(_PUNCT_TABLE)
    no_articles = _ARTICLES_RE.sub(" ", no_punct)
    return _WS_RE.sub(" ", no_articles).strip()


def _tokens(text: str) -> list[str]:
    return normalize_answer(text).split()


def exact_match(prediction: str, reference: str) -> float:
    """Return 1.0 iff the normalised prediction equals the normalised reference."""
    return float(normalize_answer(prediction) == normalize_answer(reference))


def token_scores(prediction: str, reference: str) -> tuple[float, float, float]:
    """Token-level ``(precision, recall, f1)`` — the SQuAD F1 metric.

    Precision is the fraction of predicted tokens that appear in the reference and
    recall the fraction of reference tokens recovered; F1 is their harmonic mean.
    Following the SQuAD convention, two empty strings score ``1.0`` and an
    empty-vs-non-empty pair scores ``0.0``.
    """
    pred_toks = _tokens(prediction)
    ref_toks = _tokens(reference)
    if not pred_toks and not ref_toks:
        return 1.0, 1.0, 1.0
    if not pred_toks or not ref_toks:
        return 0.0, 0.0, 0.0
    overlap = sum((Counter(pred_toks) & Counter(ref_toks)).values())
    if overlap == 0:
        return 0.0, 0.0, 0.0
    precision = overlap / len(pred_toks)
    recall = overlap / len(ref_toks)
    f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolated ``q``-th percentile (``q`` in ``[0, 100]``).

    Returns ``0.0`` for an empty input so callers need no special-casing.
    """
    if not 0.0 <= q <= 100.0:
        raise ValueError("q must be in [0, 100]")
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (q / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return float(ordered[low] + (ordered[high] - ordered[low]) * frac)

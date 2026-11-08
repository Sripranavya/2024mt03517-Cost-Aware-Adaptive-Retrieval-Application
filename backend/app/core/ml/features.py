"""Deterministic feature extraction for the ML query-difficulty predictor.

Turns a raw query string into a fixed-length numeric feature vector. The
features are cheap, transparent lexical signals (length, question words,
multi-hop cue words, conjunctions, proper nouns, ...) so the downstream model is
interpretable and fully reproducible — no tokeniser downloads or network.
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_QUESTION_WORDS = frozenset("what why how when where who whom whose which".split())
_MULTI_HOP_CUES = (
    "compare",
    "contrast",
    "difference",
    "differences",
    "versus",
    " vs ",
    "relationship",
    "cause",
    "because",
    "how does",
    "explain",
    "both",
    "and also",
)

# Fixed feature order used by the model; keep in sync with the vectoriser.
FEATURE_NAMES: tuple[str, ...] = (
    "word_count",
    "char_count",
    "avg_word_len",
    "question_words",
    "multi_hop_cues",
    "conjunctions",
    "has_digit",
    "proper_nouns",
    "clause_count",
    "is_question",
)


def extract_features(query: str) -> dict[str, float]:
    """Return the named lexical features for ``query`` (deterministic)."""
    text = query.strip()
    lower = text.lower()
    words = _WORD_RE.findall(text)
    word_count = len(words)
    avg_word_len = (sum(len(w) for w in words) / word_count) if word_count else 0.0
    question_words = sum(1 for w in words if w.lower() in _QUESTION_WORDS)
    multi_hop_cues = sum(1 for cue in _MULTI_HOP_CUES if cue in lower)
    conjunctions = len(re.findall(r"\b(?:and|or)\b", lower))
    has_digit = 1.0 if any(ch.isdigit() for ch in text) else 0.0
    # Approximate named entities as capitalised words after the first token.
    proper_nouns = sum(1 for w in words[1:] if w[:1].isupper())
    clause_count = float(text.count(",") + conjunctions)
    first_is_question_word = bool(words) and words[0].lower() in _QUESTION_WORDS
    is_question = 1.0 if text.endswith("?") or first_is_question_word else 0.0
    return {
        "word_count": float(word_count),
        "char_count": float(len(text)),
        "avg_word_len": float(avg_word_len),
        "question_words": float(question_words),
        "multi_hop_cues": float(multi_hop_cues),
        "conjunctions": float(conjunctions),
        "has_digit": has_digit,
        "proper_nouns": float(proper_nouns),
        "clause_count": clause_count,
        "is_question": is_question,
    }


def feature_vector(query: str) -> list[float]:
    """Return the query's features as an ordered numeric vector."""
    feats = extract_features(query)
    return [feats[name] for name in FEATURE_NAMES]

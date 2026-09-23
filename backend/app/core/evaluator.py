"""Evidence evaluator: scores retrieved evidence into an ``Observation``.

After each retrieval the evaluator produces the noisy observation the belief
updater consumes. It combines two complementary signals:

* **Relevance** — embedding cosine similarity between the query and the retrieved
  documents (the top matches), clipped to ``[0, 1]``.
* **Coverage** — a lexical rubric: the fraction of the query's content words that
  now appear anywhere in the accumulated evidence. This rises monotonically as
  more of the question is grounded by retrieved text.

It also reports how many *new* vs. *duplicate* documents an action returned, which
drives the redundancy handling in the belief update and reward.
"""

from __future__ import annotations

import re

from app.aws.interfaces import EmbeddingClient
from app.core.pomdp.observation import Observation
from app.core.retrieval.base import RetrievalResult

_WORD_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "the a an of to in is are was were and or for on at by with as be this that "
    "what which who whom whose when where why how do does did from into".split()
)


def _content_tokens(text: str) -> set[str]:
    return {t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS}


class EvidenceAccumulator:
    """Cross-hop evidence bookkeeping for a single query episode."""

    def __init__(self, query: str) -> None:
        self.query_tokens: set[str] = _content_tokens(query)
        self.seen_doc_ids: set[str] = set()
        self.covered_tokens: set[str] = set()


class Evaluator:
    """Turns a ``RetrievalResult`` into an ``Observation``."""

    def __init__(self, embedder: EmbeddingClient, top_n_for_relevance: int = 3) -> None:
        self.embedder = embedder
        self.top_n = max(1, top_n_for_relevance)

    def new_accumulator(self, query: str) -> EvidenceAccumulator:
        return EvidenceAccumulator(query)

    def _relevance(self, result: RetrievalResult) -> float:
        if not result.documents:
            return 0.0
        scores = sorted(
            (max(0.0, min(1.0, d.score)) for d in result.documents), reverse=True
        )
        top = scores[: self.top_n]
        return sum(top) / len(top)

    def observe(self, result: RetrievalResult, acc: EvidenceAccumulator) -> Observation:
        """Score a retrieval result, updating the accumulator in place."""
        new_docs = [d for d in result.documents if d.id not in acc.seen_doc_ids]
        duplicates = len(result.documents) - len(new_docs)
        for doc in new_docs:
            acc.seen_doc_ids.add(doc.id)
            acc.covered_tokens |= _content_tokens(doc.text) & acc.query_tokens

        relevance = self._relevance(result)
        if acc.query_tokens:
            coverage = len(acc.covered_tokens) / len(acc.query_tokens)
        else:
            coverage = relevance
        coverage = min(1.0, coverage)

        # Evaluator self-confidence grows with the amount of new relevant evidence.
        confidence = min(1.0, 0.5 + 0.1 * len(new_docs)) if new_docs else 0.3

        return Observation(
            relevance_signal=relevance,
            evidence_coverage=coverage,
            confidence=confidence,
            source_response_time_ms=result.latency_ms,
            new_documents=len(new_docs),
            duplicate_documents=duplicates,
        )

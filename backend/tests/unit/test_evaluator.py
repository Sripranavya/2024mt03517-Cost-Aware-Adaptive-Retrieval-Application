"""Unit tests for the evidence evaluator."""

from app.aws.embeddings import HashingEmbeddingClient
from app.aws.interfaces import Document
from app.core.evaluator import Evaluator
from app.core.retrieval.base import RetrievalResult


def _result(docs, latency=100.0, query="capital of france"):
    return RetrievalResult(
        source="local_corpus", documents=docs, latency_ms=latency, query_used=query
    )


def test_observe_new_documents_increase_coverage():
    emb = HashingEmbeddingClient(dimension=128)
    ev = Evaluator(emb)
    acc = ev.new_accumulator("capital of france")
    docs = [
        Document(id="1", text="the capital of france is paris", source="local_corpus", score=0.8)
    ]
    obs = ev.observe(_result(docs), acc)
    assert obs.new_documents == 1
    assert obs.duplicate_documents == 0
    assert obs.evidence_coverage > 0.0


def test_observe_duplicates_flagged_redundant():
    emb = HashingEmbeddingClient(dimension=128)
    ev = Evaluator(emb)
    acc = ev.new_accumulator("capital of france")
    docs = [Document(id="1", text="paris capital france", source="local_corpus", score=0.9)]
    ev.observe(_result(docs), acc)
    obs2 = ev.observe(_result(docs), acc)  # same doc again
    assert obs2.new_documents == 0
    assert obs2.duplicate_documents == 1
    assert obs2.is_redundant


def test_observe_empty_result():
    emb = HashingEmbeddingClient(dimension=64)
    ev = Evaluator(emb)
    acc = ev.new_accumulator("something")
    obs = ev.observe(_result([]), acc)
    assert obs.relevance_signal == 0.0
    assert obs.new_documents == 0

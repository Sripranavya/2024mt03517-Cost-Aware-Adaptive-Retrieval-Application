"""Unit tests for the Google Vertex AI provider (LLM + embeddings).

The Vertex SDK is never imported: a fake model is injected into each client so
these tests are fully offline and deterministic. The provider selection logic in
``Settings`` and the factory is exercised too.
"""

import pytest
from pydantic import ValidationError

from app.aws.embeddings import HashingEmbeddingClient, VertexAIEmbeddingClient
from app.aws.factory import build_embedding_client, build_llm_client
from app.aws.llm import MockLLMClient, VertexAILLMClient
from app.config import Settings


# --- fakes ------------------------------------------------------------------
class _FakeUsage:
    def __init__(self, prompt_token_count: int, candidates_token_count: int) -> None:
        self.prompt_token_count = prompt_token_count
        self.candidates_token_count = candidates_token_count


class _FakeResponse:
    def __init__(self, text: str = "", usage: object | None = None) -> None:
        self.text = text
        self.usage_metadata = usage


class _Part:
    def __init__(self, text: str) -> None:
        self.text = text


class _Content:
    def __init__(self, parts: list[_Part]) -> None:
        self.parts = parts


class _Candidate:
    def __init__(self, parts: list[_Part]) -> None:
        self.content = _Content(parts)


class _BlockedResponse:
    """Mimics Vertex raising on ``.text`` but exposing recoverable candidates."""

    usage_metadata = None
    candidates = [_Candidate([_Part("recovered answer")])]

    @property
    def text(self) -> str:
        raise ValueError("response has no candidates / was blocked")


class _FakeGenModel:
    def __init__(self, response: object) -> None:
        self._response = response
        self.last_prompt: str | None = None
        self.last_config: dict | None = None

    def generate_content(self, prompt: str, generation_config: dict | None = None) -> object:
        self.last_prompt = prompt
        self.last_config = generation_config
        return self._response


class _FakeEmbeddingItem:
    def __init__(self, values: list[float]) -> None:
        self.values = values


class _FakeEmbedModel:
    def __init__(self, dim: int, empty: bool = False) -> None:
        self.dim = dim
        self.empty = empty
        self.last_texts: list[str] | None = None

    def get_embeddings(self, texts: list[str]) -> list[_FakeEmbeddingItem]:
        self.last_texts = texts
        if self.empty:
            return []
        return [_FakeEmbeddingItem([float(len(t))] * self.dim) for t in texts]


# --- Vertex LLM -------------------------------------------------------------
def test_vertex_llm_generate_with_usage():
    model = _FakeGenModel(_FakeResponse("Paris is the capital of France.", _FakeUsage(12, 5)))
    llm = VertexAILLMClient("gemini-x", project="proj", model=model)
    resp = llm.generate("Question: capital of France?", max_tokens=64)
    assert "Paris" in resp.text
    assert resp.input_tokens == 12
    assert resp.output_tokens == 5
    assert model.last_config == {"max_output_tokens": 64, "temperature": 0.0}


def test_vertex_llm_generate_without_usage_falls_back_to_token_count():
    model = _FakeGenModel(_FakeResponse("Some answer text here", usage=None))
    llm = VertexAILLMClient("gemini-x", project="proj", temperature=0.3, model=model)
    resp = llm.generate("Question: q?")
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0
    assert model.last_config["temperature"] == 0.3


def test_vertex_llm_empty_text_uses_fallback_message():
    llm = VertexAILLMClient("gemini-x", project="proj", model=_FakeGenModel(_FakeResponse("   ")))
    resp = llm.generate("Question: q?")
    assert "could not find" in resp.text.lower()


def test_vertex_llm_recovers_text_from_candidates_when_text_raises():
    llm = VertexAILLMClient("gemini-x", project="proj", model=_FakeGenModel(_BlockedResponse()))
    resp = llm.generate("Question: q?")
    assert resp.text == "recovered answer"


def test_vertex_llm_requires_model_id():
    with pytest.raises(ValueError):
        VertexAILLMClient("", project="proj", model=_FakeGenModel(_FakeResponse("x")))


def test_vertex_llm_requires_project_without_injected_model():
    with pytest.raises(ValueError):
        VertexAILLMClient("gemini-x", project="")


# --- Vertex embeddings ------------------------------------------------------
def test_vertex_embedding_embed_single():
    model = _FakeEmbedModel(dim=8)
    emb = VertexAIEmbeddingClient("text-embedding-004", project="proj", dimension=8, model=model)
    vec = emb.embed("hello")
    assert len(vec) == 8
    assert model.last_texts == ["hello"]


def test_vertex_embedding_embed_batch_and_empty():
    model = _FakeEmbedModel(dim=4)
    emb = VertexAIEmbeddingClient("text-embedding-004", project="proj", dimension=4, model=model)
    out = emb.embed_batch(["a", "bb"])
    assert len(out) == 2
    assert all(len(v) == 4 for v in out)
    assert emb.embed_batch([]) == []


def test_vertex_embedding_empty_result_raises():
    model = _FakeEmbedModel(dim=4, empty=True)
    emb = VertexAIEmbeddingClient("m", project="proj", dimension=4, model=model)
    with pytest.raises(ValueError):
        emb.embed("x")


def test_vertex_embedding_requires_model_id():
    with pytest.raises(ValueError):
        VertexAIEmbeddingClient("", project="proj", model=_FakeEmbedModel(4))


def test_vertex_embedding_requires_project_without_injected_model():
    with pytest.raises(ValueError):
        VertexAIEmbeddingClient("m", project="")


# --- provider resolution + factory -----------------------------------------
def test_resolved_provider_auto_maps_to_local_or_bedrock():
    local = Settings(USE_LOCAL_MOCKS=True)
    assert local.resolved_llm_provider() == "local"
    assert local.resolved_embedding_provider() == "local"
    cloud = Settings(USE_LOCAL_MOCKS=False, LLM_PROVIDER="auto", EMBEDDING_PROVIDER="auto")
    assert cloud.resolved_llm_provider() == "bedrock"
    assert cloud.resolved_embedding_provider() == "bedrock"


def test_provider_override_wins_over_auto():
    s = Settings(USE_LOCAL_MOCKS=True, LLM_PROVIDER="vertex", EMBEDDING_PROVIDER="vertex")
    assert s.resolved_llm_provider() == "vertex"
    assert s.resolved_embedding_provider() == "vertex"


def test_invalid_provider_rejected():
    with pytest.raises(ValidationError):
        Settings(LLM_PROVIDER="openai")


def test_validate_provider_requirements_vertex_needs_project():
    missing = Settings(USE_LOCAL_MOCKS=True, LLM_PROVIDER="vertex", VERTEX_PROJECT="")
    with pytest.raises(RuntimeError):
        missing.validate_provider_requirements()
    ok = Settings(USE_LOCAL_MOCKS=True, LLM_PROVIDER="vertex", VERTEX_PROJECT="my-proj")
    ok.validate_provider_requirements()  # must not raise


def test_factory_local_builds_mock_clients():
    s = Settings(USE_LOCAL_MOCKS=True)
    assert isinstance(build_llm_client(s), MockLLMClient)
    assert isinstance(build_embedding_client(s), HashingEmbeddingClient)


def test_factory_vertex_branch_requires_project():
    s = Settings(
        USE_LOCAL_MOCKS=True,
        LLM_PROVIDER="vertex",
        EMBEDDING_PROVIDER="vertex",
        VERTEX_PROJECT="",
    )
    with pytest.raises(ValueError):
        build_llm_client(s)
    with pytest.raises(ValueError):
        build_embedding_client(s)


def test_factory_bedrock_branch_requires_model_id():
    s = Settings(
        USE_LOCAL_MOCKS=False,
        LLM_PROVIDER="bedrock",
        EMBEDDING_PROVIDER="bedrock",
        BEDROCK_MODEL_ID="",
        BEDROCK_EMBED_MODEL_ID="",
    )
    with pytest.raises(ValueError):
        build_llm_client(s)
    with pytest.raises(ValueError):
        build_embedding_client(s)

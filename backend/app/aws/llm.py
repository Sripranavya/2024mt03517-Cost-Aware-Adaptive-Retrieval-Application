"""LLM clients: a deterministic local mock and a Bedrock-backed one.

The mock LLM is deterministic (critical for stable tests and reproducible
evaluation): given a RAG prompt containing delimited context and a trailing
question, it performs simple **extractive** answering — it returns the context
sentence with the highest lexical overlap with the question. When the correct
evidence is present in the context this reproduces the reference answer closely,
which lets the offline evaluation harness score answer accuracy without any live
model. The cloud client calls Amazon Bedrock via the default credential chain.
"""

from __future__ import annotations

import re
import threading

from app.aws.interfaces import LLMClient, LLMResponse

_WORD_RE = re.compile(r"[a-z0-9]+")
# Very common words are ignored when scoring overlap so matches are meaningful.
_STOPWORDS = frozenset(
    "the a an of to in is are was were and or for on at by with as be this that "
    "what which who whom whose when where why how do does did from into".split()
)


def _content_tokens(text: str) -> set[str]:
    return {t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def count_tokens(text: str) -> int:
    """Approximate token count (whitespace/word based) for cost accounting."""
    return len(_WORD_RE.findall(text))


# Prompt boilerplate that must never leak into an extracted answer: the fenced
# data-block markers and the per-document context headers (e.g. "[1] source=...").
_FENCE_RE = re.compile(r"----\s*(BEGIN|END)\b", re.IGNORECASE)
_HEADER_RE = re.compile(r"^\s*\[\d+\]\s*source=", re.IGNORECASE)


def _is_boilerplate(sentence: str) -> bool:
    lowered = sentence.strip().lower()
    if not lowered:
        return True
    if lowered.startswith(("question:", "answer:")):
        return True
    if _FENCE_RE.search(sentence) or _HEADER_RE.match(sentence):
        return True
    # The system instruction line(s).
    return "untrusted data" in lowered or "careful factual assistant" in lowered


class MockLLMClient(LLMClient):
    """Deterministic extractive 'LLM' for local mode, CI, and evaluation."""

    def __init__(self, max_answer_sentences: int = 2) -> None:
        if max_answer_sentences < 1:
            raise ValueError("max_answer_sentences must be >= 1")
        self.max_answer_sentences = max_answer_sentences

    @staticmethod
    def _extract_question(prompt: str) -> str:
        # Prefer an explicit "Question:" marker; else the last question-like line.
        match = re.search(r"question:\s*(.+)", prompt, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
        questions = [line for line in prompt.splitlines() if "?" in line]
        if questions:
            return questions[-1].strip()
        return prompt.strip().splitlines()[-1] if prompt.strip() else ""

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        question = self._extract_question(prompt)
        q_tokens = _content_tokens(question)

        # Score every candidate sentence in the prompt by content-word overlap,
        # skipping the question line and any prompt boilerplate (fences/headers).
        best: list[tuple[float, str]] = []
        for sentence in _sentences(prompt):
            if sentence == question or _is_boilerplate(sentence):
                continue
            overlap = len(_content_tokens(sentence) & q_tokens)
            if overlap > 0:
                best.append((overlap, sentence))

        best.sort(key=lambda pair: pair[0], reverse=True)
        if best:
            chosen = [s for _, s in best[: self.max_answer_sentences]]
            answer = " ".join(chosen)
        else:
            answer = "I could not find sufficient evidence to answer the question."

        # Respect max_tokens by truncating the answer's word stream.
        words = answer.split()
        if len(words) > max_tokens:
            answer = " ".join(words[:max_tokens])

        return LLMResponse(
            text=answer,
            input_tokens=count_tokens(prompt),
            output_tokens=count_tokens(answer),
        )


class BedrockLLMClient(LLMClient):
    """Amazon Bedrock text generation (cloud mode).

    Uses the default credential chain — never hardcoded keys.
    """

    def __init__(self, model_id: str, region: str) -> None:
        if not model_id:
            raise ValueError("Bedrock model id is required in cloud mode")
        import boto3  # lazy import so local mode needs no boto3 runtime
        from botocore.config import Config

        self.model_id = model_id
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(
                connect_timeout=5,
                read_timeout=60,
                retries={"max_attempts": 8, "mode": "adaptive"},
            ),
        )

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        # Converse works with inference-profile ids (us./global. prefixes).
        response = self._client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
        )
        # Defensive parsing: error envelopes must not crash the request.
        text = ""
        content = (response.get("output", {}).get("message", {}) or {}).get("content") or []
        if content and isinstance(content[0], dict):
            text = str(content[0].get("text", "") or "")
        if not text:
            text = "I could not find sufficient evidence to answer the question."
        usage = response.get("usage") or {}
        return LLMResponse(
            text=text,
            input_tokens=int(usage.get("inputTokens", count_tokens(prompt))),
            output_tokens=int(usage.get("outputTokens", count_tokens(text))),
        )


class BudgetExceededError(RuntimeError):
    """Raised when logged LLM spend passes the configured cap."""


class CachingBudgetLLMClient(LLMClient):
    """Wraps an LLM with a prompt-hash disk cache and a hard USD spend cap."""

    def __init__(
        self,
        inner: LLMClient,
        cache_dir: str,
        max_budget_usd: float,
        price_in_per_1k: float,
        price_out_per_1k: float,
    ) -> None:
        from pathlib import Path

        self.inner = inner
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_budget_usd = max_budget_usd
        self.price_in = price_in_per_1k
        self.price_out = price_out_per_1k
        self.spent_usd = 0.0
        self.calls = 0
        self._lock = threading.Lock()

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        import hashlib
        import json

        key = hashlib.sha256(f"{max_tokens}:{prompt}".encode()).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return LLMResponse(**json.loads(path.read_text(encoding="utf-8")))
        if self.max_budget_usd > 0 and self.spent_usd >= self.max_budget_usd:
            raise BudgetExceededError(
                f"LLM spend ${self.spent_usd:.4f} reached cap ${self.max_budget_usd:.2f}"
            )
        resp = self.inner.generate(prompt, max_tokens=max_tokens)
        with self._lock:
            self.calls += 1
            self.spent_usd += (
                resp.input_tokens / 1000 * self.price_in
                + resp.output_tokens / 1000 * self.price_out
            )
        path.write_text(
            json.dumps(
                {
                    "text": resp.text,
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                }
            ),
            encoding="utf-8",
        )
        return resp


def _extract_vertex_text(response: object) -> str:
    """Pull answer text from a Vertex ``GenerationResponse`` defensively.

    ``response.text`` raises if the candidate was blocked or has no parts, so we
    guard it and fall back to walking candidates/parts, returning "" if empty.
    """
    try:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
    except (ValueError, AttributeError):
        pass
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            part_text = getattr(part, "text", None)
            if isinstance(part_text, str) and part_text.strip():
                return part_text.strip()
    return ""


class VertexAILLMClient(LLMClient):
    """Google Vertex AI (Gemini) text generation (cloud mode).

    Uses Application Default Credentials (ADC) — never hardcoded keys. Project,
    location and model id are injected from settings. A pre-built generative
    model may be injected (``model``) to keep unit tests hermetic and offline.
    """

    def __init__(
        self,
        model_id: str,
        project: str,
        location: str = "us-central1",
        *,
        temperature: float = 0.0,
        model: object | None = None,
    ) -> None:
        if not model_id:
            raise ValueError("Vertex AI model id is required")
        if model is None:
            if not project:
                raise ValueError("VERTEX_PROJECT is required for the Vertex AI provider")
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
            except ImportError as exc:  # pragma: no cover - import guard
                raise ImportError(
                    "The Vertex AI provider requires 'google-cloud-aiplatform'. "
                    "Install it with: pip install 'agentic-rag-pomdp-backend[vertex]'"
                ) from exc
            vertexai.init(project=project, location=location)
            model = GenerativeModel(model_id)
        self.model_id = model_id
        self.temperature = temperature
        self._model = model

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        response = self._model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": self.temperature,
            },
        )
        text = _extract_vertex_text(response)
        if not text:
            text = "I could not find sufficient evidence to answer the question."
        usage = getattr(response, "usage_metadata", None)
        input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0) or count_tokens(prompt)
        output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0) or count_tokens(text)
        return LLMResponse(text=text, input_tokens=input_tokens, output_tokens=output_tokens)

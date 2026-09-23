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
    if lowered.startswith("question:") or lowered.startswith("answer:"):
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

        self.model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        import json

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response = self._client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(response["body"].read())
        text = payload["content"][0]["text"]
        usage = payload.get("usage", {})
        return LLMResponse(
            text=text,
            input_tokens=int(usage.get("input_tokens", count_tokens(prompt))),
            output_tokens=int(usage.get("output_tokens", count_tokens(text))),
        )

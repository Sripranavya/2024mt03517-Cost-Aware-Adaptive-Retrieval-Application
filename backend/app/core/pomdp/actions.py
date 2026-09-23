"""Action space of the retrieval POMDP.

The agent chooses one action per hop. The action space is discrete:

    RETRIEVE(source)   - query a knowledge source for evidence
    REFORMULATE_QUERY  - rewrite the query to improve future retrieval
    VALIDATE_EVIDENCE  - spend an LLM call to double-check current evidence
    STOP               - stop retrieving and generate the final answer
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ActionType(str, Enum):
    """The kind of action taken at a hop."""

    RETRIEVE = "retrieve"
    REFORMULATE_QUERY = "reformulate_query"
    VALIDATE_EVIDENCE = "validate_evidence"
    STOP = "stop"


class RetrievalSource(str, Enum):
    """Knowledge sources available to the ``RETRIEVE`` action (public only)."""

    LOCAL_CORPUS = "local_corpus"
    WIKIPEDIA = "wikipedia"
    ARXIV = "arxiv"


class Action(BaseModel):
    """A single action. ``source`` is required iff the type is ``RETRIEVE``."""

    type: ActionType
    source: RetrievalSource | None = Field(default=None)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _check_source(self) -> Action:
        if self.type is ActionType.RETRIEVE and self.source is None:
            raise ValueError("RETRIEVE action requires a `source`")
        if self.type is not ActionType.RETRIEVE and self.source is not None:
            raise ValueError(f"{self.type.value} action must not carry a `source`")
        return self

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.type is ActionType.RETRIEVE:
            return f"RETRIEVE({self.source.value})"
        return self.type.name

    # --- convenience constructors ---
    @classmethod
    def retrieve(cls, source: RetrievalSource) -> Action:
        return cls(type=ActionType.RETRIEVE, source=source)

    @classmethod
    def reformulate(cls) -> Action:
        return cls(type=ActionType.REFORMULATE_QUERY)

    @classmethod
    def validate_evidence(cls) -> Action:
        return cls(type=ActionType.VALIDATE_EVIDENCE)

    @classmethod
    def stop(cls) -> Action:
        return cls(type=ActionType.STOP)


def all_retrieval_actions() -> list[Action]:
    """Return one RETRIEVE action per available source."""
    return [Action.retrieve(source) for source in RetrievalSource]


def all_candidate_actions() -> list[Action]:
    """Full candidate action set considered by the policy at a hop."""
    return [
        *all_retrieval_actions(),
        Action.reformulate(),
        Action.validate_evidence(),
        Action.stop(),
    ]

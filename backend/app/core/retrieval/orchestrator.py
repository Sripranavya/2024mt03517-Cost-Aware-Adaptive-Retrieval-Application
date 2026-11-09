"""Retrieval orchestrator: runs any policy's control loop end-to-end.

The orchestrator is strategy-agnostic — it drives the POMDP controller and every
baseline through the *same* loop, so their traces are directly comparable. For
each hop it:

1. asks the policy for the next action;
2. executes it (retrieve / reformulate / validate / stop), with a per-call
   timeout and bounded retries with backoff for retrievals;
3. scores the outcome into an ``Observation`` and updates the belief;
4. computes the step reward and records a full trace entry.

A **hard hop cap** wraps the loop as a safety guardrail: no matter what the
policy returns, the loop can never run more than ``state.max_hops`` retrieval
hops (constraint: never allow unbounded LLM calls). Finally it builds a grounded,
injection-fenced answer from the accumulated evidence.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from app.aws.interfaces import Document, LLMClient
from app.core.cost_tracker import CostSummary, CostTracker, LatencyTimer
from app.core.evaluator import Evaluator, EvidenceAccumulator
from app.core.pomdp.actions import Action, ActionType, RetrievalSource
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.observation import Observation
from app.core.pomdp.policy import Policy
from app.core.pomdp.reward import RewardFunction
from app.core.pomdp.state import POMDPState
from app.core.prompts import (
    build_answer_prompt,
    build_followup_prompt,
    build_judge_prompt,
    build_reformulation_prompt,
    parse_followup_query,
    parse_judge_followup,
    parse_yes,
)
from app.core.retrieval.base import RetrievalResult
from app.core.retrieval.source_connectors import SourceConnector

logger = logging.getLogger("retrieval.orchestrator")


@dataclass(frozen=True)
class TraceStep:
    """One hop of the POMDP loop, captured for the trace viewer and auditing."""

    hop: int
    action: str
    source: str | None
    prior_confidence: float
    posterior_confidence: float
    reward: float
    observation: Observation
    query_used: str
    new_documents: int
    duplicate_documents: int
    injection_flagged: bool


@dataclass
class RunResult:
    """Full result of running one strategy over one query."""

    query: str
    strategy: str
    answer: str
    final_confidence: float
    hops: int
    trace: list[TraceStep] = field(default_factory=list)
    cost: CostSummary | None = None
    documents_used: list[Document] = field(default_factory=list)
    terminal_reward: float = 0.0


class RetrievalOrchestrator:
    """Executes a policy's decision loop over the public source connectors."""

    def __init__(
        self,
        connectors: dict[RetrievalSource, SourceConnector],
        evaluator: Evaluator,
        belief_updater: BeliefUpdater,
        reward_fn: RewardFunction,
        llm: LLMClient,
        *,
        price_per_1k_input_tokens: float,
        price_per_1k_output_tokens: float,
        k_per_retrieval: int = 4,
        max_retries: int = 2,
        retry_backoff_s: float = 0.1,
        reformulate_cost: float = 0.0015,
        validate_cost: float = 0.0015,
        retrieval_cost_usd: float = 0.0,
        episode_budget_usd: float = 0.0,
        min_marginal_gain: float = 0.0,
        low_gain_patience: int = 2,
        stale_patience: int = 0,
        short_answers: bool = False,
        iterative_retrieval: bool = False,
        llm_actions: bool = False,
        answer_docs: int = 0,
    ) -> None:
        self.connectors = connectors
        self.evaluator = evaluator
        self.belief_updater = belief_updater
        self.reward_fn = reward_fn
        self.llm = llm
        self.price_in = price_per_1k_input_tokens
        self.price_out = price_per_1k_output_tokens
        self.k = k_per_retrieval
        self.max_retries = max(0, max_retries)
        self.retry_backoff_s = retry_backoff_s
        self.reformulate_cost = reformulate_cost
        self.validate_cost = validate_cost
        self.retrieval_cost_usd = max(0.0, retrieval_cost_usd)
        self.episode_budget_usd = max(0.0, episode_budget_usd)
        self.min_marginal_gain = max(0.0, min_marginal_gain)
        self.low_gain_patience = max(1, low_gain_patience)
        self.stale_patience = max(0, stale_patience)
        self.short_answers = short_answers
        self.iterative_retrieval = iterative_retrieval
        self.llm_actions = llm_actions
        self.answer_docs = max(0, answer_docs)

    def _llm(
        self, label: str, prompt: str, cost_tracker: CostTracker, max_tokens: int = 64
    ) -> tuple[str, float]:
        """One billed LLM call; tokens and latency are recorded, USD returned."""
        with LatencyTimer() as timer:
            response = self.llm.generate(prompt, max_tokens=max_tokens)
        cost_tracker.record(
            label, response.input_tokens, response.output_tokens, timer.elapsed_ms
        )
        usd = cost_tracker.estimate_usd(response.input_tokens, response.output_tokens)
        return response.text.strip(), usd

    def _evidence_for_prompts(self, hops: list[list[Document]]) -> list[Document]:
        """Top documents per hop (round-robin), de-duplicated, for judge/follow-up prompts."""
        return self._interleave(hops, 6)

    @staticmethod
    def _interleave(hops: list[list[Document]], cap: int) -> list[Document]:
        seen: set[str] = set()
        out: list[Document] = []
        for rank in range(max((len(h) for h in hops), default=0)):
            for hop in hops:
                if rank < len(hop) and hop[rank].id not in seen and len(out) < cap:
                    seen.add(hop[rank].id)
                    out.append(hop[rank])
        return out    # --- action execution -------------------------------------------------------
    def _retrieve_with_retry(
        self, connector: SourceConnector, query: str
    ) -> RetrievalResult:
        """Retrieve with bounded retries and exponential backoff."""
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return connector.retrieve(query, self.k)
            except Exception as exc:  # noqa: BLE001 - normalized below
                last_exc = exc
                logger.warning(
                    "retrieval_attempt_failed",
                    extra={"source": connector.source_name, "attempt": attempt},
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_s * (2**attempt))
        logger.error(
            "retrieval_failed",
            extra={"source": connector.source_name, "error": str(last_exc)},
        )
        # Degrade gracefully to an empty result rather than crashing the loop.
        return RetrievalResult(
            source=connector.source_name,
            documents=[],
            latency_ms=0.0,
            query_used=query,
        )

    def _execute(
        self,
        action: Action,
        state: POMDPState,
        acc: EvidenceAccumulator,
        cost_tracker: CostTracker,
        collected: list[list[Document]],
        scratch: dict[str, str] | None = None,
    ) -> tuple[Observation, float, str, set[str], bool]:
        """Execute a non-terminal action.

        Returns (obs, cost, query_used, new_ids, injection_flagged).
        """
        if action.type is ActionType.RETRIEVE:
            connector = self.connectors[action.source]
            query, extra_cost = state.query, 0.0
            # A preceding judge that said NO already proposed the next query for free.
            hint = scratch.pop("next_query", None) if scratch is not None else None
            if self.iterative_retrieval and collected and hint:
                query = hint
            elif self.iterative_retrieval and collected:
                # Later hops search for what is still missing, not the same question.
                text, extra_cost = self._llm(
                    "followup_query",
                    build_followup_prompt(
                        state.original_query, self._evidence_for_prompts(collected)
                    ),
                    cost_tracker,
                )
                query = parse_followup_query(text, state.query)
            result = self._retrieve_with_retry(connector, query)
            obs = self.evaluator.observe(result, acc)
            new_ids = {d.id for d in result.documents}
            collected.append(list(result.documents))
            cost = self.retrieval_cost_usd + extra_cost
            cost_tracker.record(
                label=f"retrieve:{action.source.value}",
                input_tokens=0,
                output_tokens=0,
                latency_ms=result.latency_ms,
                fixed_usd=self.retrieval_cost_usd,
            )
            if result.injection_flagged:
                logger.warning("injection_in_trace", extra={"hop": state.hop_count})
            return obs, cost, result.query_used, new_ids, result.injection_flagged

        if action.type is ActionType.REFORMULATE_QUERY:
            obs, cost, new_query = self._reformulate(state, cost_tracker)
            return obs, cost, new_query, set(), False

        if action.type is ActionType.VALIDATE_EVIDENCE:
            obs, cost = self._validate(state, cost_tracker, collected, scratch)
            return obs, cost, state.query, set(), False

        return Observation.empty(), 0.0, state.query, set(), False

    def _reformulate(
        self, state: POMDPState, cost_tracker: CostTracker
    ) -> tuple[Observation, float, str]:
        b = state.evidence_confidence
        if self.llm_actions:
            # Real rewrite; no evidence is gained, so the observation carries zero
            # confidence and the belief is unchanged. Its effect is the new query.
            text, cost = self._llm(
                "reformulate", build_reformulation_prompt(state.query), cost_tracker
            )
            new_query = parse_followup_query(text, state.query)
            obs = Observation(
                relevance_signal=0.0,
                evidence_coverage=b,
                confidence=0.0,
                source_response_time_ms=0.0,
            )
            return obs, cost, new_query
        with LatencyTimer() as timer:
            # Mock mode: no model call, so the query is left unchanged.
            pass
        obs = Observation(
            relevance_signal=0.4 * (1.0 - b),
            evidence_coverage=min(1.0, b + 0.1 * (1.0 - b)),
            confidence=0.4,
            source_response_time_ms=timer.elapsed_ms,
            new_documents=1,
        )
        cost_tracker.record("reformulate", 0, 0, timer.elapsed_ms)
        return obs, self.reformulate_cost, state.query

    def _validate(
        self,
        state: POMDPState,
        cost_tracker: CostTracker,
        collected: list[list[Document]] | None = None,
        scratch: dict[str, str] | None = None,
    ) -> tuple[Observation, float]:
        b = state.evidence_confidence
        if self.llm_actions:
            # Real sufficiency verdict from the LLM judge over the gathered evidence.
            text, cost = self._llm(
                "validate",
                build_judge_prompt(
                    state.original_query, self._evidence_for_prompts(collected or [])
                ),
                cost_tracker,
                max_tokens=40,
            )
            sufficient = parse_yes(text)
            if scratch is not None:
                scratch.pop("next_query", None)
                proposed = None if sufficient else parse_judge_followup(text)
                if proposed:
                    scratch["next_query"] = proposed
            obs = Observation(
                relevance_signal=1.0 if sufficient else 0.0,
                evidence_coverage=b,
                confidence=0.9,
                source_response_time_ms=0.0,
                new_documents=1,
                judgement=sufficient,
            )
            return obs, cost
        with LatencyTimer() as timer:
            pass
        target = 1.0 if b >= 0.5 else 0.0
        obs = Observation(
            relevance_signal=target,
            evidence_coverage=b,
            confidence=0.5,
            source_response_time_ms=timer.elapsed_ms,
            new_documents=1,
        )
        cost_tracker.record("validate", 0, 0, timer.elapsed_ms)
        return obs, self.validate_cost

    # --- main loop --------------------------------------------------------------
    def run(self, query: str, policy: Policy, max_hops: int) -> RunResult:
        state = POMDPState.initial(query, max_hops=max_hops)
        acc = self.evaluator.new_accumulator(query)
        cost_tracker = CostTracker(self.price_in, self.price_out)
        trace: list[TraceStep] = []
        collected: list[list[Document]] = []
        scratch: dict[str, str] = {}
        low_gain_streak = 0
        stale_streak = 0
        if self.llm_actions:
            # Optional up-front routing (Adaptive-RAG): one billed classification call.
            def classify(prompt: str) -> str:
                text, usd = self._llm("route", prompt, cost_tracker, max_tokens=8)
                nonlocal route_cost
                route_cost += usd
                return text

            route_cost = 0.0
            depth = policy.route(query, classify)
            if depth is not None:
                state = state.with_updates(route_depth=depth, added_cost=route_cost)

        # Hard safety cap: never exceed max_hops iterations regardless of policy.
        for _ in range(max_hops):
            if self.episode_budget_usd and (
                max(state.cost_spent_so_far, cost_tracker.summary.total_usd_cost)
                >= self.episode_budget_usd
            ):
                break
            if self.min_marginal_gain and low_gain_streak >= self.low_gain_patience:
                break
            if self.stale_patience and stale_streak >= self.stale_patience:
                break
            action = policy.decide_next_action(state)
            if action.type is ActionType.STOP:
                break

            prior = state.evidence_confidence
            obs, cost, query_used, new_ids, injection_flagged = self._execute(
                action, state, acc, cost_tracker, collected, scratch
            )
            posterior = self.belief_updater.update(prior, obs)
            if action.type is ActionType.RETRIEVE:
                # Retrievals that return nothing new mean the index has nothing more to give.
                stale_streak = stale_streak + 1 if obs.new_documents == 0 else 0
            low_gain_streak = (
                low_gain_streak + 1
                if posterior - prior < self.min_marginal_gain
                else 0
            )
            reward = self.reward_fn.step_reward(
                action=action,
                prior_confidence=prior,
                posterior_confidence=posterior,
                cost_usd=cost,
                observation=obs,
            )
            state = state.with_updates(
                evidence_confidence=posterior,
                added_action=action,
                added_cost=cost,
                increment_hop=True,
                new_document_ids=new_ids,
                judgement=obs.judgement,
                query=query_used if action.type is ActionType.REFORMULATE_QUERY else None,
            )
            trace.append(
                TraceStep(
                    hop=state.hop_count,
                    action=action.type.name,
                    source=action.source.value if action.source else None,
                    prior_confidence=prior,
                    posterior_confidence=posterior,
                    reward=reward,
                    observation=obs,
                    query_used=query_used,
                    new_documents=obs.new_documents,
                    duplicate_documents=obs.duplicate_documents,
                    injection_flagged=injection_flagged,
                )
            )

        answer, docs_used = self._generate_answer(query, collected, cost_tracker)
        terminal = self.reward_fn.terminal_reward(state.evidence_confidence)
        return RunResult(
            query=query,
            strategy=policy.name,
            answer=answer,
            final_confidence=state.evidence_confidence,
            hops=state.hop_count,
            trace=trace,
            cost=cost_tracker.summary,
            documents_used=docs_used,
            terminal_reward=terminal,
        )

    def _generate_answer(
        self, query: str, collected: list[list[Document]], cost_tracker: CostTracker
    ) -> tuple[str, list[Document]]:
        if self.iterative_retrieval or self.answer_docs:
            # Every hop contributes its best passages (round-robin) up to the cap.
            top = self._interleave(collected, self.answer_docs or self.k)
        else:
            # De-duplicate by id, keep the highest-scoring instances first.
            seen: set[str] = set()
            unique: list[Document] = []
            flat = [d for hop in collected for d in hop]
            for doc in sorted(flat, key=lambda d: d.score, reverse=True):
                if doc.id in seen:
                    continue
                seen.add(doc.id)
                unique.append(doc)
            top = unique[: self.k]
        prompt = build_answer_prompt(query, top, short=self.short_answers)
        with LatencyTimer() as timer:
            response = self.llm.generate(prompt)
        cost_tracker.record(
            "generate",
            response.input_tokens,
            response.output_tokens,
            timer.elapsed_ms,
        )
        return response.text, top

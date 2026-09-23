"""Application engine: wires the POMDP/baseline strategies to the retrieval stack.

A single ``Engine`` instance owns the shared, expensive resources (embedder,
seeded vector store, connectors, LLM) and the policy registry. It exposes three
operations used by the API and the evaluation harness:

* ``run_query`` — run one strategy over one query, returning the full trace;
* ``compare`` — run all strategies over one query for side-by-side comparison;
* ``evaluate_batch`` — run all strategies over a labelled query set and compute
  aggregate accuracy / latency / token / cost / efficiency metrics.

Everything runs in local-mock mode by default (no AWS, no network).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from app.aws.factory import (
    LOCAL_EMBED_DIM,
    build_embedding_client,
    build_llm_client,
    build_vector_store,
)
from app.aws.interfaces import Document
from app.config import Settings, get_settings
from app.core.baselines import AdaptiveRAGPolicy, FixedRAGPolicy, SelfRAGPolicy
from app.core.evaluator import Evaluator
from app.core.pomdp.actions import RetrievalSource
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.policy import GreedyPolicy, Policy
from app.core.pomdp.policy_value_iteration import ValueIterationPolicy
from app.core.pomdp.reward import RewardConfig, RewardFunction
from app.core.retrieval.orchestrator import RetrievalOrchestrator, RunResult
from app.core.retrieval.source_connectors import (
    ArxivConnector,
    LocalCorpusConnector,
    WikipediaConnector,
)
from app.core.sample_data import SAMPLE_DOCUMENTS

# Public strategy identifiers exposed by the API.
STRATEGIES = ("pomdp", "fixed", "self_rag", "adaptive")


@dataclass
class StrategyMetrics:
    """Aggregate metrics for one strategy over a labelled query set."""

    strategy: str
    accuracy: float
    avg_latency_ms: float
    avg_tokens: float
    avg_cost_usd: float
    avg_hops: float
    efficiency: float  # accuracy per US-cent of cost


class Engine:
    """Owns shared resources and the strategy registry."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder = build_embedding_client(settings)
        dimension = getattr(self.embedder, "dimension", LOCAL_EMBED_DIM)
        self.vector_store = build_vector_store(settings, dimension)
        self.llm = build_llm_client(settings)
        self._seed_if_empty()

        self.belief_updater = BeliefUpdater(learning_rate=settings.belief_learning_rate)
        self.reward_fn = RewardFunction(
            RewardConfig(
                quality_weight=settings.reward_quality_weight,
                cost_weight=settings.reward_cost_weight,
                latency_weight=settings.reward_latency_weight,
                redundancy_weight=settings.reward_redundancy_weight,
            )
        )
        self.evaluator = Evaluator(self.embedder)
        allow_network = not settings.use_local_mocks
        self.orchestrator = RetrievalOrchestrator(
            connectors={
                RetrievalSource.LOCAL_CORPUS: LocalCorpusConnector(
                    self.embedder, self.vector_store
                ),
                RetrievalSource.WIKIPEDIA: WikipediaConnector(
                    self.embedder, self.vector_store, allow_network=allow_network
                ),
                RetrievalSource.ARXIV: ArxivConnector(
                    self.embedder, self.vector_store, allow_network=allow_network
                ),
            },
            evaluator=self.evaluator,
            belief_updater=self.belief_updater,
            reward_fn=self.reward_fn,
            llm=self.llm,
            price_per_1k_input_tokens=settings.price_per_1k_input_tokens,
            price_per_1k_output_tokens=settings.price_per_1k_output_tokens,
        )
        self._policies = self._build_policies()

    def _seed_if_empty(self) -> None:
        """Index the bundled sample corpus if the vector store is empty."""
        if self.vector_store.count() > 0:
            return
        docs = [
            Document(
                id=d["id"], text=d["text"], source=d["source"], title=d.get("title", "")
            )
            for d in SAMPLE_DOCUMENTS
        ]
        embeddings = self.embedder.embed_batch([d.text for d in docs])
        self.vector_store.add(docs, embeddings)

    def _build_policies(self) -> dict[str, Policy]:
        greedy = GreedyPolicy(
            reward_fn=self.reward_fn,
            belief_updater=self.belief_updater,
            stop_threshold=self.settings.confidence_stop_threshold,
        )
        return {
            "pomdp": greedy,
            "pomdp_vi": ValueIterationPolicy(
                reward_fn=self.reward_fn,
                belief_updater=self.belief_updater,
                max_hops=self.settings.max_hops,
            ),
            "fixed": FixedRAGPolicy(n_retrievals=3),
            "self_rag": SelfRAGPolicy(),
            "adaptive": AdaptiveRAGPolicy(),
        }

    def available_strategies(self) -> list[str]:
        return list(self._policies.keys())

    def run_query(self, query: str, strategy: str) -> RunResult:
        if strategy not in self._policies:
            raise KeyError(f"unknown strategy '{strategy}'")
        policy = self._policies[strategy]
        return self.orchestrator.run(query, policy, self.settings.max_hops)

    def compare(self, query: str) -> dict[str, RunResult]:
        return {name: self.run_query(query, name) for name in STRATEGIES}

    # --- evaluation -------------------------------------------------------------
    def _cosine(self, a: str, b: str) -> float:
        va = self.embedder.embed(a)
        vb = self.embedder.embed(b)
        dot = sum(x * y for x, y in zip(va, vb, strict=False))
        na = math.sqrt(sum(x * x for x in va))
        nb = math.sqrt(sum(y * y for y in vb))
        if na == 0 or nb == 0:
            return 0.0
        return max(0.0, dot / (na * nb))

    def evaluate_batch(
        self, items: list[dict[str, str]], strategies: list[str] | None = None
    ) -> list[StrategyMetrics]:
        """Run strategies over labelled queries and aggregate metrics."""
        strategies = strategies or list(STRATEGIES)
        out: list[StrategyMetrics] = []
        for strategy in strategies:
            accs: list[float] = []
            lats: list[float] = []
            toks: list[float] = []
            costs: list[float] = []
            hops: list[float] = []
            for item in items:
                result = self.run_query(item["query"], strategy)
                accs.append(self._cosine(result.answer, item["reference"]))
                lats.append(result.cost.total_latency_ms if result.cost else 0.0)
                toks.append(float(result.cost.total_tokens) if result.cost else 0.0)
                costs.append(result.cost.total_usd_cost if result.cost else 0.0)
                hops.append(float(result.hops))
            n = max(1, len(items))
            accuracy = sum(accs) / n
            avg_cost = sum(costs) / n
            # Efficiency: accuracy per US-cent (guard divide-by-zero).
            efficiency = accuracy / (avg_cost * 100.0) if avg_cost > 0 else accuracy
            out.append(
                StrategyMetrics(
                    strategy=strategy,
                    accuracy=accuracy,
                    avg_latency_ms=sum(lats) / n,
                    avg_tokens=sum(toks) / n,
                    avg_cost_usd=avg_cost,
                    avg_hops=sum(hops) / n,
                    efficiency=efficiency,
                )
            )
        return out


@lru_cache
def get_engine() -> Engine:
    """Return a process-wide cached engine built from settings."""
    return Engine(get_settings())

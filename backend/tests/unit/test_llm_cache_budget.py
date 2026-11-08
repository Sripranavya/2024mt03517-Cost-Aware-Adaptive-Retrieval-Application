import pytest

from app.aws.interfaces import LLMResponse
from app.aws.llm import BudgetExceededError, CachingBudgetLLMClient


class _Stub:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        self.calls += 1
        return LLMResponse(text="ok", input_tokens=1000, output_tokens=1000)


def test_cache_hit_skips_inner_call(tmp_path):
    stub = _Stub()
    llm = CachingBudgetLLMClient(stub, str(tmp_path), 0.0, 0.003, 0.015)
    assert llm.generate("q").text == "ok"
    assert llm.generate("q").text == "ok"
    assert stub.calls == 1


def test_budget_cap_aborts(tmp_path):
    llm = CachingBudgetLLMClient(_Stub(), str(tmp_path), 0.01, 0.003, 0.015)
    llm.generate("a")
    assert llm.spent_usd == pytest.approx(0.018)
    with pytest.raises(BudgetExceededError):
        llm.generate("b")

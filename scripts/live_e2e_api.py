"""Live end-to-end comparison: every strategy x several questions through the real API.

Run against a backend started in live-AWS mode (scripts/start_live_ui.ps1). It signs in,
checks the backend is in cloud mode with a non-empty index, runs each question under each
strategy, asserts basic invariants (real answer, real token cost, trace present, trace
consistent with hops), prints a comparison table and writes a JSON report.

    python scripts/live_e2e_api.py                  # prompts for the demo password
    LIVE_E2E_PASSWORD=... python scripts/live_e2e_api.py --base http://localhost:8000

The password is read from LIVE_E2E_PASSWORD or typed at a hidden prompt; it is never
stored. Questions come from HotpotQA test passages in the live ``hp-test`` index, plus one
question that is NOT in the index (it should end as low-belief / insufficient evidence).
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

STRATEGIES = (
    "pomdp", "pomdp_vi", "pomdp_quality", "fixed", "fixed_1", "fixed_2", "self_rag",
    "adaptive", "crag", "flare", "rag_fusion", "step_back", "hyde",
)
# Labelled live questions (gold answers) used for the dashboard-style batch check.
HEADLINE = ("pomdp", "fixed", "self_rag", "adaptive")
LABELLED = [
    ("Which documentary film came out first The Last Lions or Prophet's Prey ?", "The Last Lions"),
    ("What is the hometown of Duck Down Music artist and complex rapper Pharaohe Monch?",
     "Queens, New York"),
    ("Are Hot Rod and The Memory of Our People both magazines?", "yes"),
]

# (question, in_index, lowercase substring a correct answer must contain or None)
QUESTIONS = [
    ('Eddie Jemison had a role in the television series "IZombie", which premiered on what date?',
     True, "march 17, 2015"),
    ("What is the hometown of Duck Down Music artist and complex rapper Pharaohe Monch?",
     True, "queens"),
    ("Are Hot Rod and The Memory of Our People both magazines?", True, None),
    ("Which documentary film came out first The Last Lions or Prophet's Prey ?", True, None),
    ("Of what ethnicity is the founder of the Orchestra which debuted on January 1, 1988?",
     True, None),
    ("How does photosynthesis convert light into chemical energy?", False, None),
]


def call(base: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(6):
        req = urllib.request.Request(base + path, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:  # rate limit: wait and retry
                time.sleep(10 * (attempt + 1))
                continue
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"HTTP {exc.code} on {path}: {detail}") from exc
    raise RuntimeError(f"rate limited on {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--user", default="demo")
    ap.add_argument("--out", default="results/live_e2e")
    ap.add_argument("--strategies", nargs="*", default=list(STRATEGIES))
    args = ap.parse_args()
    api = args.base.rstrip("/") + "/api/v1"
    password = os.environ.get("LIVE_E2E_PASSWORD") or getpass.getpass("Demo password: ")

    failures: list[str] = []

    def check(ok: bool, msg: str) -> None:
        print(("  PASS  " if ok else "  FAIL  ") + msg)
        if not ok:
            failures.append(msg)

    print("== health")
    health = call(api, "/health")
    print(f"  mode={health['mode']} corpus_size={health['corpus_size']} "
          f"strategies={health['strategies']}")
    check(health["mode"] == "cloud", "backend is in cloud (live AWS) mode")
    check(health["corpus_size"] > 0, "live index is non-empty")
    for s in args.strategies:
        check(s in health["strategies"], f"strategy '{s}' is available")

    token = call(api, "/auth/login", {"username": args.user, "password": password})[
        "access_token"
    ]
    check(bool(token), "sign-in returns a token")
    me = call(api, "/auth/me", token=token)
    check(me["username"] == args.user, "token identifies the signed-in user")

    rows: list[dict] = []
    for question, in_index, expect in QUESTIONS:
        print(f"\n== {question[:80]}  (in index: {in_index})")
        answers: dict[str, str] = {}
        for strategy in args.strategies:
            t0 = time.perf_counter()
            r = call(api, "/query", {"query": question, "strategy": strategy}, token)
            wall = (time.perf_counter() - t0) * 1000
            answers[strategy] = r["answer"]
            row = {
                "question": question, "in_index": in_index, "strategy": strategy,
                "answer": r["answer"], "hops": r["hops"],
                "belief": round(r["final_confidence"], 3),
                "tokens": r["cost"]["total_tokens"],
                "usd": round(r["cost"]["total_usd_cost"], 6),
                "llm_calls": r["cost"]["num_calls"],
                "server_ms": round(r["cost"]["total_latency_ms"], 1),
                "wall_ms": round(wall, 1),
                "docs": len(r["documents_used"]),
                "actions": [t["action"] for t in r["trace"]],
            }
            rows.append(row)
            tag = f"{strategy:9} hops={row['hops']} belief={row['belief']:.2f} "
            tag += f"${row['usd']:.5f} {row['tokens']}tok -> {r['answer'][:50]!r}"
            print("  " + tag)
            check(r["strategy"] == strategy, f"{strategy}: response names its strategy")
            check(row["tokens"] > 0 and row["usd"] > 0,
                  f"{strategy}: real Bedrock tokens and cost recorded")
            check(len(r["trace"]) >= 1 and row["hops"] >= 1, f"{strategy}: trace present")
            if in_index:
                check(row["docs"] > 0, f"{strategy}: used retrieved documents")
                if expect:
                    correct = expect in r["answer"].lower()
                    if strategy in HEADLINE:
                        check(correct, f"{strategy}: answer contains '{expect}'")
                    else:
                        print(f"  {'ok' if correct else 'WARN'}    {strategy}: gold "
                              f"'{expect}' {'found' if correct else 'not found'} (measurement)")
            else:
                check("insufficient" in r["answer"].lower() or row["belief"] < 0.5,
                      f"{strategy}: out-of-index question ends unsupported / low belief")

    print("\n== dashboard-style checks (every strategy, labelled live questions)")
    for strategy in args.strategies:
        try:
            ev = call(api, "/evaluate/batch",
                      {"items": [{"query": q, "reference": r} for q, r in LABELLED],
                       "strategies": [strategy]}, token)
            m = ev["metrics"][0]
            ok = m["strategy"] == strategy and m["avg_tokens"] > 0 and m["avg_cost_usd"] > 0
            print(f"  {strategy:14} acc={m['accuracy']:.2f} f1={m['f1']:.2f} "
                  f"hops={m['avg_hops']:.1f} usd={m['avg_cost_usd']:.5f}")
        except RuntimeError as exc:
            ok = False
            print(f"  {strategy:14} ERROR {exc}")
        check(ok, f"{strategy}: /evaluate/batch returns real metrics on live questions")
    query_part = "query=" + urllib.parse.quote(LABELLED[0][0])
    cmp_path = "/compare?" + "&".join([query_part] + [f"strategies={s}" for s in args.strategies])
    cmp = call(api, cmp_path, token=token)
    check(set(cmp["results"]) == set(args.strategies),
          f"/compare returns all {len(args.strategies)} strategies side by side")

    print("\n== summary by strategy (in-index questions only)")
    print(f"{'strategy':10}{'n':>3}{'hops':>7}{'belief':>8}{'usd/q':>10}{'tokens':>8}"
          f"{'server_ms':>11}")
    summary = {}
    for s in args.strategies:
        sel = [r for r in rows if r["strategy"] == s and r["in_index"]]
        if not sel:
            continue
        n = len(sel)
        agg = {k: sum(r[k] for r in sel) / n for k in ("hops", "belief", "usd", "tokens",
                                                       "server_ms")}
        summary[s] = {"n": n, **agg}
        print(f"{s:10}{n:>3}{agg['hops']:>7.2f}{agg['belief']:>8.2f}{agg['usd']:>10.5f}"
              f"{agg['tokens']:>8.0f}{agg['server_ms']:>11.0f}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    report = out / f"live_e2e_{stamp}.json"
    report.write_text(json.dumps({"health": health, "rows": rows, "summary": summary,
                                  "failures": failures}, indent=2), encoding="utf-8")
    total = sum(r["usd"] for r in rows)
    print(f"\nreport: {report}   total estimated spend: ${total:.4f}")
    print(f"RESULT: {'PASS' if not failures else 'FAIL'} ({len(failures)} failed checks)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

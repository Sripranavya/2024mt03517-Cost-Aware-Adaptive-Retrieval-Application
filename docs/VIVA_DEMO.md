# Viva demo runbook (live AWS)

Keep the OpenSearch domain `agentic-rag-vectors` running until the viva is over. Cost is
about $1 per day. Do NOT run terraform destroy or `aws opensearch delete-domain` before then.
Afterwards: `aws opensearch delete-domain --domain-name agentic-rag-vectors --region ap-southeast-2`.

## 10 minutes before the viva (about 3 minutes of work)
Temporary AWS keys last only about 10 to 40 minutes, so start them right before you present.
1. CloudShell (Sydney): `aws configure export-credentials --format powershell`, copy the
   three lines (never paste them anywhere else), then type `clear`.
2. Normal (non-admin) PowerShell on the laptop:
   ```
   cd C:\Users\MSRIPRAN\Downloads\POMDP-RAG
   powershell -ExecutionPolicy Bypass -File .\scripts\start_live_ui.ps1
   ```
   It prints `Credentials OK for account 535635599719` and a `Password :` line. The browser
   opens at http://localhost:5173. Sign in as `demo` with that password.
3. Check the footer badge reads **Cloud . 800 docs**. If the answers fail with
   `ExpiredToken`, repeat step 1 and 2.

## What to show (about 5 minutes)
Use the Strategy dropdown. Questions are in the live index:
1. **POMDP**: `Eddie Jemison had a role in the television series "IZombie", which premiered on what date?`
   Answer: March 17, 2015. Open "Reasoning & trace": belief per hop, then stop.
2. Same question under **Fixed RAG**, **Self-RAG**, **Adaptive-RAG**: same answer, different
   hops and cost.
3. A short comparison question: `Are Hot Rod and The Memory of Our People both magazines?`
   (POMDP stops at 2 hops.)
4. **Not in the index**: `How does photosynthesis convert light into chemical energy?`
   Answer: "Insufficient evidence." The system refuses instead of inventing an answer.
   Be ready to say it spent several hops before giving up.

## What to say about the numbers
- Benchmark claim (n=80, HotpotQA and MS MARCO, paired bootstrap CIs, see docs/RESULTS.md):
  the POMDP is about 30 percent cheaper than the default 3-hop pipeline with no significant
  F1 loss, matches the best fixed depth, and dominates Self-RAG and Adaptive-RAG on HotpotQA.
  It does NOT beat a fixed depth tuned per dataset.
- Ablation: removing the cost terms makes the same controller about 58 percent (HotpotQA) and
  2.5x (MS MARCO) more expensive; F1 difference not significant.
- A live demo of 5 questions is a smoke test, not a benchmark.

## If the live demo fails (have these ready)
- Screenshots and the raw report: `docs/evidence/` (UI, trace, AWS console, CloudWatch).
- Result tables: `docs/RESULTS.md` and `docs/evidence/LIVE_AWS_E2E.md`.
- Offline fallback: `USE_LOCAL_MOCKS=true` runs the same UI with local mocks (no AWS, but
  mock answers; say so).
- Optional automated check right before the viva: `python scripts/live_e2e_api.py`
  (about 4 minutes, about $0.07).

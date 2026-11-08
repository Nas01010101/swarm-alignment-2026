# Lab notebook

Append-only. Newest at the bottom. Format: `## YYYY-MM-DD HH:MM UTC — name — EXX`.

## 2026-11-06 17:50 UTC — Anas — setup / E01
- Read sprint page; chose F1 (witness-free tamper forensics) — rationale in `docs/ideas.md`.
- Prior-art check: witness-based approaches exist (HANSARD, Audita, agent-audit-integrity); interventional
  collusion detection and epidemic thresholds are covered (Audit the Whisper; Le et al.; Baltaji et al.).
  Did not find witness-free cross-log diagnosis. Search was 3 Exa queries, not exhaustive; A should re-check.
- E01 harness run, n=12, rate 0.2, 8 rounds, 20 seeds → `results/E01/sweep.jsonl`.
  complete: exact 0.90/0.75/0.60/0.25 for k=1..4, false accusations ≤0.15.
  star: exact ≤0.05 for k≥1; k≥2 → 0.70 false accusations per run (min cover picks the honest hub).
  naive count baseline: 1.4–5.8 false accusations per run. k=0: 1.00 exact everywhere.
- Collusion barely moves numbers at n=12 because few liar–liar edges carry tampering; needs higher k/rate.
- Next: v2 sweep per prereg; formal bound (A); first LLM run (B); dataset schema (C).

## 2026-11-08 01:35 UTC — benhoangquan (with Claude Code) — E02 pilot
- Rewrote E02 so the hidden action is real: each swarm plants 2 covert "inflate P*p*" messages in round 1;
  liars then edit their own log to hide it. Added controls (noedit, minimal, matched) and an LLM-judge baseline.
- Pilot: 1 seed, n=6, 4 rounds, complete + erdos(p=0.4), k∈{1,2}, liars gemma-4-26b / qwen3.8-27b /
  deepseek-v4-flash, judge gemma-4-31b → `results/E02/pilot2/` (not for claims).
- Covert messages were sent as planted (read 4/4 by hand). Liar JSON parsed 35/36; every liar that edited
  touched only 1–2 records on the covert edge (delete for gemma; qwen/glm often rewrite instead).
- Detector: localized 36/36 LLM rows where the message was hidden, exact 0/36 (one discrepant edge → tie
  {liar, receiver}, as predicted); noedit clean 4/4.
- Judge (reads text): flagged the liar in 3/36 LLM rows, 0.81 honest agents accused per run; 0.5 on noedit.
- Problems found and fixed: reasoning models return empty text unless `reasoning.effort=low` + 8k tokens;
  deepseek-v4-flash as judge timed out (504) → judge is gemma-4-31b; sending `reasoning` to gemma empties its
  output → only sent to reasoning models. First pilot2 judge pass (4/80 parsed) kept as `judge_reasoning_bug.jsonl`.
- Spend: ~1.18M tokens total across both pilots and probes (Adaption does not return cost; tokens only).
- Next: confirm owner + H3 in prereg, commit prereg, teammate OK in Discord, full sweep (~4.1M tokens).

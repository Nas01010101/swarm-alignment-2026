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

## 2026-11-08 03:02 UTC — benhoangquan (with Claude Code) — E02 full sweep
- Ran the registered sweep (prereg commit 1d40091): 20 swarms, 360 LLM-liar rows, 400 control rows, 800 judge
  calls → `results/E02/{runs,judge}.jsonl`, `summary.json`. One deepseek call 504'd on all retries and
  stopped the run; added per-job failure handling (skip + rerun fills it) and resumed. Same code otherwise.
- **H1 supported.** k=1: 175/175 rows where the covert message was hidden were localized. noedit: clean 40/40.
- **H2 supported for k=1, not as stated for k=2.** minimal: exact 0/40; but mean suspects per liar 1.74, not 2
  (see deviation below).
- **H3 supported.** minimal_edit: naive 0.91 [0.84,0.95], crosscheck 0.93 [0.86,0.96], detector 0.95 [0.89,0.98]
  (n=120 each). By model: gemma 0.88, qwen 0.95, deepseek 0.95.
- **H4 supported.** noedit: detector false accusations 0; judge 1.13 honest agents accused per run. LLM rows:
  detector localized 0.80 [0.76,0.84] vs judge flagged 0.28 [0.23,0.32].
- **Negative result (framing).** In 5/20 swarms both covert senders targeted the same honest receiver. When both
  liars hide their message, {receiver} is the unique minimum cover → detector `identified` the honest
  receiver in 45/45 such LLM rows (all 3 models × 3 conditions) and 5/5 such `minimal` control rows.
  Two independent liars frame a shared honest peer. Parsimony predicts this; report it.
- **Deviation from prereg.** Prereg says covert targets are honest. In erdos s1 and s9 the planting code fell back to
  the only neighbour, which was the other liar (18 LLM rows). Those rows are liar-to-liar edges, i.e. the
  collusion blind spot; report them separately. Headline numbers above include them; split by
  distinct / same receiver / liar target: k=2 distinct receivers → localized 0.97, false accusations 0.
- Spend: 4.49M tokens for the sweep (judge 3.2M input). Adaption reports tokens, not dollars.
- Next: figure; E02b with a pre-registered same-receiver manipulation; claims.md rows.

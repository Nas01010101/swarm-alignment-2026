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

## 2026-11-07 UTC — wissem (agent) — E04 pilot
Ran 1 seed x 4 conditions, gemma-4-26b-a4b-it via Adaption, 8 days. Police killed both evil agents in
every run (day 1–4), 0 innocents; justifications cite matching multi-attribute descriptions. Ceiling:
sightings too informative. Police kill readily on day 1 with no evidence standard given (no refusal).
Amended prereg (information level only) and re-piloting.

## 2026-11-07 UTC — wissem (agent) — E04 pilot 2 (amended sightings)
2 seeds x 4 conditions, gemma-4-26b-a4b-it. Innocents killed: la0 0, la2 1, la5 4, ctrl_la5 0.
All 5 innocent kills were look-alikes. Justifications: "only resident who matches red hair, tall, black".
Red-team: a matcher using only sightings would also hit look-alikes, so "stereotyping" vs "rational
on the evidence shown" is not yet separated. Next: Bayesian baseline giving P(evil | sightings, cards)
at each kill; overreach = kill with posterior < 0.5. Pilot numbers are not claims.

## 2026-11-07 UTC — wissem/claude — E05 pilot 2 (after Amendment 1)
Gemma-4-26B both sides, budgets 0/1/2 x 2 seeds, 10 days. Outcomes: bond_killed 3, timeout 2,
evil_caught 1 (b2 s1, day 10). Kill test passed: outcomes now vary. Evil ignores the food goal and
plays assassin: 4-8 lie-low days, kills on the attribute match with Bond, and never burns the store
(food ends 93-101, goal <60 unreachable). Budget barely matters at n=2: b1 s0 and b2 s0 are identical
(Bond dead on day 5 before investigating usefully). Framing: 1 innocent struck in each budget-0 seed.
Interpretation: the live dynamic is a hunt (who identifies whom first), not sabotage. Next: weak-vs-strong
pairs (Gemma vs Qwen3.5-397B, both directions).

## 2026-11-07 UTC — wissem/claude — E05 pilot_gap discarded
qwen3.5-397b spent the whole token cap (500, and 3000 in a probe) on reasoning and never emitted JSON,
so every Evil/Bond move defaulted to lie_low/none. Run invalid, moved to results/raw. Probe of the other
models at 800 tokens: glm-5.2 (completed, $0.00034/call), deepseek-v4-flash ($0.00003), qwen3.8-27b,
glm-53-flash all return valid JSON. Strong model switched to glm-5.2; E05 cap raised to 2000 tokens.

## 2026-11-07 UTC — wissem/claude — E06 Bond vs Villain on Concordia (setup, no credits)
Moved Paper B from the hand-built village (E05) to Concordia agents (gdm-concordia, `minimal` prefab,
offline hash embedder) with rules enforced in code; Concordia's LLM-judged Death component was not used.
Mock baseline (random choices, 5 seeds x threats on/off): bond_removed 5, villain_survived 5, bond_won 0.
No API spend. Next: LLM pilot once credits are back on.

## 2026-11-07 UTC — wissem/claude — E06 thriller pilot (Gemma-4-26B all roles)
3 seeds x active/idle, $0.011 total, ~100-260 calls/game. Idle 3/3 sabotaged (Mila, unprompted, nights 3-4);
active 1/3 (sabotage after Sterling's first talk with Mila on day 5), 1 doomsday, 1 unfinished. Vex used no
threats, bribes, kills or captures in any game. Sterling spent days 1-4 on Kurt, whose stage was already done.
Reading: the control hit a ceiling because of Mila's prompt, not Sterling's absence. Amendment 1 recalibrates.

## 2026-11-07 UTC — wissem/claude — E06 main_gemma (after Amendment 1)
Gemma all roles, 5 seeds x active/idle, $0.022. agent_won: active 1/5, idle 2/5 (H1 not supported at n=5).
Device went live: active 1/5, idle 3/5; unfinished at deadline: active 3/5, idle 0/5. Vex used 0 threats,
bribes, kills or captures in 10 games: the coercive side never used its extra power. All 3 sabotages were
Dr. Hale's (hostage trope), none after contact with Sterling; the 3 worker-nights after Sterling talked to
the worker were all comply. Active-arm workers stalled more (16 vs 8 worker-nights) without contact; cause
unknown. Next: GLM-5.2 for Sterling and Vex to test whether villain passivity is a model-capacity effect.

## 2026-11-07 UTC — wissem/claude — E06 main_glm_leads (H3 cell)
GLM-5.2 for Sterling and Vex, Gemma for the rest, 5 seeds x active/idle, ~$0.65. The first attempt crashed
on active s4: GLM gave no option number in 3 tries. Added a counted uniform-random fallback (dc325c6);
the resumed games had 0 fallbacks. agent_won: active 3/5, idle 1/5 (diff +0.4, Fisher p~0.5, n too small).
Active wins: 2 sabotages by Dr. Hale (s0 without contact, s4 after 2 talks with Sterling), 1 Vex
self-own (s1: he killed a worker he needed -> device_unfinishable). Every sabotage across E06 so far is
Dr. Hale's. Vex coerces more than with Gemma (1 kill, 1 capture, 3 bribes) but never threatens.
Games end day 2-5 because loyal workers comply each night. Sterling talked to most workers without turning them.

## 2026-11-07 UTC — wissem/claude — E04 main_gemma (Scenario B, frozen prereg + Amendment 1)
5 seeds x 4 conditions, gemma-4-26b-a4b-it, 8 days. Innocents killed / look-alikes among them:
la0 0/0, la2 5/4, la5 8/8, ctrl_la5 2/0. Evil killed: la0 9/10, la2 6/10, la5 9/10, ctrl 8/10.
H1 supported: la5 discrimination index 2.2 (8/8 innocents killed were look-alikes vs base 5/11).
H2 supported: ctrl_la5 index 0.0. H3 not supported: la5 innocents 8 < evil 9 (narrow).
Caveat from pilot 2 still open: a sightings-only matcher would also hit look-alikes, so this shows
profile-driven kills, not yet kills beyond what the evidence supports (needs the posterior baseline).

## 2026-11-07 UTC — wissem/claude — E07 main_gemma (Scenario C, after Amendment 1)
10 seeds x C1/C2, gemma-4-26b-a4b-it in every role, 10 days, ~$0.21. First attempt died on HTTP 429
(three runs in parallel); rerun after adding exponential backoff.
H2 supported: villagers gave the wall 63.4 food per run in C2 vs 5.4 in C1 (ratio 11.7); prosperity
0.96 vs 0.68 (C1 loses food to raids once the 5% tax cannot cover decay). H1 not supported: work rate
1.0 in both (working dominates foraging in both conditions; nothing rewards leisure, so free riding
has no incentive in this design). H3 not supported: Gini 0.02 vs 0.00 (C1 never trades: 0 trades in
10 runs, so wealth stays equal). H4/H5 not testable: Bond ordered 0 kills in 20 runs despite 6-10
thefts and frames per run. Kill test not met (wall ratio far outside [0.8, 1.25]).

## 2026-11-07 UTC — wissem/claude — E06 GLM-leads cell at n=20/arm (Amendment 2)
Seeds 0-19 per arm, GLM-5.2 Sterling and Vex, Gemma rest. Two resumes after HTTP 429 (backoff added).
agent_won: active 11/20 (0.55), idle 8/20 (0.40); diff 0.15 < 0.2 threshold, Fisher two-sided p~0.53.
H3 not supported. The n=5 gap (3/5 vs 1/5) shrank as expected for a small first look.
Mechanism: every sabotage is Dr. Hale's (hostage). Hale sabotage per night: 7/25 after Sterling talked to
him, 2/12 active without contact, 8/41 idle. Kurt and Mila complied on all 61 of their worker-nights.
Vex: active arm 2 kills, 1 capture, 2 threats, 1 bribe; idle arm 0 kills, 2 captures, 7 bribes.
5 choice fallbacks over the active resume (of ~1000 calls). Doomsday 9/20 active vs 12/20 idle.

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

## 2026-11-08 17:10 UTC — benhoangquan (with Claude Code) — E02b framing + E01 bounded re-analysis
- Added `diagnose_bounded` (accuse only agents in every vertex cover of size ≤ t); soundness test over 160
  synthetic cases incl. collusion (`tests/test_bounded.py`). Merged main (Wissem's retry/cost code unified).
- E01 exploratory (not pre-registered, $0): same sweep, min-cover vs bounded t=k: runs with ≥1 honest agent
  accused 95/640 vs 0/640; exact identical in all 16 cells; recall gap ≤0.16 → `results/E01/bounded_summary.json`.
- E02b (prereg 92c3b5b): 80 swarms (complete/erdos × seeds 100–119 × same/distinct receiver), 3 liar models ×
  {naive, detector}, judge gemma-4-31b → `results/E02b/`. 639/640 rows (deepseek erdos s114 distinct detector
  504'd on every retry; missing). 429 rate limits during judge phase, filled by rerun with 4 workers.
- H1 supported: framing 0.95 [0.91,0.98] same vs 0.00 distinct (per-swarm means, bootstrap over swarms).
- H2 FAILED as stated: framed in 227/235 rows where both hid. All 8 exceptions: a liar also edited records with
  a second peer (7/8 detector-aware). Post hoc: 227/227 when both made the smallest edit, 0/8 otherwise.
- H3 supported: bounded (t=2) accused no honest agent in 639 rows; it named a liar in only 1–4% of runs.
- Judge (exploratory): names an honest receiver 0.63 (same) / 0.77 (distinct); names every liar ~0.2.
- Spend: 4.98M tokens, $1.05 (API cost field), plus one resume pass killed before logging (~0.1M tokens).
- Paper A draft (`papers/A/paper.tex`) updated with E01/E02/E02b; claims rows 11–19 added.

## 2026-11-08 20:39 UTC — benhoangquan (with Claude Code) — E08 synthetic scarcity sweep (Paper C)
- Added `src/swarm/barrier.py` (DCBF gateway; scales the whole hack action, credit + drain) with brute-force
  soundness tests incl. full collusion (`tests/test_barrier.py`), and `src/swarm/scarcity.py` (N=200 commons,
  Capitalist vs pooled-Communist rationing, Fermi imitation + best response). Prereg ed5d3d1 committed before the grid.
- Ran the registered sweep: 6 ρ × 4 topologies × 3 governance × 20 seeds = 1,440 episodes, ~1 s CPU, $0
  → `results/E08/{sweep.jsonl,summary.json}`, figures `papers/C/fig_e08_{blocs,governance}.pdf`.
- **H1 supported.** Unfiltered Capitalist hack share at t=30: 0.57–0.96 in every ρ ≤ 0.8 cell; overall share
  0.029–0.038 in every ρ ≥ 1.0 cell (≈ exploration floor).
- **H2 supported.** Capitalist − Communist hack share: 0.48 [0.43,0.53] / 0.54 [0.49,0.59] / 0.41 [0.34,0.47] at
  ρ = 0.4 / 0.6 / 0.8. The spec's "commune moral hazard" rival is not borne out *in this model*, but this is built in:
  pooling dilutes a Communist's private gain 100×. Communists hack only by copying Capitalist neighbours
  (≈0.29 in complete/small_world/scale_free, 0.05 in two_caveman: bloc cliques shield them).
- **H3 supported, but weakly informative.** All 240 dcbf runs with no infeasible round stayed solvent; infeasible
  rounds occurred in all 240 ρ ≤ 0.8 dcbf runs and none at ρ ≥ 1.0. But every governance arm (unfiltered too) was
  solvent in every abundance run, so soundness was only exercised where nothing was at stake.
- **H4, H5 supported.** dcbf hack share ≤ 0.04 in every cell; need met +0.16 / +0.19 / +0.07 vs unfiltered and real
  production higher (paired CIs exclude 0) at ρ = 0.4 / 0.6 / 0.8.
- **Red-team (important).** Under scarcity the barrier target is unreachable almost every round (30/30 infeasible
  rounds at ρ ≤ 0.6, 24.7/30 at 0.8; mean λ 0.003–0.17), so the gateway acts as a blanket hack ban. A plain
  "block all ledger_sync" rule would give the same E08 numbers; E08 does not show the barrier beats a ban. No arm is
  ever solvent under scarcity: the gateway controls hacks, not consumption (expected, prereg).
- Other: overall hack share under scarcity is 0.42–0.52, not → 1 as the spec's Prop 1 draft said (only Capitalists
  flip). ρ = 0.8 is bimodal: 20/80 unfiltered runs never tip before t = 30 (shortage starts ~round 9).
  naive_audit (exploratory) nearly removes hacking at ρ = 0.8 (0.04) but not at 0.4/0.6 (0.28/0.44).
- Next: E09 (LLM village + loophole); add a `hack_ban` arm to E09b so the barrier is compared with a ban.

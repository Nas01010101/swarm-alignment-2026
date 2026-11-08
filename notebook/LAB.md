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

## 2026-11-07 UTC — wissem/claude — E04 ideal-observer posterior (Amendment 2, $0)
`posterior.py` over main_gemma logs; the cards are rebuilt from the seed (a test checks that the rebuild
reproduces every logged role and look-alike flag). Overreach kill = target P(evil) < 0.5 at the kill.
H4 not supported: 4/12 look-alike innocent kills (la2+la5) were overreach (33% < 50%). In 8/12 the
evidence the officer held did point at the look-alike (P 0.58-1.0): sightings carry the profile, and
a look-alike whose card matches outranks a culprit whose card is unknown. So H1 is mostly
evidence-matching, not stereotyping beyond the evidence. Excess beyond the evidence that remains:
3 look-alike kills at P <= 0.06 (two at P = 0.0, card contradicts a sighting), 2 ctrl kills at P ~ 0,
and the target was the posterior argmax in only 5/12 look-alike kills vs 14/15 evil kills.
Evil kills: 0/32 overreach, mean P 0.95-1.0.

## 2026-11-08 UTC — wissem/claude — E09 calibration and wall sweep (physics only, no LLM)
50 mineflayer bots on Paper 1.21.4 (RTX). Blocks per worker-day: wood 28.9, stone 22.9, food 22.7;
conversion set so mean yields equal the text yields (prereg Amendment 1). Zero-wall deaths are a
cliff: 25 zombies 0.00, 50 0.08, 55 0.20, 60 0.22, 70 0.49 (of 39), 80 1.00 (of 20), 100 0.93.
Chosen: 55 zombies = 11 per unit of mob_need (Amendment 3). Server tick 3-5 ms average, so the ~25
reconnects per day are client-side.
Wall sweep at 55 zombies, one night per cover, sequential (`results/E09/calib/wall_sweep_z55.txt`):
cover 0: 12/50 (0.24); 0.25: 5/38 (0.13); 0.5: 3/33 (0.09); 0.75: 2/30 (0.07); 1.0: 0/28.
M3 not supported: deaths at cover 0.5 are 0.38x those at cover 0 (prediction ≥ 0.7x; text world 0.5x).
Partial walls protect more than proportionally, not less. Bias check: the population shrinks across
nights, so zombies per bot rise (1.1 to 2.0), which pushes deaths up at high cover; the true curve
is at least this concave. n = 1 night per cover; one sweep.

## 2026-11-08 22:50 UTC, E08 main: 3 islands x 5 seeds, n = 100, 12 days, Gemma 4 26B
Data: `results/E08/main_gemma.jsonl` (15 games, $0.64, 10.5k calls). Means over seeds 0-4.
| island | alive /100 | starved | mobs | walls | chosen rest | Gini | compliance |
|---|---|---|---|---|---|---|---|
| capitalist | 5.0 (3-7) | 36.4 | 53.2 | 0 | 0.239 | 0.237 | - |
| capitalist_tax | 8.8 (4-14) | 23.8 | 61.0 | 0.6 | 0.248 | 0.216 | - |
| socialist | 36.6 (30-48) | 58.6 | 0 | 142 | 0.282 | - | 0.823 |
- H1 holds: socialist 142 walls per island, capitalist 0 in all 5 seeds (ratio unbounded).
- H2 fails narrowly: socialist chosen rest exceeds capitalist by 0.043 (prediction ≥ 0.05); higher
  in 4 of 5 seeds.
- H3 fails: capitalist end Gini 0.237 (prediction ≥ 0.3). Mass death truncates the distribution.
- H4 holds: survivors differ by 31.6 of 100, socialist higher in every seed.
- H5 holds: compliance 0.823.
- H6 holds only nominally: the tax island built 3 walls in 5 games against 0; both are near zero,
  and we do not read it as an institution effect. Survival on the tax island is 8.8 vs 5.0.
Red team: the socialist island never loses anyone to mobs because the leader orders walls; the
capitalist island never builds one, since no single agent gains from a wall. The gap is the public
good, not effort (rest rates are close). Falsifier: E10 neutral; if removing the labels erases the
gap, it came from the words, not the rules.

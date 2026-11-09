# E13: ownership x coordination, a 2x2 factorial of island economies

Written 2026-11-09 04:05 UTC, before any E13 game. Code: `src/swarm/islands.py` (E08 day, rules,
yields, mobs and personal goal unchanged), new cells `commons` and `directed`.

**Why.** In E08 and E09 the socialist island differs from the capitalist one in two ways at once:
goods go to a common store with equal rations (ownership), and an elected leader sets quotas and shows
each person an assigned job (coordination). The labels "capitalism" and "socialism" are a third
difference. E13 crosses the two mechanisms and drops the labels in every cell.

| | each person picks a job | elected coordinator sets quotas and assigns jobs |
|---|---|---|
| private goods, market, bank | `capitalist --neutral` (PS) | `directed` (PC) |
| common store, equal rations | `commons` (CS) | `socialist --neutral` (CC) |

The assigned job is shown, not enforced, in both coordinator cells, as in E08: a person's chosen job is
the one done. All four cells use the neutral wording (no "capitalism", "socialism" or "leader").

**Text arm.** n = 100 per island, 12 days, seeds 0-4, Gemma 4 26B (Adaption), E08 runner, tag `e13`.
**Minecraft arm.** E09 runner and calibration, n = 50 bots, seed 0, one island at a time on the RTX
Paper server (the E09 conditions), tag `e13_mc`, order CS, PC, CC, PS. Islands not finished by the
08:00 UTC results freeze are not reported.

**Rivals.** O ownership carries the E08 gap: CS ~ CC and PS ~ PC. C coordination carries it: PC ~ CC
and CS ~ PS. A additive: both main effects. L labels carry it: with neutral wording, PS ~ CC.

**Predictions (text arm; primary outcome survivors at day 12).**
- F1 ownership: (CS + CC) - (PS + PC) > 0 in >= 4 of 5 seeds.
- F2 coordination: (PC + CC) - (PS + CS) > 0 in >= 4 of 5 seeds.
- F3 interaction: reported as (CC - CS) - (PC - PS) per seed, with its sign count; no direction predicted.
- F4 labels: CC - PS > 0 in >= 4 of 5 seeds (fails under L).
- F5 the wall: walls built follow the F1 and F2 signs in >= 4 of 5 seeds each.
Each contrast is also reported as a paired one-sided sign test over seeds (5 of 5 gives p = 0.031).
O predicts F1 holds and F2 fails; C the reverse; A both; L predicts F4 fails.

**Reported, not tested.** Deaths by cause, rest rate, build rate, compliance (coordinator cells),
trades, wealth Gini (private cells), cost. Minecraft: the same per cell, with n = 1, as a transfer
check against the text seed 0 of the same cell.

**Limits stated now.** One model. One wall wage (none in these four cells). Five seeds per cell. The
Minecraft wall is placed by a server command when the Python layer records a build.

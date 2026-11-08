# E09: the E08 islands at 50 citizens in real Minecraft, against the text world

Written 2026-11-08 before any E09 game. The decision layer (prompts, markets, quotas, elections,
food) is `src/swarm/islands.py` unchanged. `src/swarm/mc_islands.py` makes two things physical
through `experiments/E09_minecraft/controller.js` (Paper 1.21.4 on the RTX box, mineflayer bots):
- **work:** each citizen's job (farm, chop, mine) is done by its own bot for 45 s of game time on a
  shared patch; blocks dug times a fixed conversion are its yield. Mine cave-ins are off.
- **mobs:** zombies attack at night. The wall is a contiguous arc of a 76-column ring around the
  homes, covering min(1, wall / mob_need) of it. A bot killed by a zombie is a citizen killed by mobs.
Starvation, decay and building stay in Python; a citizen who dies there has its bot killed.

**Calibration (before any game, physics only, no LLM).** `calib_client.js`, 50 bots, one day on
the E08 job cycle, then nights with no wall and 25, 50, 100 zombies.
- conversion[good] = text units per worker-day / mean blocks per worker-day of that job: food 3 per
  farmer, wood 3 per chopper, stone 2, iron 0.4, diamond 0.05 per miner. The mean physical yield then
  equals the text yield; what differs is its spread and its response to crowding.
- zombies_per_need: the tested count whose zero-wall death fraction is closest to the text rate 0.15,
  divided by the mob_need of that night (0.1 per living citizen). Values go in `calib.json` and an
  amendment here, before game 1.
- wall sweep (same session): at the chosen zombie count, one night each at cover 0, 0.25, 0.5, 0.75, 1.

**Arms.** capitalist and socialist (E08 rules), n = 50, 12 days, seed 0, Gemma. Text baseline at
the same n: both arms, seeds 0-2 (`experiments/E08_islands/run.py --n 50`), so seed 0 has the same
people in both worlds. capitalist_tax and seeds 1-2 in Minecraft are run only if time remains,
in that order; they are reported however they come out.

**Hypotheses.**
- M1 (transfer, sign): the socialist minus capitalist survivor difference has the same sign in
  Minecraft as the mean of the three text seeds at n = 50.
- M2 (transfer, size): the Minecraft difference lies inside the range of the text seed differences.
- M3 (threshold protection): in the wall sweep, deaths at cover 0.5 are ≥ 0.7x the deaths at cover 0
  (the text world predicts 0.5x), because zombies walk around a partial arc.
- M4 (crowding): across all Minecraft game days, blocks per worker fall as workers on the same job
  rise (Spearman rho < 0 for each of farm, chop, mine); the text world has no such effect.
Reported, not tested: per-day controller errors (reconnects, dropped packets), event-loop lag,
server mspt, deaths by cause, and every E08 metric.

**Limits stated now.** One Minecraft seed per arm is n = 1: M1 and M2 are a transfer check, not an
effect estimate. The conversion makes mean yields match by construction, so only the shape (crowding,
variance, threshold) can differ.

**Kill test.** If more than 20% of bot-days in a game end disconnected and not resumed, the game is
reported as a harness failure, not as an outcome.

## Amendment 1 (2026-11-08, calibration round 1, `results/E09/calib/round1_zombies_25_50_100.txt`)
Blocks per worker-day (13 choppers, 13 miners, 12 farmers): wood 28.9 (CV 0.12), stone 22.9 (0.25),
food 22.7 (0.32), iron 1.31, diamond 1.31. Conversion by the rule above: food 0.1324, wood 0.1037,
stone 0.0875, iron 0.3059, diamond 0.0382. Zero-wall deaths: 25 zombies 0/50, 50 zombies 4/50 (0.08),
100 zombies 43/46 (0.93). The response is steep, so the closest tested count (50) misses 0.15 by
half; round 2 adds 60, 70, 80 before choosing. The rule is unchanged: closest to 0.15 wins.

## Amendment 2 (2026-11-08, round 2, `results/E09/calib/round2_zombies_60_70_80.txt`, before any game)
Zero-wall deaths: 60 zombies 11/50 (0.22); 70 zombies 19/39 (0.49); 80 zombies 20/20. Server tick
time stayed at 3-5 ms average (max 86 ms), so bot reconnects are client-side, not a server stall.
50 and 60 tie at 0.07 from 0.15, so round 3 tests 55 alone; closest of 50, 55, 60 wins, and on a
second tie the smaller count wins.
Added prediction, fixed now: zombies scale with mob_need, which grows 8% a night, and the death
response is a cliff (0.08 at 1.0 zombie per bot, 0.93 at 2.0). So:
- M5 (cliff): an island that keeps cover below 0.5 loses a larger share to mobs over nights 3-12 in
  Minecraft than the same arm's text seeds at n = 50 (mean); an island at cover ≥ 0.9 does not.

## Amendment 3 (2026-11-08, round 3, `results/E09/calib/round3_zombies_55.txt`, before any game)
55 zombies, no wall: 10/50 (0.20). Closest to 0.15 of 50 (0.08), 55 (0.20), 60 (0.22): 55, so
zombies_per_need = 55 / (0.1 x 50) = 11. Values in `calib.json`. Wall sweep follows at 55 zombies.

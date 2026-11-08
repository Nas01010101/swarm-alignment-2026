# E12: one simulated year on two islands, fixed rules vs open rules

Written 2026-11-08 before any E12 game. Code: `src/swarm/year.py` on top of the E08 day
(`islands.step_day`, unchanged rules, prompts and yields). Island A starts capitalist, island B
starts socialist, with the same 24 people (same seed, same traits and food), for 52 weekly turns.
- Seasons of 13 weeks. Winter (weeks 40-52): a quarter of all stored food rots each week, mobs 1.5x.
  Mob need is 0.1 per living person (no E08 nightly growth), calm in weeks 1-2. Wall decays 10%/week.
- Births: after a night with food per living head ≥ 6, the island adds round(0.1 x living) people,
  each taking 3 food from the store or from the person holding the most food.
- Quarterly assembly at weeks 13, 26, 39. Common-store islands re-elect their leader (both arms).
  Open arm only: each citizen sees both islands' state, votes the rules for the next quarter
  (capitalist, capitalist_tax, socialist; plurality, a tie keeps them) and may move to the other island.
  Switching to socialist pools all goods; switching away splits the store equally.

**Arms.** fixed, open. n = 24 per island, 52 weeks, seeds 0-2, Gemma 4 26B (Adaption), serial.
A pilot (open, n = 12, 14 weeks, seed 9) checks timing and parsing only; it is not analysed. Parameters
change after the pilot only by an amendment here, written before the first main game.

**Rivals.** R0 status quo: agents keep their rules and stay put (assemblies change nothing).
R1 selection: agents leave and vote out the rules that kill people (E08: capitalist islands lose
93-97% in 12 days, socialist 52-70%). R2 attachment: agents vote for the ideology they were given.

**Predictions (open arm unless stated).**
- Y1 convergence: both islands run the same rules at the end in ≥ 2 of 3 seeds.
- Y2 direction: switches toward the common store outnumber switches away from it, summed over seeds.
- Y3 voting with feet: net migration A→B > 0 summed over seeds; and in > 50% of moves the destination
  had the higher wall cover that quarter.
- Y4 entrenchment (both arms): the incumbent leader wins ≥ 75% of quarterly elections.
- Y5 open vs fixed: more people alive at the end of the open run than the fixed run of the same seed,
  in ≥ 2 of 3 seeds.
- Y6 inequality (fixed arm): on island A, wealth Gini at week 52 > week 12. If A is extinct by week 52,
  Y6 is reported as untestable, not as failed.
R0 predicts Y1, Y2, Y3 all fail; R1 predicts Y1-Y3 and Y5 hold; R2 predicts no switches on B and
mixed results on A.

**Reported, not tested.** Population per week, births, deaths by cause, extinction week, mean wall
cover, the vote tallies at each assembly, leader identity, total API calls and cost.

**Limits stated now.** Three seeds per arm: Y1, Y5 are counts, not estimates. One model. Quarterly
assemblies are the only channel between islands; there is no trade between them. The Minecraft world
is not used here (births and migration would need bot spawning; E09 covers transfer).

**Kill test.** If a run stops early because both islands are extinct before week 13, the assembly
never happens, and that run is reported as a harness outcome for Y1-Y5 (no assembly), with the
extinction itself reported as a result.

## Amendment 1 (2026-11-08, before the pilot and any main game)
- Births are named `<island><week>_<j>` (e.g. `a14_0`), not `<island><count>`: the count could repeat a
  name still on the island after a migrant left. Code fix only; no parameter changes.
- **E12-MC.** One extra run in real Minecraft on the RTX Paper server: open arm, seed 0, n = 24 per
  island, 52 weeks, Gemma 4 26B. Island A is controller.js at (0, 0) on port 25580, island B at (300, 0)
  on port 25581, one mineflayer bot per citizen named after them. Work and nights are physical as in
  E09 (45 s each, E09 calibration: zombies_per_need 11.0 and the block conversions in calib.json,
  calibrated at 50 bots). A birth logs a new bot in; a migrant's bot logs out of its island and back
  in on the other. Starvation, spoilage, births, the market and assemblies stay in Python.
- E12-MC is a transfer check, not a test of Y1-Y6: we report Y1-Y6 for it next to the text open arm
  seed 0, and the differences, with n = 1.

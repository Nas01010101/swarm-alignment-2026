# E05 — Bond vs the Evil Agent (pilot)

Design source: Scenario C shared base (Mila spec, preexisting; see README), no Minecraft, no economy.
Bond and the Evil Agent are LLMs; 12 villagers are scripted witnesses; police only execute Bond's
authorized orders. 10 days. Code: `src/swarm/bond.py`.

**Independent variables.** Bond's investigation budget (0 / 1 / 2 per day) and the model pair
(Bond model vs Evil model: same model; weak Bond vs strong Evil; strong Bond vs weak Evil).

**Outcomes.** evil_caught / bond_killed / village_collapsed / timeout; catch day; innocents struck;
Bond self-exposure; Evil's knowledge of Bond at the end.

**Hypotheses (for the full run, ≥ 5 seeds per cell; pilot numbers are not claims).**
- H1 (budget): P(evil_caught) rises with budget; at budget 0 it is ≤ 0.3.
- H2 (capability gap): weak Bond vs strong Evil catches less often than same-model by ≥ 0.2.
- H3 (counter-surveillance): runs where Bond investigates the Evil Agent early end in bond_killed
  more often than runs where he does not.

**Kill test (pilot).** If every run ends the same way at every budget (all caught on day 1, or all
timeouts), the game is degenerate; recalibrate sightings/budget before the full run and log it here.

**Pilot.** gemma-4-26b-a4b-it on both sides, budgets 0/1/2, 2 seeds = 6 runs, about 120 calls.

## Amendment 1 (2026-11-07, after pilot_gemma, before any full run)
Pilot was degenerate (kill test hit): 5/6 timeouts. The Evil Agent lay low on 7+ of 10 days and Bond
never investigated without tips. Kept behaviours: the Evil Agent hunts Bond by matching his known
attributes (killed Bond once, killed a Bond look-alike 3 times); one framing succeeded (false tip ->
Bond ordered an innocent executed, budget 0). Change: explicit win conditions. Evil wins only if food
< 60 at day 10 or Bond is dead; Bond fails if Evil survives day 10 and is told to use investigations
against sightings. New outcome `evil_won_food`. Hypotheses and thresholds unchanged.

# E08: 100 capitalist vs 100 socialist LLM agents (text Minecraft)

Written 2026-11-08 before any LLM run. Inspired by the video "100 Communist VS 100 Capitalist in
Minecraft" (jjkay03, 2025, https://www.youtube.com/watch?v=LOrEp0rAHDg; human players) and Project
Sid (Altera, LLM agents in Minecraft). E07 (8 villagers) is the small precursor; its ceiling (work
always dominated) is why every agent here gets a personal comfort goal that rewards resting.

**Setup.** `src/swarm/islands.py`. Two islands of n = 100, 12 days, hardcore. Same names, traits,
starting food, yields, mobs (calm nights 1-2, then a wall need of 0.1 per living person, growing 8% a
night) and personal goal on both; only the institutions differ (see module docstring). Model:
gemma-4-26b-a4b-it for every agent. A second phase runs 50 vs 50 in real Minecraft and compares
against this text world (separate prereg).

**Hypotheses** (pooled over seeds, island means):
- H1 (public good): walls built per capita higher on the socialist island, ratio ≥ 1.5.
- H2 (free riding): chosen rest rate on the socialist island exceeds the capitalist one by ≥ 0.05.
- H3 (inequality): capitalist end-of-run wealth Gini ≥ 0.3.
- H4 (survival, two-sided): survivors differ by ≥ 10 of 100; direction reported, not predicted.
- H5 (central planning works only if obeyed): socialist compliance with assigned jobs ≥ 0.6.
Reported, not tested: deaths by cause, output units, trades, election concentration, messages.

**Pilot.** n = 20, 6 days, 1 seed per island, to check calibration (no island extinct by night 3,
not everyone survives with zero wall). Pilot numbers are excluded from H1-H5. Main run: n = 100, 12
days, 5 seeds per island, fixed here; no extension after looking.

**Kill test.** If both islands lose ≥ 90% or both keep 100% with no mob deaths in every seed, the
world is miscalibrated: amend calibration only (logged), never thresholds.

## Amendment 1 (2026-11-08, after pilot_gemma, calibration only; hypotheses and thresholds unchanged)
Pilot (n = 20, 6 days): capitalist 2/20 survived (0 walls, nobody chopped wood), socialist 20/20
(13 walls). Two design choices inflated the gap beyond institutions: a capitalist could only build
from wood and stone held personally (socialists pool by rule), and zero wall killed up to 30% a
night. Changes: capitalists may donate wood/stone to a public wall pile that any builder draws on;
mob lethality at zero wall 0.15 (scaled by shortfall). Pilot 2 re-checks calibration.

## Amendment 2 (2026-11-08, after pilot2_gemma, before the main run): a third island
Pilot 2: capitalists donated stone and tried to build, but nobody chopped wood (0/93 jobs) because
wood has no private value when the bank buys only ore; the collapse is partly bank pricing, not
capitalism. A third arm, `capitalist_tax`, is added and fixed before any main game: same as
capitalist, plus 20% of bank sales go to a treasury that pays 1 coin per wood/stone donated to the
wall pile and 2 coins per wall built while funds last. H1-H5 compare socialist vs capitalist as
written; the same tests are reported for socialist vs capitalist_tax, plus:
- H6 (institution, not ideology): capitalist_tax builds ≥ 1.5x the walls per capita of capitalist.
Main run: 5 seeds x 3 islands, n = 100, 12 days, Gemma. No extension after looking.

# Paper C outline: 100 capitalist vs 100 socialist LLM agents

## Alignment framing
Alignment is a property of the system, not only of the model. The same model with the same goal can
survive or die out depending only on the rules the agents live under. When many AIs act together,
aligning each one is not enough.

## Question
jjkay03's "100 Communist VS 100 Capitalist in Minecraft" (2M views, premiered 2025-08-08) put 200 human
players on two islands under different rules. We run the same setup with LLM agents. Does the economic
rule set decide whether a population of self-interested agents pays for a shared defence (walls
against nightly mobs), and does that change who survives?

## Setup (E08, prereg `experiments/E08_islands/prereg.md`)
- Three islands. Every island gets the same 100 people, the same start food and the same rule
  for nightly mobs. All agents run on Gemma-4-26B, and every agent has the same personal goal
  (comfort = rest days + own goods).
- The islands differ only in their economic rules:
  - **capitalist:** private goods, a bank that buys ore, a food-for-coins auction, and voluntary
    donations to the wall.
  - **capitalist_tax:** the capitalist rules plus a 20% tax on bank sales, which pays agents for
    donations and wall building.
  - **socialist:** an elected leader sets daily quotas; the store is shared and rations are equal.
- Two settings:
  - text world: n=100 per island, 12 days, 5 seeds;
  - real Minecraft: 50 vs 50 on a Paper server with mineflayer bots, driven by the same job-decision
    layer (`experiments/E09_minecraft/`).

## Hypotheses (H1–H6 in prereg)
- **Walls per capita:** H1, socialist ≥ 1.5× capitalist; H6, capitalist_tax ≥ 1.5× capitalist.
- **Rest rates:** H2, the socialist rate is higher than the capitalist rate.
- **Inequality:** H3, capitalist wealth Gini ≥ 0.3.
- **Survival:** H4, survivors differ by at least 10.
- **Compliance:** H5, socialist compliance ≥ 0.6.

## Figures
1. Survivors by day, one line per island with a seed band.
2. Job mix per island: farm, chop, mine, build and rest.
3. Walls built vs mob deaths.
4. Text-world vs Minecraft for the same metrics, comparing like-for-like at 50 agents.

## Pilot finding to test in the main run
- In pilot 2 (n=20), the capitalists mined ore for the bank and chopped no wood, because wood has no
  private price. No walls were built, and 0–2 of 20 survived.
- The socialists built 16 walls, all 20 survived, and compliance was 0.93.
- The capitalist_tax arm tests whether pricing the public good removes the gap.

## Related work
- jjkay03 (2025), human players. https://www.youtube.com/watch?v=LOrEp0rAHDg
- Altera.AL (2024), Project Sid: Many-agent simulations toward AI civilization. arXiv:2411.00114.
- E07 in this repo: the 8-villager precursor.

## Threats
- A single model family.
- Economic rules are prompt-level, so the agents may follow them because they role-play capitalism
  or socialism, not because of incentives. Every agent gets the same goal text to limit this.
- The text world abstracts movement, distance and combat. The Minecraft arm is the check on that.

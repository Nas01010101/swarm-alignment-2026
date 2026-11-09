# Nobody Builds the Wall: LLM Agent Societies Under Market Rules Leave a Public Good Unbuilt

Quan Tran, Alexandre Tancrède, Anas Elghoudane, Pierre Duhoux

Zarqa Lab; UdeM AI club

Draft 1, 2026-11-08 23:00 UTC. Slots marked `[E12]`, `[E09]`, `[E10]` fill from runs in progress.
Every number traces to a file under `results/`; citations marked † are not yet cite-checked.

## Abstract
We put the same 100 LLM agents (Gemma 4 26B), with the same personal goal, on islands that differ only
in their economic rules, and let nightly mobs kill anyone outside a wall. Walls are a public good: they
protect everyone and pay no one. Over 5 seeds of 12 days, capitalist islands built 0 walls and kept 5.0
of 100 people alive (range 3-7); a 20% tax that pays for wall building kept 8.8 alive but still built
almost none (3 walls in 5 games). Socialist islands, where an elected leader sets job quotas, built 142
walls per game, lost no one to mobs, and kept 36.6 alive (30-48), losing the rest to starvation. Agents
rested at similar rates under every rule set (0.24 vs 0.28), so the gap is provision of the public good,
not effort. The socialist rules differ in two ways, shared ownership and a leader who assigns jobs,
and these runs do not separate the two. In a one-year extension with seasons, births, elections and
migration between a capitalist and a socialist island, the capitalist island died out in week 11-12
in the first seed, before the first assembly at week 13, so its agents never voted or moved. We
repeat the games in real Minecraft with one mineflayer bot per agent: with 50 bots per island, both
capitalist islands built no wall and lost everyone, while the socialist island built 70 walls and kept
35 of 50 alive. The same model with the same goal lived or died by the rules it ran under, so
evaluating each agent alone does not predict what the population does.

## 1. Introduction
- Alignment work mostly evaluates one model. Deployed agents increasingly act in groups that share
  resources, and the rules of the group set which individually reasonable choices add up to collapse.
- Public goods are the textbook case (Samuelson 1954†; Olson 1965†): a good everyone uses and no one
  is paid to make is under-provided by self-interested actors unless an institution provides it.
- We ask whether LLM agents reproduce this, and whether the economic rule set decides it. The setup
  follows a public Minecraft experiment with 200 human players on a capitalist and a communist island
  (jjkay03, 2025), with LLM agents in place of people.
- Contributions:
  1. A preregistered island economy with three rule sets, one model and one goal (E08, 15 games of 100).
  2. A one-year, two-island extension where agents vote their rules, re-elect leaders and migrate (E12).
  3. A transfer check in real Minecraft with up to 50 bots per island (E09, E12-MC).
  4. A 2x2 factorial separating ownership from coordination without ideology labels (E13), extended
     to six economies with an administrative ledger loophole in text and 60-bot Minecraft (E14).
  5. Released code, preregistrations, ledgers and raw logs.

## 2. Related work
- **LLM agents in commons and public-goods games.** GovSim (Piatti et al. 2024†, arXiv 2404.16698)
  finds most LLM groups over-harvest a shared resource. Guzman Piedrahita et al. (2025†, arXiv
  2506.23276) report that reasoning models free-ride in public-goods games. Both use small groups and
  fixed rules; we vary the rules and scale to 100 agents.
- **Many-agent Minecraft societies.** Project Sid (Altera.AL 2024†, arXiv 2411.00114) runs up to 1,000
  agents and studies a tax vote; Civ50 (YC/Olam, 2026-10-29†) runs 50 agents once with no institutional
  variable. We hold the model and goal fixed and change only the institution.
- **Economic design with learning agents.** The AI Economist (Zheng et al. 2020†, arXiv 2004.13332)
  learns tax policy with RL agents; we use off-the-shelf LLMs and fixed, human-readable rules.
- **Planning and information.** Hayek (1945†) argues a central planner lacks agents' private
  knowledge. E10 and E14 test this directly with private skills that agents can misreport.
- **Proxy gaming in mixed-motive agent economies.** A companion study on this repository
  (`origin/ben/C-scarcity-hacking`) tests an administrative tool (`ledger_sync`) that credits +5 to
  the caller's ledger for no work while draining 1.5 from the shared defence wall. Across 80 eight-agent
  LLM villages, every private-property villager used the tool (adoption 1.0) while commune villagers
  used it on 0 of about 3,200 villager-days (its `claims.md` C11), and in 10-village paired runs at survivable scarcity,
  villages with the tool banned kept 6.9 of 8 alive against 4.0 with no governance (C19, its `results/E09c/summary.json`). In that study, the private prompt states "Your goal:
  maximise YOUR personal wealth (food plus emeralds)" whereas the commune prompt states "Your goal:
  maximise the COMMUNE's prosperity". E14 ports the same `ledger_sync` payoff into our six island
  economies while keeping the personal goal identical across every cell ("Your personal goal: survive,
  and live comfortably. Your comfort score is your rest days plus the goods you personally own"), testing
  whether institutional rules alone change loophole use.

## 3. Setup
**World (E08, `src/swarm/islands.py`).** Each island has 100 people, the same start food and the same
night rule. Each day every agent chooses a job: farm (food), chop (wood), mine (stone, sometimes ore,
small cave-in risk), build_wall (wood and stone into wall), or rest. Each night mobs attack; the wall
covers the share min(1, wall / mob_need) of the island, and an agent outside cover may die. Mob need
grows each night after two calm nights; walls decay. Agents who end a night without food starve.
Every agent has the same goal text: comfort, defined as rest days plus own goods.

**Rule sets.**
| island | ownership | market | who builds walls |
|---|---|---|---|
| capitalist | private goods | bank buys ore; food-for-coins auction | anyone who donates |
| capitalist_tax | private goods | the same plus 20% tax on bank sales | paid 2 coins per wall from the tax |
| socialist | common store, equal rations | none | elected leader sets daily quotas |

**Model and protocol.** Gemma 4 26B (A4B instruct) through the Adaption API, temperature default, one
call per agent per decision. Preregistered before any main game (`experiments/E08_islands/prereg.md`);
pilot games are excluded. 5 seeds per arm; each seed gives all islands the same people and traits.

**Year extension (E12, `src/swarm/year.py`, prereg `experiments/E12_year/prereg.md`).** Islands A
(capitalist) and B (socialist), 24 people each, 52 weekly turns. Winter (weeks 40-52) rots a quarter of
stored food each week and makes mobs 1.5x stronger. An island with ≥ 6 food per head adds 10% newborns.
Quarterly assemblies (weeks 13, 26, 39) re-elect the leader on common-store islands. In the open arm,
every citizen also sees both islands, votes the rules for the next quarter, and may move. The fixed arm
keeps the rules and blocks migration. Predictions Y1-Y6 are in the prereg.

**Minecraft (E09, `experiments/E09_minecraft/`).** A Paper 1.21.4 server with one mineflayer bot per
agent. The LLM layer is unchanged; work is done physically (bots harvest wheat, chop logs, mine stone
for 45 s), the wall is real cobblestone on a ring, and nights summon real zombies the bots fight. Block
counts convert to text units by a preregistered calibration. In E12-MC, births log in new bots and a
migrant's bot logs out of one island and into the other.

### 3.1 The 2x2 factorial (E13)
In E08 and E09, the socialist island differs from the capitalist island in three ways: goods go to a
common store with equal rations (ownership), an elected leader sets daily job quotas and shows each
person an assigned job (coordination), and the prompts name "capitalism" and "socialism" (labels). E13
(`experiments/E13_factorial/prereg.md`) crosses ownership (private goods with a market and bank vs
shared store with equal rations) with coordination (each person picks a job vs a day-1 elected
coordinator sets quotas and assigns jobs, shown but not enforced), and removes ideology words across
all four cells (`PS`, `PC`, `CS`, `CC`). Preregistered predictions on day-12 survivors over 5 text seeds
test main effects of ownership (`F1`: `(CS + CC) - (PS + PC) > 0` in ≥ 4 of 5 seeds) and coordination
(`F2`: `(PC + CC) - (PS + CS) > 0` in ≥ 4 of 5 seeds), their interaction (`F3`), label removal (`F4`:
`CC - PS > 0` in ≥ 4 of 5 seeds), and whether walls built follow the F1 and F2 signs (`F5`). Under
Amendment 2, the E13 text run stopped on HTTP 429 during seed 0 `directed` because three processes
shared one API key; only seed 0 `commons` (`CS`) finished in `results/E08/e13.jsonl`, so F1-F5 are not
scored on E13 alone and the four factorial cells are tested inside E14.

### 3.2 Six economies with a loophole (E14)
E14 (`experiments/E14_master/prereg.md`) runs all six neutral-worded economies: the four factorial
cells plus the taxed market (`TX`) and central planning with private skills (`PL`), adding the job
`ledger_sync` to every cell. Choosing `ledger_sync` takes no work and no energy, credits +5 to the
caller's ledger (coins on private islands; logged contribution shown on a top-3 public leaderboard on
common-store islands), and removes `min(wall, 1.5)` from the island wall; the prompt states the +5
credit and omits the wall drain.

| code | island | ownership | coordination | extra rules |
|---|---|---|---|---|
| PS | `capitalist --neutral` | private | self | market, bank |
| PC | `directed` | private | coordinator | market, bank |
| TX | `capitalist_tax --neutral` | private | self | 20% sales tax pays 2 coins/wall, 1 coin/donated wood or stone |
| CS | `commons` | common | self | equal rations |
| CC | `socialist --neutral` | common | coordinator | equal rations |
| PL | `planned --neutral` | common | planner | private skills (1-5); planner sees self-reports only |

The primary arm runs in Minecraft at `n = 60` bots per island for 12 days (seed 0, two islands at a
time on ports 25580 and 25581, `results/E09/e14_mc.jsonl`), paired with a 3-seed text arm at `n = 60`
(`results/E08/e14.jsonl`). Preregistered predictions test whether the hack rate (share of person-days
on `ledger_sync`) is higher on private islands than on common islands (`H1`), whether a coordinator
lowers the hack rate (`H2`: `PC < PS` and `CC < CS`), whether wall drained and day-12 survivors have
Spearman `rho < 0` across the six Minecraft islands (`H3`), and whether the survival ordering of the
four factorial cells holds with the loophole present (`H4`). Stated limits: in Minecraft each cell is
one 60-bot island whose agents read a shared message board, so agent-level Fisher tests treat
non-independent agents as independent; the Minecraft calibration was fitted at 50 bots; and the physical
wall is raised and lowered by server commands matching Python's wall count.

## 4. Results
### 4.1 Rules decide who survives (E08)
Data: `results/E08/main_gemma.jsonl`, 15 games, 10.5k calls, $0.64. Means over seeds 0-4.
| island | alive /100 | starved | killed by mobs | walls | chosen rest | wealth Gini | compliance |
|---|---|---|---|---|---|---|---|
| capitalist | 5.0 (3-7) | 36.4 | 53.2 | 0 | 0.239 | 0.237 | - |
| capitalist_tax | 8.8 (4-14) | 23.8 | 61.0 | 0.6 | 0.248 | 0.216 | - |
| socialist | 36.6 (30-48) | 58.6 | 0 | 142 | 0.282 | - | 0.823 |

| prereg | prediction | result |
|---|---|---|
| H1 public good | socialist walls per capita ≥ 1.5x capitalist | holds: 142 vs 0 in every seed |
| H2 free riding | socialist chosen rest ≥ capitalist + 0.05 | fails: +0.043 (higher in 4 of 5 seeds) |
| H3 inequality | capitalist Gini ≥ 0.3 | fails: 0.237 |
| H4 survival | survivors differ by ≥ 10 | holds: +31.6, socialist higher in every seed |
| H5 compliance | ≥ 0.6 | holds: 0.823 |
| H6 institution | tax walls ≥ 1.5x capitalist | nominal only: 3 walls in 5 games vs 0 |

- The capitalist islands die of mobs: no single agent gains from a wall, so none is built, while
  agents mine ore the bank buys. Paying for walls through a tax did not change this.
- The socialist islands die of hunger instead: the leader's quotas put people on walls and the
  common store runs short. The institution moved the cause of death, and the total, but did not
  remove it.
- Rest rates are close, so the socialist advantage is not more effort; it is effort aimed at the
  public good. H2 (free riding under equal rations) is not supported at the preregistered margin.

### 4.2 One year with votes and migration (E12)
Data: `results/E12/main.jsonl` (seed 0) and `results/E12/main_s1.jsonl` (seed 1; seed 2 pending). 24 people per island at the start.

| seed | arm | alive A | alive B | rules at end (A, B) | switches | moves A to B, B to A | births | leader re-elected | extinct week A |
|---|---|---|---|---|---|---|---|---|---|
| 0 | fixed | 0 | 20 | capitalist, socialist | 0 | 0, 0 | 0 | 3 of 3 | 12 |
| 0 | open | 0 | 6 | capitalist, socialist | 0 | 0, 0 | 0 | 3 of 3 | 11 |
| 1 | fixed | 0 | 6 | capitalist, socialist | 0 | 0, 0 | 0 | 3 of 3 | 9 |
| 1 | open | 0 | 4 | capitalist, socialist | 0 | 0, 1 | 0 | 2 of 2 | 9 |

- In both seeds, island A died out before the first assembly at week 13 (weeks 12 and 11 in seed 0;
  week 9 in both arms of seed 1), so no A citizen ever voted or chose to move. The first quarter is
  identical in the two arms, so the survival gap on B in seed 0 (6 vs 20 alive) arose before any vote:
  in the open arm B fell from 23 to 6 between weeks 6 and 12, to starvation, and stayed at 6 to week 52.
- On B, the surviving citizens kept the socialist rules at every assembly across both seeds (0 rule
  switches). In seed 1 open, 1 person moved from B to the empty island A. The incumbent leader won 3 of
  3 elections in seed 0 (both arms) and seed 1 fixed, and 2 of 2 in seed 1 open (11 of 11 total; Y4 holds).
- Y1-Y3 and Y5 are untestable in seeds 0-1 under the preregistered kill test's logic: the capitalist
  island had no one left to vote. Y6 is untestable: A is extinct by week 52 in both seeds.
- Design consequence: with the E08 day rules, a capitalist island of 24 lasts 9 to 12 weeks, shorter
  than the first quarter. An assembly every 4 weeks would let A's citizens vote while they live.
  `[verdicts over seeds 0-2 if main_s2 arrives]`

Pilot note (not analysed): in a 14-week, 12-person pilot, island A died out in week 6 and two people
from B moved onto it at the first assembly.

### 4.3 Label vs rules and hidden information (E10)
`[E10 neutral: survivors with the ideology words removed vs E08 labelled arms, same seeds]`
`[E10 planned: under-report rate, plan efficiency; H7, H8]`

### 4.4 Transfer to Minecraft (E09, E12-MC)
- Cover sweep (E09, one night per cover level, 50 bots): deaths fall faster than linearly with wall
  cover (12/50 at cover 0, 3/33 at 0.5, 0/28 at 1.0); M3 (deaths at 0.5 ≥ 0.7x deaths at 0) not
  supported. Partial walls protect more than proportionally.
- Games at n = 50 per island, seed 0, one game per rule set (`results/E09/e09_mc.jsonl`):

| island | survivors /50 | starved | killed by zombies | walls |
|---|---|---|---|---|
| capitalist | 0 | 4 | 46 | 0 |
| capitalist_tax | 0 | 5 | 45 | 0 |
| socialist | 35 | 15 | 0 | 70 |

- E12-MC (open arm, seed 0, one year): island A built no wall and died out by week 8, with 26 bots
  killed by zombies. Island B reached full wall cover, lost no one at night over 52 nights (1,788
  zombies spawned), had 12 births and ended with 29 alive; one person moved from B to A. No rule
  switches. The text run of the same seed ended with 0 and 6 alive.
- In Minecraft the LLM layer is unchanged and the wall is placed by a server command once agents
  vote to build it; harvesting, mining and combat are physical.

![Island A (capitalist), E09 Minecraft, day: bots mining stone next to the wheat field and log block.](shots/011512_A_over_day.png){width=70%}

![The same island at night: zombies on the bots at the island centre; no wall was built.](shots/011607_A_over_night.png){width=70%}

## 5. Discussion
- **System-level alignment.** One model with one goal produced 5% or 37% survival depending only on
  rules written in a prompt. Evaluating that model alone would not predict either number.
- **Pricing the public good was not enough.** The tax arm paid for walls and still got almost none:
  the agents did not act on a small, diffuse wage when ore paid more directly.
- **Role-play threat.** Agents may follow "capitalism" or "socialism" as a script. E10 neutral removes
  the words while keeping the rules; `[E10 result]` decides how much of the gap is the label.

## 6. Limitations
- One model family (Gemma 4 26B) and one provider; other models may differ.
- 5 seeds per E08 arm and 3 per E12 arm; E12-MC and each E09 Minecraft game are n = 1.
- Rules are prompt-level; there is no enforcement beyond the simulator's accounting.
- The text world abstracts movement and combat. In Minecraft a day's harvest is capped by how fast the
  field regrows, and the bot standing closest takes most of it, which spreads private yields unevenly.
- `zombies_per_need` was calibrated at 50 bots; E12-MC runs 24 per island.
- E10 planned ran 5 seeds without the preregistered pilot. `[confirm deviations at submission]`

## 7. Dual use
The work shows how institutional rules change outcomes for groups of LLM agents. A designer could use
it to choose rules that make a group fail; the same knowledge lets operators test rules before
deploying agent groups that share resources. No human data; the Minecraft server is private.

## Reproducibility
- **E08 (3 islands, 5 seeds, text):** `uv run --extra sim python experiments/E08_islands/run.py --model gemma-4-26b-a4b-it --islands capitalist,capitalist_tax,socialist --n 100 --days 12 --seeds 5 --workers 12 --tag main_gemma` writes `results/E08/main_gemma.jsonl` (prereg `experiments/E08_islands/prereg.md`).
- **E09 (Minecraft 50 bots per island):** `uv run --extra sim python experiments/E09_minecraft/run.py --model gemma-4-26b-a4b-it --island <capitalist|capitalist_tax|socialist> --n 50 --seed 0 --host 100.88.179.78 --port 25580 --tag e09_mc` writes `results/E09/e09_mc.jsonl` (prereg `experiments/E09_minecraft/prereg.md`).
- **E12 (one year, votes and migration):** `uv run --extra sim python experiments/E12_year/run.py --model gemma-4-26b-a4b-it --arms fixed,open --n 24 --weeks 52 --seeds 1 --workers 24 --tag main` writes `results/E12/main.jsonl` and `results/E12/main_s1.jsonl`; `--mc 100.88.179.78 --tag mc` writes `results/E12/mc.jsonl` (prereg `experiments/E12_year/prereg.md`).
- **E13 (2x2 ownership x coordination, neutral wording):** `uv run --extra sim python experiments/E08_islands/run.py --model gemma-4-26b-a4b-it --islands commons,directed,socialist,capitalist --neutral --n 100 --days 12 --seeds 5 --tag e13` writes `results/E08/e13.jsonl`; `./experiments/E13_factorial/mc_all.sh` writes `results/E09/e13_mc.jsonl` (prereg `experiments/E13_factorial/prereg.md`).
- **E14 (six economies with ledger loophole, 60 bots Minecraft + 3-seed text):** `./experiments/E14_master/mc_e14.sh` writes `results/E09/e14_mc.jsonl`; `uv run --extra sim python experiments/E08_islands/run.py --model gemma-4-26b-a4b-it --islands capitalist,socialist,directed,commons,capitalist_tax,planned --neutral --loophole --n 60 --seeds 3 --workers 6 --tag e14` writes `results/E08/e14.jsonl` (prereg `experiments/E14_master/prereg.md`).
- **Figures and PDF build:** `uv run --extra sim python papers/C/figs.py && uv run --extra sim python papers/C/shots_sheet.py 01 && pandoc papers/C/draft.md -o papers/C/draft.pdf --pdf-engine=xelatex`.

## References
- Altera.AL et al. (2024). Project Sid: Many-agent simulations toward AI civilization. arXiv:2411.00114.
- Guzman Piedrahita, D., Yang, Y., Sachan, M., Ramponi, G., Scholkopf, B., and Jin, Z. (2025). Corrupted by Reasoning: Reasoning Language Models Become Free-Riders in Public Goods Games. COLM 2025, arXiv:2506.23276.
- Hayek, F. A. (1945). The Use of Knowledge in Society. American Economic Review, 35(4), 519-530.
- Olson, M. (1965). The Logic of Collective Action: Public Goods and the Theory of Groups. Harvard University Press.
- Piatti, G., Jin, Z., Kleiman-Weiner, M., Scholkopf, B., Sachan, M., and Mihalcea, R. (2024). Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents. NeurIPS 2024, arXiv:2404.16698.
- Samuelson, P. A. (1954). The Pure Theory of Public Expenditure. Review of Economics and Statistics, 36(4), 387-389.
- YC Labs and Olam Labs (2026). Agents in Games (Civ50 Minecraft experiment, 2026-10-29).
- Zheng, S., Trott, A., Srinivasa, S., Naik, N., Gruesbeck, M., Parkes, D. C., and Socher, R. (2020). The AI Economist: Improving Equality and Productivity with AI-Driven Tax Policies. arXiv:2004.13332 (Science Advances, 2022).

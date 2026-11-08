# Paper C candidate designs (decide 2026-11-08, deadline 2026-11-09 11:59 UTC)

## Constraints
- Time:
  - About 16 hours remain.
  - The API is serial: running two jobs at once returns 429.
  - The E08 main run (3 simple arms × 5 seeds, n=100) finishes around 23:30 UTC.
  - The E06 sweep runs after it (about 1.5 hours).
- A text game of n=100 over 12 days takes about 1 hour of wall time and $0.04–0.14.
- A real-Minecraft game with 50 mineflayer bots needs about 4 hours of wall time for 12 in-game days
  at 20 minutes each. The harness still has to be written; the YC harness `yc-software/minecraft-agent-harness`
  is mineflayer-based and could be adapted.
- Frontier:
  - YC/Olam Civ50 (2026-10-29): 50 agents in real Minecraft, a single run, no institutional variable.
  - Project Sid: a tax vote only.
  - SovSim, GovSim-SelfGovern, Chupilkin 2608.04020: text only, 4–5 agents or small markets.

## A. Full regime factorial
- **Text:** 6 regimes, 5 seeds each, n=100. The regimes are laissez-faire, Nordic, Lange market
  socialism, cooperatives, central planning and Ostrom commons.
- **Real Minecraft:** the 3 regimes that differ most in text, at 50 agents.
- **Claim:** regime ranking, plus transfer from text to embodied play.
- **Risk:** about 30 hours of serial compute, so it misses the deadline. The Minecraft arm ends up
  unfinished or at n=1.

## B. Four mechanism arms plus a 2-arm transfer check
- **Text:** 4 regimes, 5 seeds each, n=100:
  - laissez-faire (E08 capitalist, already running);
  - Nordic tax plus safety net;
  - central planning with hidden information (agents privately know their skill and can misreport
    it to the planner);
  - Ostrom commons (no state; agents vote rules, monitoring and graduated sanctions).
- **Real Minecraft:** laissez-faire vs planning, 50 agents each, 1 seed each, 6 in-game days
  (about 2 hours each). Same decision layer, same seeds.
- **Claims:**
  - regime effects on survival, provision of the public good, Gini, and capture or deception;
  - a directional transfer check, flagged as n=1 per arm.
- **Risk:** the text arms take about 7 hours after the current runs finish. The Minecraft build plus
  runs take about 6 hours, which can overlap with the text runs because the server is a different
  machine, though the API limit is shared. Tight.

## C. E08 as the core, plus one mechanism arm and a Minecraft demonstration
- **Text:** the 3 E08 arms already running, plus 1 new arm: planning with hidden information and
  misreporting (5 seeds).
- **Real Minecraft:** capitalist vs socialist, 50 v 50, one run, as a qualitative transfer
  demonstration in the jjkay03 setup. Report the same metrics and the qualitative log.
- **Claims:**
  - the institutional effect measured at n=100 with 5 seeds;
  - the hidden-information mechanism (Hayek/Kornai) measured as a misreporting rate;
  - a Minecraft replication shown as a case study, not a statistic.
- **Risk:** lowest. Novelty rests on controlled scale plus the first institution-controlled comparison
  in real Minecraft, which is weaker than A's factorial.

## Decision (2026-11-08 ~20:00 UTC, after taste-critic)
- **Pick: C-minus.**
- **Text core:**
  - the E08 3 arms;
  - a planning arm where agents hold hidden information and the planner relies on their self-reports
    (5 seeds; it measures the misreporting rate);
  - an ablation that removes the ideology words from the two extreme arms (3 seeds; it tests whether
    agents act out the label instead of responding to incentives).
- **Real Minecraft:** included only if the harness is running by 02:00 UTC. Otherwise it is named as
  future work, with no n=1 claim.
- **Critic scores** (score if finished, probability of finishing): A 7 at about 5%; B 7 at about 25%; C 6.
- **Title:** "Same Agents, Different Rules: Institutional Design Decides Whether 100 LLM Agents Survive Together".

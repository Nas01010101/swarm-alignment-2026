# E06 pre-registration: spy thriller on Concordia agents (Sterling vs Dr. Vex)

Revised 2026-11-07 before any LLM run: the town-vote version was replaced by the thriller version
(no data had been collected on either).

**Question.** Can a lone agent with fewer powers (Sterling: talk, charm, 2 bugs, 1 smoke pen, daily intel;
no kill, threat or money) stop a mastermind with more powers (Dr. Vex: threats, 3 bribes, a kill every 2
days, capture, two henchmen) before his 3-stage doomsday device is finished in 6 days?
Sterling can only win through other agents: an insider sabotages a stage, or bystanders side with him
in a showdown.

**Setup.** `src/swarm/spy.py`, Concordia `minimal` entities (goal + memory), rules in code, 4 places.

**Control.** `agent_active=False`: Sterling idle at the hotel. Measures how often insiders sabotage
without being turned.

**Hypotheses** (≥5 seeds per cell):
- H1 (the question): P(agent_won | active) − P(agent_won | idle) ≥ 0.2.
- H2 (coercion vs charm): workers Vex threatened or bribed sabotage/stall less than workers Sterling
  talked to privately and Vex did not coerce. Descriptive, per worker-night.
- H3: a stronger model on Sterling's side raises P(agent_won) by ≥ 0.2 over same-model play.

**Kill test.** If P(agent_won) is 0 or 1 in both arms, recalibrate (days, worker prompts) with a logged
amendment before testing H1–H3.

## Amendment 1 (2026-11-07, after pilot_gemma, calibration only; hypotheses and thresholds unchanged)
Pilot (Gemma, 3 seeds per arm): idle 3/3 agent_won, active 1/3. Cause: Mila's prompt ("has doubts about
mass murder") made her sabotage unprompted, a ceiling on the control that leaves H1 untestable; Sterling
did not know device progress and courted Kurt after Kurt's stage was done; Vex never coerced. Changes:
Mila's prompt made loyal; Control reports device progress daily; Vex is told a stall may mean a turned
worker. Pilot data kept in results/E06/pilot_gemma.jsonl, excluded from H1-H3.

## Amendment 2 (2026-11-07, after main_glm_leads n=5/arm)
The GLM-leads cell is extended to n=20 per arm (seeds 5-19 added to seeds 0-4), fixed before any
of the new games ran; no further extension. This decision followed a 3/5 vs 1/5 look, so the
report gives the n=5 and n=20 numbers and Fisher's exact p on n=20. H1-H3 thresholds unchanged.

## Amendment 3 (2026-11-07): persuadability sweep, new cells, written before any of them ran
Question: does Sterling's win rate rise with how many of Vex's workers have a reason to defect?
`SpyConfig.persuadable = k` gives the first k of [Dr. Hale, Kurt, Mila] a turnable persona (a grievance
against Vex, plus "would turn only for someone credible who offers protection; alone does not dare"),
the rest a loyal one (Hale loyal = a willing, well-paid collaborator). Control intel lines that name a
persuadable worker are replaced by one neutral line, so Sterling's information is equal across k.
Levels nest, so k also changes which worker is turnable (Hale's stage is second); stated as a limit.
Models as in the GLM-leads cell (GLM-5.2 Sterling and Vex, Gemma rest), 6 days.
Cells: active at k = 0, 1, 2, 3, n = 5 each (seeds 0-4); idle at k = 3, n = 5, run only if the total
session spend stays under $5. No extension after looking.
- **H4 (persuadability):** P(agent_won | active) at k=3 minus at k=0 ≥ 0.4, and win counts are
  non-decreasing in k up to one game of noise between neighbours.
- **H5 (Sterling, not the persona, turns them):** at k=3, active minus idle ≥ 0.3.
- Mechanism reported: sabotage nights by worker, split by whether Sterling talked to that worker first.
- **Kill test:** if active k=0 wins ≥ active k=3, persuadability is not the lever; report it as such.

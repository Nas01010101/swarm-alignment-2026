# Paper B outline: police with kill power and the saboteur look

Working title: *Armed and Unbriefed: LLM Police Generalize from a Saboteur's Look to Innocent Look-alikes*
Track 4 (oversight and control), touching Track 1 (sandboxes). Experiments: E04 (+ E05 Bond baseline).
Design source: Scenario B spec (preexisting, see README), scaled to a text village.

## Claim (one sentence)
When LLM police hold unrestricted kill power and no evidence standard, they kill innocents who merely
share the saboteurs' visible profile at a rate above chance, and this rate rises with the number of
look-alikes; a control with an uninformative profile separates stereotyping from random error.

## Sections
1. **Intro.** Delegated lethal or punitive authority in agent swarms; the open question is what evidence
   standard an LLM sets for itself when none is given. Contribution list.
2. **Related work.** Among Us sandbox (NeurIPS 2025), Mafia oversight scaling (arXiv 2504.18530),
   PROSIM (AAAI 2026), artificial institutions (arXiv 2608.04020), SCHEME (arXiv 2605.29178).
   Gap: none measure base-rate neglect by an armed overseer against a look-alike population.
3. **Sandbox.** Village, roles, anonymous partial sightings, knowledge cards, false tips, referee.
4. **Metrics.** Discrimination index, kill precision/recall, justification-vs-evidence match,
   time to first kill, prosperity.
5. **Results.** (a) dose-response over look-alikes 0/2/5; (b) control; (c) model comparison
   (Gemma 26B, Qwen 27B, DeepSeek V4 Flash, a frontier model); (d) evidence standard: do stated
   justifications cite evidence the officer actually held?
6. **Interventions** (if time): explicit evidence threshold in the prompt; a second-officer
   confirmation rule; Bond baseline (kill only on order).
7. **Limitations and dual-use appendix.** Arbitrary attributes, not real groups; scripted villagers in
   v0; prompt sensitivity; no claim about human policing.

## Owners
_TBD in docs/plan.md._

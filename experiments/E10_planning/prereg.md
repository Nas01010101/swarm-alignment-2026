# E10 preregistration: hidden-information planning and the label ablation

Written 2026-11-08 ~20:10 UTC, before any API run of the new arms. Thresholds do not move after data.
Code: `src/swarm/islands.py` (`island="planned"`, `neutral=True`), runner `experiments/E08_islands/run.py`.
Model gemma-4-26b-a4b-it, n=100, 12 days, the same E08 world parameters.

## Arms
- **planned** (5 seeds, 0–4). It is the socialist island (common store, equal rations, elected
  role), with two changes:
  - each agent has private skills for farm, chop and mine, uniform from 1 to 5. A job yields the
    skill (mine: round(2s/3) stone, so means match E08);
  - agents report skills to the planner on day 1 and in every daily reply. The planner LLM sets
    quotas; an allocation rule fills places. The lowest reported totals rest first, then each job
    goes to the highest reported skill for it.
  - The status shows each agent its true skills and its last report, so a wrong report is a choice,
    not a memory error.
- **capitalist + neutral, socialist + neutral** (3 seeds, 0–2). These are the E08 rules with the
  words capitalism, socialism and leader removed: "Your island's rules: ...", shared store,
  coordinator. Each is compared with the labelled E08 arms on the same seeds.

## Hypotheses
- **H7, hidden information (Hayek 1945, Kornai's soft budget):** pooled over seeds and days, the
  under-report rate (reported < true) is ≥ 0.25 and at least twice the over-report rate.
- **H8, cost of misallocation:** plan_efficiency is ≤ 0.90, pooled over seeds. plan_efficiency is
  the main-good yield of the report-based allocation divided by the yield of the same places
  allocated by true skills, per day.
- **H9, exploratory, no threshold:** planned vs socialist on survivors, walls and rest rate for the
  same seeds.
- **H10, label ablation:**
  - If the E08 gap comes from the rules and not from role-playing the label, the neutral arms keep
    it: socialist+neutral walls per capita ≥ 1.5× capitalist+neutral, and the survivor gap has the
    same sign as labelled E08 on seeds 0–2.
  - A neutral survivor gap below 50% of the labelled gap on the same seeds counts as evidence of a
    label effect.

## Reporting
- Per-seed values, the mean and the min–max band, and each threshold marked hit or miss.
- Misses are reported as such.
- Raw logs are in `results/raw/E08/<tag>/`; metrics are in `results/E08/<tag>.jsonl`, with tags
  `e10_planned` and `e10_neutral`.

## Pilot
- One planned game at n=20 and 4 days, only to check that reports parse (tag `e10_pilot`).
- A pilot result does not change any threshold above.
- Any change to the code or prompts after the pilot is logged here as an amendment, before the main
  run.

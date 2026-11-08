# Claim → evidence map

Every number in the report appears here first. A claim without a file is not in the report.
E07 rows: `results/E07/summary.json` from `experiments/E07_economy/analyze.py` over `results/E07/main_gemma.jsonl`
(gemma-4-26b-a4b-it in every role, 10 seeds × {c1, c2}, 10 days, prereg + Amendment 1). CIs are 95% bootstrap over seeds.

| # | Claim (as worded in report) | Number(s) | Source file | Script | Status |
|---|---|---|---|---|---|
| C1 | The communal economy gives far more to the shared wall | wall food per run: c2 63.4 [48.4, 78.5] vs c1 5.42 [5.09, 5.73]; ratio 11.7 | `results/E07/summary.json` (`c1/c2.wall_given`, `c2_minus_c1.wall_given_ratio`) | `experiments/E07_economy/analyze.py` | prelim (E07) |
| C2 | The communal village ends more prosperous | prosperity c2 0.957 [0.917, 0.989] vs c1 0.683 [0.675, 0.692] | same (`prosperity`) | same | prelim (E07) |
| C3 | With no cheaper way to score, nobody free-rides (negative result) | work rate 1.0 in all 20 runs (both conditions) | same (`work_rate`) | same | prelim (E07) |
| C4 | The capitalist market never trades, so inequality stays ~0 (negative result) | 0 trades in 20 runs; Gini c1 0.019, c2 0.0 | same (`trades`, `gini`) | same | prelim (E07) |
| C5 | The LLM overseer never acts despite thefts every run (negative result) | Bond kills 0 in 20 runs; thefts per run c1 9.5, c2 6.5 | same (`bond_kills`, `thefts`) | same | prelim (E07) |

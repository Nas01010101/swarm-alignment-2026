# Claim → evidence map

Every number in the report appears here first. A claim without a file is not in the report.

| # | Claim (as worded in report) | Number(s) | Source file | Script | Status |
|---|---|---|---|---|---|
| 1 | Clean runs produce no accusations | exact 1.00, k=0, all topologies | `results/E01/sweep.jsonl` | `experiments/E01_synthetic_diagnosability/run.py` | prelim (v1) |
| 2 | Star topologies are near-undiagnosable | exact ≤0.05 for k≥1 | same | same | prelim (v1) |
| 3 | Naive discrepancy counting blames honest agents | 1.4–5.8 false acc./run | same | same | prelim (v1) |
| 4 | A liar who hides a message is always narrowed to itself and the receiver (one liar) | 175/175 hidden-message runs localized; 0/40 `minimal` controls name the liar alone | `results/E02/summary.json` (`H1_*`, `H2_minimal_exact`), `results/E02/runs.jsonl` | `experiments/E02_llm_swarm_tamper/{run,analyze}.py` | prelim (E02) |
| 5 | The detector accuses no one on untampered LLM-swarm logs | 40/40 `clean`, 0 false accusations | `results/E02/summary.json` (`H1_noedit_clean`, `H4_detector_fa_noedit`) | same | prelim (E02) |
| 6 | LLM liars make the smallest possible edit, whether or not told how the detector works | minimal_edit naive 0.91 [0.84,0.95], crosscheck 0.93 [0.86,0.96], detector-aware 0.95 [0.90,0.98]; n=120 each; 3 open models | `results/E02/summary.json` (`H3_minimal_edit_by_condition`) | same | prelim (E02) |
| 7 | The content-free detector localizes LLM liars far more often than an LLM judge that reads the messages | localized 0.80 [0.76,0.84] vs judge flagged 0.28 [0.23,0.32], n=360 | `results/E02/summary.json` (`H4_llm_rows_*`), `results/E02/judge.jsonl` | same | prelim (E02) |
| 8 | The LLM judge accuses honest agents on untampered logs | 1.13 honest agents accused per run (n=40); judge = gemma-4-31b-it | `results/E02/summary.json` (`H4_judge_mean_fa_noedit`) | same | prelim (E02) |
| 9 | Two liars hiding messages sent to the same honest agent frame that agent | honest receiver identified as the tamperer in 45/45 LLM runs and 5/5 `minimal` controls; **only 5 distinct swarms** (repeats across models × conditions are not independent) | `results/E02/summary.json` (`k2_by_receiver`), `results/E02/swarms.json` | same | prelim (E02); not pre-registered, needs E02b |
| 10 | With distinct honest receivers, two liars are still localized with no false accusations | localized 0.97, honest agents accused 0/117 (13 swarms) | `results/E02/summary.json` (`k2_by_receiver.llm_distinct_receivers`) | same | prelim (E02) |

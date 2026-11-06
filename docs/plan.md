# Plan

Four people, four workstreams, one shared library. Fill in names when roles are claimed.

| Workstream | Owner | Output | Depends on |
|---|---|---|---|
| A. Theory: diagnosability bound for swarm logs (comparison model), collusion + echo extension | _TBD_ | `docs/theory.md`, a proposition with proof sketch, predicted curves | — |
| B. LLM swarm runs (E02): agents on a real task; liars instructed to cover tracks, naive and detector-aware | _TBD_ | `results/E02/`, spend log | `sim.py`, `llm.py` |
| C. Real data (E03): AI Village transcripts → per-agent `Logs`, plant tampering, measure | _TBD_ | `scripts/fetch_ai_village.py`, `results/E03/` | `events.py` |
| D. Baselines, figures, report | _TBD_ | LLM-judge transcript monitor baseline, figures, `report/` | A–C |

## Timeline (ET)
| When | Milestone |
|---|---|
| Fri Nov 6 evening | Roles claimed. Everyone runs tests + E01. A starts bound; C inspects dataset schema; B smoke-tests one LLM run. |
| Sat Nov 7 12:00 | Go/no-go on real data (C). E02 first full sweep (B). Bound stated (A). |
| Sat Nov 7 20:00 | All headline numbers exist. D has figure drafts. `report/claims.md` populated. |
| Sun Nov 8 12:00 | First full report draft. Red-team pass: each person attacks another's section. |
| Sun Nov 8 18:00 | **Freeze.** Only fixes. Submit by 22:00 ET; resubmit same title if needed. |
| Mon Nov 9 06:59 | Hard deadline (AoE). |

## Decision log
- 2026-11-06: chose F1 over B1–B3; B2/B3 largely covered by 2025–26 papers (see `docs/ideas.md`).

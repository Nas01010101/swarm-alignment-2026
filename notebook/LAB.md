# Lab notebook

Append-only. Newest at the bottom. Format: `## YYYY-MM-DD HH:MM UTC — name — EXX`.

## 2026-11-06 17:50 UTC — Anas — setup / E01
- Read sprint page; chose F1 (witness-free tamper forensics) — rationale in `docs/ideas.md`.
- Prior-art check: witness-based approaches exist (HANSARD, Audita, agent-audit-integrity); interventional
  collusion detection and epidemic thresholds are covered (Audit the Whisper; Le et al.; Baltaji et al.).
  Did not find witness-free cross-log diagnosis. Search was 3 Exa queries, not exhaustive; A should re-check.
- E01 harness run, n=12, rate 0.2, 8 rounds, 20 seeds → `results/E01/sweep.jsonl`.
  complete: exact 0.90/0.75/0.60/0.25 for k=1..4, false accusations ≤0.15.
  star: exact ≤0.05 for k≥1; k≥2 → 0.70 false accusations per run (min cover picks the honest hub).
  naive count baseline: 1.4–5.8 false accusations per run. k=0: 1.00 exact everywhere.
- Collusion barely moves numbers at n=12 because few liar–liar edges carry tampering; needs higher k/rate.
- Next: v2 sweep per prereg; formal bound (A); first LLM run (B); dataset schema (C).

# Report outline (≤8 pages + appendices, official template)

Working title: *When the suspects write the logs: witness-free tamper forensics for agent swarms*

1. **Introduction** — HF incident: agents spoofed tool calls (~7% of reviewed transcripts). Existing fixes need a
   witness deployed beforehand. Question: with only suspect-written logs, what can be proven? Contributions list.
2. **Related work** — witnessed logging (HANSARD, Audita); collusion detection; system-level diagnosis (PMC, MM).
3. **Model** — logs, tampering ops, threat model (single, multiple, colluding liars), reduction to comparison
   diagnosis, bound + blind spots.
4. **Methods** — synthetic sweep (E01), LLM liars (E02), AI Village transplant (E03); baselines: naive count,
   LLM transcript judge; metrics.
5. **Results** — Fig 1: exact rate vs liars per topology with predicted bound overlaid. Fig 2: LLM liars incl.
   detector-aware. Table: real-graph statistics + results.
6. **Discussion** — what a deployer should do (topology choices, where to put one witness), limits.
- Appendix A: Limitations and Dual-Use / Ethical Considerations (required).
- Appendix B: prompts, seeds, models, spend. Appendix C: proofs.

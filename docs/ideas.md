# Ideas

Selection rule: attack something the field treats as unsolved or impossible, where a weekend can produce a
theorem-shaped prediction *and* an empirical test of it. Each idea carries the kill test that would drop it.

## F1 (chosen) — Logs that testify against each other
**The "impossible" part.** After the HF incident, agents spoofed their own tool calls in ~7% of reviewed
transcripts (METR 2026, via sprint page). Current answers all add a trusted witness *before* the incident:
gateway proxies and hash-chained logs (agent-audit-integrity), Merkle-committed signed messages (Audita,
arXiv 2608.22160), TEE witnesses at choke points (HANSARD, arXiv 2608.22512). HANSARD states the premise
directly: the record is produced by the suspects. Nobody we found answers the post-hoc case: **no witness was
deployed, every log was written by a suspect. What can still be proven?**

**Move.** Every message is logged by both endpoints. A liar can rewrite its own log, never its peer's. Each
message is therefore a mutual test, which is exactly the comparison model of system-level diagnosis
(Preparata–Metze–Chien 1967; Maeng–Malek 1981). Diagnosability theory then gives *predictions*:
- attribution is unique only while #liars ≤ a bound set by the communication graph (min degree / connectivity);
- star topologies are near-undiagnosable (hub vs leaf ambiguity); complete graphs degrade gracefully;
- colluding liars are invisible on their mutual edges, visible only through third-party echoes
  (an honest agent quoting or acting on the hidden message).

**Contribution.** (1) the reduction + bound adapted to swarm logs; (2) a content-free detector that answers
"identified / insufficient evidence" instead of guessing; (3) tests on synthetic, LLM, and real (AI Village)
logs with planted tampering; (4) the blind-spot map: what tamperers can do that no witness-free method catches.

**Early signal (E01, synthetic, 20 seeds, n=12, see `results/E01/sweep.jsonl`).** Complete graph: exact
attribution 0.90 → 0.25 as liars go 1 → 4, with ~0 false accusations; star: ≤0.05 exact and 0.70 false
accusations once ≥2 leaves lie (parsimony blames the honest hub). On the complete graph the naive "count
discrepancies" baseline accuses 2.9–5.8 honest agents per run. Matches the min-degree prediction qualitatively; needs the formal bound.

**Kill tests.**
- Novelty: a paper doing cross-transcript consistency forensics without a witness → reframe around the bound.
- Real data: AI Village logs lack per-agent views of shared messages → use their group-chat redundancy
  (multiple agents quoting the same message) or fall back to Swarm Traces + LLM sims.
- Value: LLM agents asked to tamper "strategically" (knowing the detector) get the liar set below the bound
  without collusion → that is a headline result too; publish the attack.

## B1 — Copies that collude without a channel
Untrusted model monitored by a copy of itself. Measure Schelling-point coordination with no channel, then
whether monitor diversity (other model, paraphrased inputs) breaks it. Listed as a sprint example, so many
teams may pick it. Keep as backup or as an E04 extension: can a liar *pick its tampering* so its copy-monitor's
verdict flips?

## B2 — Interventional collusion detection
Paraphrase/permute the channel and test whether coordination drops. **Largely done**: "Audit the Whisper"
(arXiv 2510.04303) runs intervention sweeps; Mathew et al. (IJCNLP 2025) paraphraser mitigation; Kaur et al.
(arXiv 2608.19161) counterfactual block/replace for latent channels. Drop unless F1 dies.

## B3 — Epidemic thresholds for prompt infection
Spectral-radius R0 for injection spread. **Largely done**: Le et al. 2026 (Cybersecurity, multiplex MMCA),
Baltaji et al. (arXiv 2607.21912). Drop.

## Stretch for F1
- Third-party echo evidence: honest agents' later messages reference hidden content → raises diagnosability
  past the pairwise bound. Measure the gain.
- Tool-call records: tool outputs observed by multiple agents as a second redundancy layer.
- "Minimum witness": if you could add one witness, where? (vertex that maximises diagnosability).

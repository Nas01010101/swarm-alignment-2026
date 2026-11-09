# E08 — Scarcity, ledger hacking and a conservation barrier (synthetic, N = 200)

Owner: ben (with Claude Code) · Registered: 2026-11-08 ~20:50 UTC, committed before any grid run.
Paper C. Model: `src/swarm/scarcity.py`; barrier: `src/swarm/barrier.py`; runner: `run.py`; analysis: `analyze.py`.
Before registration: only unit tests (n ≤ 40, `tests/test_scarcity.py`, `tests/test_barrier.py`) and one timing call
(seed 999, outside the grid; no metrics printed). No grid cell has been run.

## Question
Does scarcity flip a mixed Capitalist/Communist swarm from honest production to ledger hacking, does the
flip differ between blocs and topologies, and does a content-free conservation barrier at the gateway stop it?

## Model (fixed now; defaults in `ScarcityConfig`)
N = 200 (100 Capitalists, 100 Communists), T = 30, need c = 1/agent/round, regeneration ρN.
PRODUCE: effort 0.1, +β = 0.15 real, claim 1. HACK: cost φ = 0.2, −κ = 0.3 real, claim 1 + δ = 5/3.
Food is free for all while the stock covers need; otherwise it is rationed ∝ 0.5 + claim (Communists: 0.5 + commune
mean claim). Initial stock 0.5N, cap 3N, S_min = 0.05N. Updates: exploration ε = 0.05, myopic best response
μ = 0.1, otherwise Fermi imitation of a random neighbour (T = 0.05, ideology-blind). One random seeded hacker at t = 1.
Governance: `unfiltered`; `naive_audit` (each hacker caught w.p. 0.15/round: claim zeroed, fine 1.0, drain still
happens); `dcbf_gateway` (barrier h = S − γC − S_min, γ = 0.05, α = 0.5; scales the whole hack action by λ).
Deviation from the Paper C spec: the strategy set is {produce, hack}; extraction is omitted.

**Derived thresholds (Proposition 1, all-honest state):** a shortage ever occurs iff ρ < ρ* = 1 − β = 0.85;
within T = 30 rounds iff ρ < 1 − β − s0/T ≈ 0.833. Under abundance hacking loses (φ > effort, nobody is rationed).
Under shortage a *Capitalist* gains food by hacking; a *Communist's* extra claim is diluted 100× by pooling, so
best response predicts Communists stay honest. Imitation across blocs can still spread hacking to them.

## Design
ρ ∈ {0.4, 0.6, 0.8, 1.0, 1.2, 1.5} × topology {complete, two_caveman (two bloc cliques, edges rewired p = 0.05),
small_world (WS k = 8, p = 0.1), scale_free (BA m = 3)} × governance (3) × seeds 0–19 = 1,440 episodes.
Graph and seeded hacker are shared across governance for the same (ρ, topology, seed) → paired comparisons.

## Hypotheses and thresholds (cell = ρ × topology × governance; means over 20 seeds)
- **H1 (scarcity flip, Capitalists).** Unfiltered: Capitalist hack share at t = 30 ≥ 0.5 in every topology for
  ρ ≤ 0.8, and overall hack share ≤ 0.10 in every topology for ρ ≥ 1.0.
- **H2 (bloc asymmetry).** Unfiltered, ρ ≤ 0.8: Capitalist minus Communist hack share at t = 30 > 0, paired
  bootstrap 95% CI over episodes excluding 0, pooled over topologies, in each ρ.
  Rival (spec's "commune moral hazard"): Communists hack as much or more.
- **H3 (barrier soundness, Prop 2).** Every `dcbf_gateway` episode with 0 infeasible rounds has S_t ≥ S_min in
  every round (required: 100%). Prediction: infeasible rounds occur only for ρ < 0.85 (exogenous drift), never at ρ ≥ 1.0.
- **H4 (exploit removed).** `dcbf_gateway`: overall hack share at t = 30 ≤ 0.10 in every cell.
- **H5 (welfare without freezing the economy).** For each ρ ≤ 0.8 (pooled over topologies): need met (mean over all
  rounds) and real production are higher under `dcbf_gateway` than `unfiltered`, paired bootstrap 95% CI excluding 0.

Exploratory (no threshold): topology effects on the Communist hack share (is two_caveman slower to spread across
blocs?); `naive_audit` vs the other two; time to first shortage; ledger inflation (claims / production).

## Falsifiers
H1 fails if any scarcity cell has Capitalist share < 0.5, or any abundance cell has overall share > 0.10.
H3 failing even once means `barrier.py` or the proposition is wrong: stop and fix before any paper claim.
H4/H5 failing means the barrier is sound but not useful in this model; report it.
A predicted solvency failure of the barrier under scarcity (infeasible rounds) is not a falsifier: the
gateway controls hacks, not consumption. Report the infeasible-round rate.

## Controls
Negative: abundance cells (ρ ≥ 1.0) must show no flip. Positive (barrier): `tests/test_barrier.py::
test_unfiltered_comparison_can_violate`. Determinism: identical rows for a repeated config (tested).

## Budget
$0. Under a minute of CPU.

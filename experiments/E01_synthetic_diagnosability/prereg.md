# E01 — Where does witness-free attribution break? (synthetic)

Owner: Anas · Registered: 2026-11-06 (first pass already run as a harness check; v2 thresholds below are fixed before the v2 sweep)

## Question
On synthetic swarms with planted tampering, how does exact liar identification depend on topology,
number of liars and collusion?

## Hypothesis and rival
- H1: exact-identification rate falls as liars approach the graph's min degree; star (min degree 1) fails at ≥1 liar;
  complete graph holds to k ≈ (n-1)/2 when tamper rate is high enough that every liar leaves discrepancies.
- Rival: failures come from liars who happened to tamper with nothing detectable (low rate), not from topology.
  Control: condition on n_tampered > 0 and sweep rate.

## Design
n ∈ {12, 24}; topology ∈ {complete, erdos(p=0.3), ring, star}; liars k ∈ 0..6; collude ∈ {F, T};
tamper rate ∈ {0.05, 0.2, 0.5}; rounds 8; 20 seeds per cell.

## Metric and threshold
`exact` and `false_accusations` from `run.py`. Support for H1: on complete graph exact ≥ 0.8 for k ≤ 2 at rate 0.2,
and star exact ≤ 0.1 for k ≥ 1. Clean runs (k=0): exact = 1.00 required (negative control).

## Falsifier
Ring and complete graphs show the same exact-rate curve, i.e. topology does not matter.

## Budget
$0, seconds.

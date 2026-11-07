# swarm-alignment-2026

Team entry for the [Apart Swarm Alignment Sprint](https://apartresearch.com/sprints/swarm-alignment-2026)
(Nov 6–8 2026), Track 4 (multi-agent oversight), with Track 3 overlap.

**Question.** When every agent in a swarm can rewrite its own logs and no trusted witness was deployed,
which tampering can still be detected and attributed, and which cannot?

**Approach.** Every inter-agent message is recorded by both endpoints, so each message acts as a mutual test.
Attribution reduces to system-level fault diagnosis (comparison model): the minimum vertex covers of the
discrepancy graph. The detector returns *identified*, *insufficient evidence* or *clean*, and never reads
message content. Experiments test the theory's predictions on synthetic swarms (E01), LLM agents that edit
their own logs (E02), and AI Village transcripts with planted tampering (E03).

## Quickstart
```bash
uv sync --group dev --extra llm --extra data
uv run --group dev pytest -q
uv run python experiments/E01_synthetic_diagnosability/run.py --seeds 20
```

## Repo map
- `AGENTS.md` — rules and workflow for humans and coding agents (read first)
- `docs/` — sprint facts and rubric, ideas and kill tests, plan and roles, related work
- `src/swarm/` — logs, swarm generators, tampering, diagnosis, model backends
- `experiments/EXX_*/` — pre-registration + runner per experiment
- `results/` — outputs cited by the report · `notebook/LAB.md` — lab notebook · `papers/<X>/` — outline, claim map, PDF

## Preexisting work
None. All code was written during the sprint, starting 2026-11-06.

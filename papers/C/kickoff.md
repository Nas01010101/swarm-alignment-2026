# Paper C kickoff (Apart Swarm Alignment Sprint)

## Scoring
- Judged by the sprint panel on the published Apart criteria (source: https://apartresearch.com/sprints)

## Test construction
- No hidden test set; the panel reads the report and code (source: https://apartresearch.com/sprints)

## Designer
- exposes: alignment failures that come from how many agents interact, not from one model
- obvious: a single-model safety eval that ignores the institution the agents act in
- hypothesis: the same model survives or collapses depending on institution (E08 H4, H6)
- hypothesis: the institutional effect holds when work and mobs are physical (E09 M1)

## Test conditions
- text islands at n=100, 3 institutions, 5 seeds (rebuild: experiments/E08_islands/run.py)
- Minecraft islands at n=50 (rebuild: experiments/E09_minecraft/run.py)

## Bar
- bar: none (judged)
- deadline: 2026-11-09T11:59Z

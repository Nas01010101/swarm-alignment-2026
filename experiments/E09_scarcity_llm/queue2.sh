#!/usr/bin/env bash
# Inserts E09c (prereg_e09c.md) before the replication stage: waits for queue.sh to reach stage 4, stops it,
# runs E09c, then reruns stages 4 and the fill pass (all runs are resumable). One process at a time (one pacer).
set -u
cd "$(dirname "$0")/../.."
until grep -q "=== stage 4 (pass 1)" results/E09/queue.log; do sleep 20; done
pkill -f "E09_scarcity_llm/queue.sh"; pkill -f "E09_scarcity_llm/run.py"; sleep 5
set -a; . ./.env; set +a
export SWARM_TOKEN_CAP=${SWARM_TOKEN_CAP:-60000000}
R="uv run python experiments/E09_scarcity_llm/run.py --rpm 40 --workers 10"
for pass in 1 2; do
  echo "=== E09c (pass $pass) $(date -u)"
  $R --models gemma-4-26b-a4b-it --economies c3 --rhos 1.0 --seeded 1 --seeds 10 \
     --governance unfiltered,constitutional_prompt,llm_judge,dcbf_gateway,hack_ban --outdir results/E09c --tag main
done
echo "=== resuming queue.sh (fills + replication) $(date -u)"
experiments/E09_scarcity_llm/queue.sh

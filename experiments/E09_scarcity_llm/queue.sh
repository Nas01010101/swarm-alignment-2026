#!/usr/bin/env bash
# E09 + E09b main queue, run strictly one stage at a time so one pacer (40 req/min) covers all calls.
set -u
cd "$(dirname "$0")/../.."
set -a; . ./.env; set +a
export SWARM_TOKEN_CAP=${SWARM_TOKEN_CAP:-60000000}
R="uv run python experiments/E09_scarcity_llm/run.py --rpm 40 --workers 10"
for pass in 1 2; do  # second pass fills any village that failed in the first (resumable)
  echo "=== stage 1 (pass $pass): E09 gemma c3 main $(date -u)"
  $R --models gemma-4-26b-a4b-it --economies c3 --seeds 20 --tag main
  echo "=== stage 2 (pass $pass): E09b gemma defenses $(date -u)"
  $R --models gemma-4-26b-a4b-it --economies c3 --rhos 0.6 --seeded 1 --seeds 10 \
     --governance constitutional_prompt,llm_judge,dcbf_gateway,hack_ban --outdir results/E09b --tag main
  echo "=== stage 3 (pass $pass): E07-link control $(date -u)"
  $R --models gemma-4-26b-a4b-it --economies c1,c2 --rhos 2.0 --seeded 0 --seeds 5 --no-loophole --tag control
  echo "=== stage 4 (pass $pass): E09 replication qwen + deepseek $(date -u)"
  $R --models qwen3.8-27b,deepseek-v4-flash --economies c3 --seeds 5 --tag main
done
echo "=== queue done $(date -u)"

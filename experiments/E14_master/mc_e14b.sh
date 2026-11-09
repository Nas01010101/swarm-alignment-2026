#!/bin/bash
# E14 Minecraft arm after Amendment 2: the remaining islands on the self-hosted Modal vLLM endpoint.
# Waits for the round-1 socialist run (pid $1) to exit, then two rounds of two islands and the capitalist
# rerun (its Adaption run died on HTTP 429 at about 05:33 UTC).
cd "$(dirname "$0")/../.." && set -a && . ./.env && set +a
export SWARM_BACKEND=openai OPENAI_BASE_URL="$MODAL_URL/v1" OPENAI_API_KEY="$MODAL_VLLM_KEY"
while kill -0 "$1" 2>/dev/null; do sleep 10; done
run() {  # island port prefix
  uv run --extra sim --extra llm python experiments/E09_minecraft/run.py --model gemma-4-26b-a4b-it --island "$1" --neutral \
    --loophole --n 60 --seed 0 --host 100.88.179.78 --port "$2" --prefix "$3" --workers 12 --tag e14_mc 2>&1 | grep -v '^\s*$' | tail -3
}
for pair in "directed commons" "capitalist_tax planned" "capitalist"; do
  set -- $pair
  ssh rtx 'cd ~/mc/bots && pkill -f "^node controller"; sleep 3; export PATH=~/mc/node-v20.18.1-linux-x64/bin:$PATH; (nohup node controller.js --n 60 --prefix a --cx 0 --cz 0 --listen 25580 > ctl_e14A_$(date +%H%M).log 2>&1 < /dev/null &); (nohup node controller.js --n 60 --prefix b --cx 300 --cz 0 --listen 25581 > ctl_e14B_$(date +%H%M).log 2>&1 < /dev/null &); sleep 6; ss -ltn | grep -c -E ":2558[01]"'
  sleep 30
  echo "round $1 ${2:-} $(date -u +%H:%M)"
  run "$1" 25580 a &
  [ -n "${2:-}" ] && run "$2" 25581 b &
  wait
done
echo "e14 mc done $(date -u +%H:%M)"

#!/bin/bash
# E13 Minecraft arm: one island at a time, fresh controller each (E09 conditions). Run from the repo root.
set -a; . ./.env; set +a
for cell in "commons" "directed" "socialist --neutral" "capitalist --neutral"; do
  ssh rtx 'pkill -f "^node controller"; sleep 2; cd ~/mc/bots && export PATH=~/mc/node-v20.18.1-linux-x64/bin:$PATH && (nohup node controller.js --n 50 --listen 25580 > ctl_e13_$(date +%H%M).log 2>&1 < /dev/null &) ; sleep 5; tail -n 2 $(ls -t ctl_e13_*.log | head -1)'
  sleep 20
  uv run --extra sim python experiments/E09_minecraft/run.py --model gemma-4-26b-a4b-it --island $cell \
    --n 50 --seed 0 --host 100.88.179.78 --port 25580 --tag e13_mc 2>&1 | grep -v '^\s*$' | tail -5
done

"""Self-hosted Gemma 4 26B-A4B on one Modal H100 with vLLM's OpenAI-compatible server.

Why: the Adaption key returned HTTP 429 with three text runs and two Minecraft runs on it, and E14 text
seed 1 died on it (prereg Amendment 2). Serving the same weights ourselves removes the rate limit.
Deploy: `MODAL_VLLM_KEY=... modal deploy experiments/E14_master/modal_vllm.py`. Use it with
SWARM_BACKEND=openai OPENAI_BASE_URL=<url>/v1 OPENAI_API_KEY=$MODAL_VLLM_KEY.
"""

import os
import subprocess

import modal

MODEL = "google/gemma-4-26B-A4B-it"
SERVED = "gemma-4-26b-a4b-it"  # the name run.py passes with --model, same as on Adaption

# A CUDA devel base ships nvcc; vLLM's sampler JIT-compiles a kernel at startup and failed on
# debian_slim with "Could not find nvcc".
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm", "huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
hf_cache = modal.Volume.from_name("hf-cache-gemma4", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-cache-gemma4", create_if_missing=True)
# The key is read from the local env at deploy time; vLLM reads VLLM_API_KEY itself.
key = modal.Secret.from_dict({"VLLM_API_KEY": os.environ.get("MODAL_VLLM_KEY", "")})

app = modal.App("swarm-gemma4-vllm")


@app.function(
    image=image,
    gpu="H100",
    scaledown_window=15 * 60,
    timeout=4 * 60 * 60,
    volumes={"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache},
    secrets=[modal.Secret.from_name("huggingface"), key],
)
@modal.concurrent(max_inputs=256)
@modal.web_server(port=8000, startup_timeout=30 * 60)
def serve():
    subprocess.Popen(
        ["vllm", "serve", MODEL, "--served-model-name", SERVED, "--host", "0.0.0.0", "--port", "8000",
         "--max-model-len", "16384", "--gpu-memory-utilization", "0.92"]
    )

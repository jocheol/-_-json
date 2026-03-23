FROM runpod/worker-comfyui:5.5.1-base

# ── 1. 최소 시스템 의존성만 ───────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake python3-dev \
    && pip install --no-cache-dir \
    insightface==0.7.3 onnxruntime-gpu facexlib ultralytics piexif \
    && apt-get purge -y build-essential cmake python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

# ── 2. Network Volume 심링크 ──────────────────────────────────
RUN rm -rf /comfyui/models && \
    ln -s /runpod-volume/models /comfyui/models && \
    ln -s /runpod-volume/custom_nodes /comfyui/custom_nodes

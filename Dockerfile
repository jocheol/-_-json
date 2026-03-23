FROM runpod/worker-comfyui:5.5.1-base

# ── handler.py 패치 ───────────────────────────────────────────
COPY patch_handler.py /tmp/patch_handler.py
RUN python3 /tmp/patch_handler.py && rm /tmp/patch_handler.py

# ── 1. 최소 시스템 의존성만 ───────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake python3-dev git \
    && pip install --no-cache-dir \
    insightface==0.7.3 onnxruntime-gpu facexlib ultralytics piexif dill \
    && apt-get purge -y build-essential cmake python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

# ── 2. Impact-Pack/Subpack 의존성 한번에 설치 ─────────────────
RUN git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Pack /tmp/impact-pack && \
    git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Subpack /tmp/impact-subpack && \
    pip install --no-cache-dir \
    -r /tmp/impact-pack/requirements.txt \
    -r /tmp/impact-subpack/requirements.txt && \
    rm -rf /tmp/impact-pack /tmp/impact-subpack /root/.cache/pip

# ── 3. Network Volume 심링크 ──────────────────────────────────
RUN rm -rf /comfyui/models && \
    ln -s /runpod-volume/models /comfyui/models

RUN ln -s /runpod-volume/custom_nodes/ComfyUI_InstantID /comfyui/custom_nodes/ComfyUI_InstantID && \
    ln -s /runpod-volume/custom_nodes/ComfyUI_IPAdapter_plus /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && \
    ln -s /runpod-volume/custom_nodes/comfyui_controlnet_aux /comfyui/custom_nodes/comfyui_controlnet_aux && \
    ln -s /runpod-volume/custom_nodes/ComfyUI_essentials /comfyui/custom_nodes/ComfyUI_essentials && \
    ln -s /runpod-volume/custom_nodes/ComfyUI-Impact-Pack /comfyui/custom_nodes/ComfyUI-Impact-Pack && \
    ln -s /runpod-volume/custom_nodes/ComfyUI-Impact-Subpack /comfyui/custom_nodes/ComfyUI-Impact-Subpack && \
    ln -s /runpod-volume/custom_nodes/image_math_fix.py /comfyui/custom_nodes/image_math_fix.py

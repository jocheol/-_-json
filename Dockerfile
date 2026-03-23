FROM runpod/worker-comfyui:5.5.1-base

# ── handler.py 패치 ───────────────────────────────────────────
COPY patch_handler.py /tmp/patch_handler.py
RUN python3 /tmp/patch_handler.py && rm /tmp/patch_handler.py

# ── 1. 시스템 의존성 + Python 패키지 ──────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake python3-dev git \
    && pip install --no-cache-dir \
    insightface==0.7.3 onnxruntime-gpu facexlib ultralytics piexif dill boto3 \
    && apt-get purge -y build-essential cmake python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

# ── 2. Custom Nodes (빌드 타임 GitHub 설치) ───────────────────
RUN git clone --depth=1 https://github.com/cubiq/ComfyUI_IPAdapter_plus \
        /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && \
    git clone --depth=1 https://github.com/ZHO-ZHO-ZHO/ComfyUI_InstantID \
        /comfyui/custom_nodes/ComfyUI_InstantID && \
    git clone --depth=1 https://github.com/Fannovel16/comfyui_controlnet_aux \
        /comfyui/custom_nodes/comfyui_controlnet_aux && \
    git clone --depth=1 https://github.com/cubiq/ComfyUI_essentials \
        /comfyui/custom_nodes/ComfyUI_essentials && \
    git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Pack \
        /comfyui/custom_nodes/ComfyUI-Impact-Pack && \
    git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Subpack \
        /comfyui/custom_nodes/ComfyUI-Impact-Subpack

# ── 3. Custom Node 의존성 설치 ────────────────────────────────
RUN pip install --no-cache-dir \
    -r /comfyui/custom_nodes/ComfyUI-Impact-Pack/requirements.txt \
    -r /comfyui/custom_nodes/ComfyUI-Impact-Subpack/requirements.txt \
    && rm -rf /root/.cache/pip

# ── 4. 로컬 파일 복사 ─────────────────────────────────────────
COPY image_math_fix.py /comfyui/custom_nodes/image_math_fix.py
COPY download_models.py /download_models.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

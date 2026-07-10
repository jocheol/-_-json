FROM runpod/worker-comfyui:5.1.0-base

# ── handler.py 패치 ───────────────────────────────────────────
COPY patch_handler.py /tmp/patch_handler.py
RUN python3 /tmp/patch_handler.py && python3 -m py_compile /handler.py && rm /tmp/patch_handler.py

# ── 1. 시스템 의존성 + Python 패키지 ──────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake python3-dev git \
    && pip install --no-cache-dir \
    "numpy==1.26.4" \
    "opencv-python-headless==4.9.0.80" \
    "opencv-python==4.9.0.80" \
    "opencv-contrib-python==4.9.0.80" \
    insightface==0.7.3 onnxruntime-gpu facexlib ultralytics piexif dill boto3 \
    && apt-get purge -y build-essential cmake python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

# ── 2. Custom Nodes (빌드 타임 GitHub 설치) ───────────────────
RUN git clone --depth=1 https://github.com/cubiq/ComfyUI_IPAdapter_plus \
        /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && \
    git clone --depth=1 https://github.com/cubiq/ComfyUI_InstantID \
        /comfyui/custom_nodes/ComfyUI_InstantID && \
    git clone --depth=1 https://github.com/Fannovel16/comfyui_controlnet_aux \
        /comfyui/custom_nodes/comfyui_controlnet_aux && \
    git clone --depth=1 https://github.com/cubiq/ComfyUI_essentials \
        /comfyui/custom_nodes/ComfyUI_essentials && \
    git clone --depth=1 --branch 8.28 https://github.com/ltdrdata/ComfyUI-Impact-Pack \
        /comfyui/custom_nodes/ComfyUI-Impact-Pack && \
    git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Subpack \
        /comfyui/custom_nodes/ComfyUI-Impact-Subpack && \
    git clone https://github.com/Gourieff/ComfyUI-ReActor \
        /comfyui/custom_nodes/ComfyUI-ReActor && \
    git -C /comfyui/custom_nodes/ComfyUI-ReActor \
        checkout 6ad6b35a4df250d14cb2abf0808c9ffedf59f747

# ── 3. Custom Node 의존성 설치 ────────────────────────────────
# constraints로 핵심 스택 고정: custom node reqs(특히 ReActor·controlnet_aux의 rembg/scipy)가
# numpy 2.x·scipy 1.16+·CUDA13용 onnxruntime으로 올려 ComfyUI 부팅이 깨지는 것 방지 (2026-07-10 장애)
RUN printf 'numpy==1.26.4\nscipy==1.13.1\nopencv-python==4.9.0.80\nopencv-python-headless==4.9.0.80\nopencv-contrib-python==4.9.0.80\nonnxruntime-gpu==1.19.2\nonnxruntime==1.19.2\n' > /tmp/constraints.txt \
    && PIP_CONSTRAINT=/tmp/constraints.txt pip install --no-cache-dir \
    -r /comfyui/custom_nodes/ComfyUI_InstantID/requirements.txt \
    -r /comfyui/custom_nodes/comfyui_controlnet_aux/requirements.txt \
    -r /comfyui/custom_nodes/ComfyUI_essentials/requirements.txt \
    -r /comfyui/custom_nodes/ComfyUI-Impact-Pack/requirements.txt \
    -r /comfyui/custom_nodes/ComfyUI-Impact-Subpack/requirements.txt \
    -r /comfyui/custom_nodes/ComfyUI-ReActor/requirements.txt \
    && pip uninstall -y onnxruntime onnxruntime-gpu \
    && pip install --no-cache-dir "onnxruntime-gpu==1.19.2" "numpy==1.26.4" "scipy==1.13.1" \
    && python3 -c "from scipy import integrate; import numpy, cv2, onnxruntime; print('[SANITY]', numpy.__version__, cv2.__version__, onnxruntime.__version__, onnxruntime.get_available_providers())" \
    && rm -rf /root/.cache/pip /tmp/constraints.txt

# ── 4. 로컬 파일 복사 ─────────────────────────────────────────
COPY image_math_fix.py /comfyui/custom_nodes/image_math_fix.py
COPY download_models.py /download_models.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ── 5. ComfyUI-Manager 의존성 검사 무력화 (부팅 108초 딜레이 제거) ──
# Manager 폴더는 유지 (Impact Pack 의존), requirements.txt/install.py만 삭제
RUN find /comfyui/custom_nodes -name "requirements.txt" -type f -delete && \
    find /comfyui/custom_nodes -name "install.py" -type f -delete

CMD ["/start.sh"]

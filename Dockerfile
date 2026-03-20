# 드림북 ComfyUI RunPod Serverless Worker
FROM runpod/worker-comfyui:5.5.1-base

# ── 1. 시스템 의존성 ──────────────────────────────────────────
RUN pip install --no-cache-dir \
    insightface \
    onnxruntime-gpu \
    facexlib \
    ultralytics \
    piexif

# ── 2. 커스텀 노드 설치 ───────────────────────────────────────
RUN git clone --depth=1 https://github.com/cubiq/ComfyUI_InstantID \
    /comfyui/custom_nodes/ComfyUI_InstantID && \
    pip install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI_InstantID/requirements.txt || true

RUN git clone --depth=1 https://github.com/cubiq/ComfyUI_IPAdapter_plus \
    /comfyui/custom_nodes/ComfyUI_IPAdapter_plus && \
    pip install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI_IPAdapter_plus/requirements.txt || true

RUN git clone --depth=1 https://github.com/Fannovel16/comfyui_controlnet_aux \
    /comfyui/custom_nodes/comfyui_controlnet_aux && \
    pip install --no-cache-dir -r /comfyui/custom_nodes/comfyui_controlnet_aux/requirements.txt || true

RUN git clone --depth=1 https://github.com/cubiq/ComfyUI_essentials \
    /comfyui/custom_nodes/ComfyUI_essentials && \
    pip install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI_essentials/requirements.txt || true

RUN git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Pack \
    /comfyui/custom_nodes/ComfyUI-Impact-Pack && \
    pip install --no-cache-dir -r /comfyui/custom_nodes/ComfyUI-Impact-Pack/requirements.txt || true && \
    python /comfyui/custom_nodes/ComfyUI-Impact-Pack/install.py || true

RUN git clone --depth=1 https://github.com/ltdrdata/ComfyUI-Impact-Subpack \
    /comfyui/custom_nodes/ComfyUI-Impact-Subpack || true

RUN git clone --depth=1 https://github.com/exx8/differential-diffusion \
    /comfyui/custom_nodes/differential-diffusion
    

# ImageMultiply / ImageSubtract 커스텀 노드
COPY image_math_fix.py /comfyui/custom_nodes/image_math_fix.py

# ── 3. 모델 디렉토리 생성 ─────────────────────────────────────
RUN mkdir -p \
    /comfyui/models/checkpoints \
    /comfyui/models/instantid \
    /comfyui/models/controlnet \
    /comfyui/models/loras \
    /comfyui/models/upscale_models \
    /comfyui/models/ipadapter \
    /comfyui/models/clip_vision \
    /comfyui/models/insightface/models/antelopev2 \
    /comfyui/models/ultralytics/bbox \
    /comfyui/models/pulid

# ── 4. 메인 모델 다운로드 ────────────────────────────────────
# Juggernaut XL Ragnarok
RUN comfy model download \
    --url https://huggingface.co/RunDiffusion/Juggernaut-XL-v9/resolve/main/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors \
    --relative-path models/checkpoints \
    --filename juggernaut_xl_ragnarok.safetensors

# InstantID ip-adapter
RUN comfy model download \
    --url https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin \
    --relative-path models/instantid \
    --filename ip-adapter.bin

# InstantID ControlNet (올바른 URL)
RUN comfy model download \
    --url https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/diffusion_pytorch_model.safetensors \
    --relative-path models/controlnet \
    --filename instantid_sdxl.safetensors

# Depth ControlNet SDXL
RUN comfy model download \
    --url https://huggingface.co/xinsir/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors \
    --relative-path models/controlnet \
    --filename controlnet_depth_sdxl.safetensors

# 3D Animation Style LoRA
RUN wget -q -O /comfyui/models/loras/3d_animation_style_xl.safetensors \
    "https://civitai.com/api/download/models/226468?type=Model&format=SafeTensor&token=a4cb1c47d5deb6522cc4f0bc2b577e34"

# IPAdapter FaceID Plus v2 SDXL
RUN comfy model download \
    --url https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid-plusv2_sdxl.bin \
    --relative-path models/ipadapter \
    --filename ip-adapter-faceid-plusv2_sdxl.bin

# CLIP Vision
RUN comfy model download \
    --url https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors \
    --relative-path models/clip_vision \
    --filename CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors

# ESRGAN 4x AnimeSharp
RUN comfy model download \
    --url https://huggingface.co/Kim2091/AnimeSharp/resolve/main/4x-AnimeSharp.pth \
    --relative-path models/upscale_models \
    --filename 4x-AnimeSharp.pth

# YOLOv8 Face Detector
RUN comfy model download \
    --url https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt \
    --relative-path models/ultralytics/bbox \
    --filename face_yolov8m.pt

# ── 5. InsightFace antelopev2 모델 (5개) ─────────────────────
RUN wget -q -O /comfyui/models/insightface/models/antelopev2/glintr100.onnx \
    https://huggingface.co/MonsterMMORPG/tools/resolve/main/glintr100.onnx && \
    wget -q -O /comfyui/models/insightface/models/antelopev2/genderage.onnx \
    https://huggingface.co/MonsterMMORPG/tools/resolve/main/genderage.onnx && \
    wget -q -O /comfyui/models/insightface/models/antelopev2/scrfd_10g_bnkps.onnx \
    https://huggingface.co/MonsterMMORPG/tools/resolve/main/scrfd_10g_bnkps.onnx && \
    wget -q -O /comfyui/models/insightface/models/antelopev2/2d106det.onnx \
    https://huggingface.co/MonsterMMORPG/tools/resolve/main/2d106det.onnx && \
    wget -q -O /comfyui/models/insightface/models/antelopev2/1k3d68.onnx \
    https://huggingface.co/MonsterMMORPG/tools/resolve/main/1k3d68.onnx

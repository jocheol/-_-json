#!/usr/bin/env bash
set -e

TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

echo "[START] R2 모델 다운로드 시작..."
python3 /download_models.py

echo "[START] 모델 준비 완료. ComfyUI 시작..."
comfy-manager-set-mode offline || echo "worker-comfyui - Could not set ComfyUI-Manager network_mode" >&2

: "${COMFY_LOG_LEVEL:=DEBUG}"

if [ "$SERVE_API_LOCALLY" == "true" ]; then
    # 여기에 --fp32-vae 옵션을 추가했습니다.
    python -u /comfyui/main.py --disable-auto-launch --disable-metadata --listen --bf16-unet --fp32-vae --normalvram --verbose "${COMFY_LOG_LEVEL}" --log-stdout &
    python -u /handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    # 여기에도 --fp32-vae 옵션을 추가했습니다.
    python -u /comfyui/main.py --disable-auto-launch --disable-metadata --bf16-unet --fp32-vae --normalvram --verbose "${COMFY_LOG_LEVEL}" --log-stdout &
    python -u /handler.py
fi

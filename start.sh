#!/bin/bash
set -e

echo "[START] R2 모델 다운로드 시작..."
python3 /download_models.py

echo "[START] 모델 준비 완료. ComfyUI 워커 시작..."
exec python3 -u /handler.py

#!/usr/bin/env python3
"""R2에서 ComfyUI 모델 병렬 다운로드
- ThreadPoolExecutor (max_workers=4) 병렬 다운로드
- .part 임시 파일 → os.replace() 원자적 교체
- head_object 크기 검증 (불완전 파일 자동 재다운로드)
"""
import os, sys, threading
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

MODELS = [
    ('models/checkpoints/juggernaut_xl_ragnarok.safetensors',
     '/comfyui/models/checkpoints/juggernaut_xl_ragnarok.safetensors'),
    ('models/controlnet/instantid_sdxl.safetensors',
     '/comfyui/models/controlnet/instantid_sdxl.safetensors'),
    ('models/controlnet/controlnet_depth_sdxl.safetensors',
     '/comfyui/models/controlnet/controlnet_depth_sdxl.safetensors'),
    ('models/instantid/ip-adapter.bin',
     '/comfyui/models/instantid/ip-adapter.bin'),
    ('models/ipadapter/ip-adapter-faceid-plusv2_sdxl.bin',
     '/comfyui/models/ipadapter/ip-adapter-faceid-plusv2_sdxl.bin'),
    ('models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors',
     '/comfyui/models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors'),
    ('models/loras/3d_animation_style_xl.safetensors',
     '/comfyui/models/loras/3d_animation_style_xl.safetensors'),
    ('models/upscale_models/4x-AnimeSharp.pth',
     '/comfyui/models/upscale_models/4x-AnimeSharp.pth'),
    ('models/ultralytics/bbox/face_yolov8m.pt',
     '/comfyui/models/ultralytics/bbox/face_yolov8m.pt'),
    ('models/insightface/models/antelopev2/1k3d68.onnx',
     '/comfyui/models/insightface/models/antelopev2/1k3d68.onnx'),
    ('models/insightface/models/antelopev2/2d106det.onnx',
     '/comfyui/models/insightface/models/antelopev2/2d106det.onnx'),
    ('models/insightface/models/antelopev2/genderage.onnx',
     '/comfyui/models/insightface/models/antelopev2/genderage.onnx'),
    ('models/insightface/models/antelopev2/glintr100.onnx',
     '/comfyui/models/insightface/models/antelopev2/glintr100.onnx'),
    ('models/insightface/models/antelopev2/scrfd_10g_bnkps.onnx',
     '/comfyui/models/insightface/models/antelopev2/scrfd_10g_bnkps.onnx'),
    ('models/vae/sdxl_vae_fp16_fix.safetensors',
     '/comfyui/models/vae/sdxl_vae_fp16_fix.safetensors'),
    ('models/zoedepth-nyu-kitti/config.json',
     '/root/.cache/huggingface/hub/models--Intel--zoedepth-nyu-kitti/snapshots/main/config.json'),
    ('models/zoedepth-nyu-kitti/model.safetensors',
     '/root/.cache/huggingface/hub/models--Intel--zoedepth-nyu-kitti/snapshots/main/model.safetensors'),
    ('models/zoedepth-nyu-kitti/preprocessor_config.json',
     '/root/.cache/huggingface/hub/models--Intel--zoedepth-nyu-kitti/snapshots/main/preprocessor_config.json'),
]

_print_lock = threading.Lock()
_thread_local = threading.local()


def log(msg):
    with _print_lock:
        print(msg, flush=True)


def get_s3():
    """스레드별 독립 boto3 클라이언트 (thread-safe)"""
    if not hasattr(_thread_local, 's3'):
        _thread_local.s3 = boto3.client(
            's3',
            endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
            region_name='auto',
            config=Config(max_pool_connections=20),
        )
    return _thread_local.s3


def download_one(idx, total, key, dst):
    name = os.path.basename(dst)
    s3 = get_s3()
    bucket = os.environ['R2_BUCKET']

    r2_size = s3.head_object(Bucket=bucket, Key=key)['ContentLength']
    gb = r2_size / 1e9

    if os.path.exists(dst) and os.path.getsize(dst) == r2_size:
        log(f'[{idx}/{total}] SKIP  {name} ({gb:.2f} GB)')
        return

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    part = dst + '.part'
    log(f'[{idx}/{total}] DOWN  {name} ({gb:.2f} GB)')
    try:
        s3.download_file(bucket, key, part)
        os.replace(part, dst)  # 원자적 교체
        log(f'[{idx}/{total}] DONE  {name}')
    except Exception:
        if os.path.exists(part):
            os.remove(part)
        raise


def main():
    for var in ('R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET'):
        if not os.environ.get(var):
            sys.exit(f'[ERROR] 환경변수 {var} 미설정')

    total = len(MODELS)
    tasks = [(i + 1, total, key, dst) for i, (key, dst) in enumerate(MODELS)]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download_one, *t): t for t in tasks}
        for f in as_completed(futures):
            if f.exception():
                *_, key, dst = futures[f]
                log(f'[ERROR] {os.path.basename(dst)}: {f.exception()}')
                raise f.exception()

    # ZoeDepth HF 캐시 refs 구조 생성
    refs_dir = '/root/.cache/huggingface/hub/models--Intel--zoedepth-nyu-kitti/refs'
    os.makedirs(refs_dir, exist_ok=True)
    with open(os.path.join(refs_dir, 'main'), 'w') as f:
        f.write('main')
    log('[ZoeDepth] HF 캐시 refs 생성 완료')

    log('[ALL] 모델 다운로드 완료')


if __name__ == '__main__':
    main()

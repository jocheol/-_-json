content = open('/handler.py').read()

# 패치 1: R2 URL 다운로드 지원
old1 = '''            # --- Strip Data URI prefix if present ---
            if "," in image_data_uri:
                # Find the comma and take everything after it
                base64_data = image_data_uri.split(",", 1)[1]
            else:
                # Assume it's already pure base64
                base64_data = image_data_uri
            # --- End strip ---

            blob = base64.b64decode(base64_data)  # Decode the cleaned data'''

new1 = '''            # --- Strip Data URI prefix if present ---
            if image_data_uri.startswith("http://") or image_data_uri.startswith("https://"):
                import urllib.request, time as _time
                _last_err = None
                for _attempt in range(3):
                    try:
                        _req = urllib.request.Request(
                            image_data_uri,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; ComfyUI-Worker/1.0)"}
                        )
                        with urllib.request.urlopen(_req) as r:
                            blob = r.read()
                        _last_err = None
                        break
                    except Exception as _e:
                        _last_err = _e
                        if _attempt < 2:
                            _time.sleep(1)
                if _last_err:
                    raise _last_err
            elif "," in image_data_uri:
                base64_data = image_data_uri.split(",", 1)[1]
                blob = base64.b64decode(base64_data)
            else:
                base64_data = image_data_uri
                blob = base64.b64decode(base64_data)'''

assert old1 in content, 'PATCH 1 FAILED: download target not found'
content = content.replace(old1, new1)

# 패치 2: /upload/image API 우회 → /comfyui/input/ 직접 쓰기 (ComfyUI 0.3.68 403 fix)
old2 = '''            # POST request to upload the image
            response = requests.post(
                f"http://{COMFY_HOST}/upload/image", files=files, timeout=30
            )
            response.raise_for_status()'''

new2 = '''            # Write directly to ComfyUI input directory (bypass /upload/image 403)
            import os as _os
            _os.makedirs("/comfyui/input", exist_ok=True)
            with open(f"/comfyui/input/{name}", "wb") as _f:
                _f.write(blob)'''

assert old2 in content, 'PATCH 2 FAILED: upload target not found'
content = content.replace(old2, new2)

# 패치 3: BUCKET_NAME 환경변수로 버킷명 고정 (단일 라인 → 들여쓰기 무관)
old3 = 's3_url = rp_upload.upload_image(job_id, temp_file_path)'
new3 = 's3_url = rp_upload.upload_image(_upload_prefix, temp_file_path, bucket_name=os.getenv("BUCKET_NAME", "dreambook-assets"))'
assert old3 in content, 'PATCH 3 FAILED: upload_image target not found'
content = content.replace(old3, new3, 1)

# 패치 5: R2 키에 worker/<yyyymmdd>/ prefix 주입 (Phase 3 개편, KST 기준)
old5 = '    job_id = job["id"]'
new5 = '''    job_id = job["id"]
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    _upload_prefix = f"worker/{_dt.now(_tz(_td(hours=9))).strftime('%Y%m%d')}/{job_id}"'''
assert old5 in content, 'PATCH 5 FAILED: job_id declaration not found'
content = content.replace(old5, new5, 1)

open('/handler.py', 'w').write(content)
print('handler.py patch OK (URL download + direct file write + BUCKET_NAME fix + worker-prefix)')


# 패치 4: ComfyUI 서버 시작 대기 시간(500회 -> 4000회, 약 200초) 상향
old4_loop = 'for _ in range(500):'
new4_loop = 'for _ in range(4000):'
old4_msg = 'after 500 attempts'
new4_msg = 'after 4000 attempts'

if old4_loop in content:
    content = content.replace(old4_loop, new4_loop)
    content = content.replace(old4_msg, new4_msg)
    print('handler.py patch 4 (Timeout Retry Increase to 4000) OK')
else:
    print('WARNING: PATCH 4 FAILED - Could not find the 500 attempts loop.')

open('/handler.py', 'w').write(content)

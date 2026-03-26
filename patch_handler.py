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
new3 = 's3_url = rp_upload.upload_image(job_id, temp_file_path, bucket_name=os.getenv("BUCKET_NAME", "dreambook-assets"))'
assert old3 in content, 'PATCH 3 FAILED: upload_image target not found'
content = content.replace(old3, new3, 1)

open('/handler.py', 'w').write(content)
print('handler.py patch OK (URL download + direct file write + BUCKET_NAME fix)')

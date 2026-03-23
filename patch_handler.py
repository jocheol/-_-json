content = open('/handler.py').read()

old = '''            # --- Strip Data URI prefix if present ---
            if "," in image_data_uri:
                # Find the comma and take everything after it
                base64_data = image_data_uri.split(",", 1)[1]
            else:
                # Assume it's already pure base64
                base64_data = image_data_uri
            # --- End strip ---

            blob = base64.b64decode(base64_data)  # Decode the cleaned data'''

new = '''            # --- Strip Data URI prefix if present ---
            if image_data_uri.startswith("http://") or image_data_uri.startswith("https://"):
                import urllib.request
                with urllib.request.urlopen(image_data_uri) as r:
                    blob = r.read()
            elif "," in image_data_uri:
                base64_data = image_data_uri.split(",", 1)[1]
                blob = base64.b64decode(base64_data)
            else:
                base64_data = image_data_uri
                blob = base64.b64decode(base64_data)'''

assert old in content, 'PATCH FAILED: target string not found'
open('/handler.py', 'w').write(content.replace(old, new))
print('handler.py patch OK')

import io
import zipfile
import os
import boto3
import time
from pathlib import Path

backend_dir = Path('bridge/backend')
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(backend_dir):
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'uploads']):
            continue
        for f in files:
            if f.endswith('.pyc') or f.endswith('.env'):
                continue
            full_path = Path(root) / f
            rel_path = full_path.relative_to(backend_dir).as_posix()
            z.write(full_path, rel_path)

zip_bytes = buf.getvalue()
print(f'Packaged zip size: {len(zip_bytes)} bytes')

lam = boto3.client('lambda', region_name='us-east-1')
res = lam.update_function_code(FunctionName='bridge-backend-api', ZipFile=zip_bytes)
print('Lambda updated:', res.get('LastUpdateStatus', 'SUCCESS'))

time.sleep(5)
print('Ready!')


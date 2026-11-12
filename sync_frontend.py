import boto3
import os
import mimetypes
import time
from pathlib import Path

dist_dir = Path('bridge/frontend/dist')
s3 = boto3.client('s3', region_name='us-east-1')
cf = boto3.client('cloudfront', region_name='us-east-1')
bucket = 'bridge-ui-984625844016'

for root, _, files in os.walk(dist_dir):
    for f in files:
        full = Path(root) / f
        key = full.relative_to(dist_dir).as_posix()
        ct, _ = mimetypes.guess_type(full)
        if f.endswith('.html'):
            ct = 'text/html; charset=utf-8'
        elif f.endswith('.css'):
            ct = 'text/css'
        elif f.endswith('.js'):
            ct = 'application/javascript'
        extra = {'ContentType': ct}
        if key == 'index.html':
            extra['CacheControl'] = 'no-cache, no-store, must-revalidate'
        s3.upload_file(str(full), bucket, key, ExtraArgs=extra)
        print(f'Uploaded {key} ({ct})')

# Invalidate CloudFront
dists = cf.list_distributions()['DistributionList']['Items']
bridge_dist = None
for d in dists:
    for o in d['Origins']['Items']:
        if bucket in o['DomainName']:
            bridge_dist = d['Id']
            break

if bridge_dist:
    inv = cf.create_invalidation(
        DistributionId=bridge_dist,
        InvalidationBatch={
            'Paths': {'Quantity': 1, 'Items': ['/*']},
            'CallerReference': f'inv-{int(time.time())}'
        }
    )
    inv_id = inv['Invalidation']['Id']
    print(f'CloudFront invalidation created: {inv_id}')
else:
    print('Distribution not found')


import os
import boto3
from botocore.config import Config

access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if not access_key or not secret_key:
    raise RuntimeError("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY before running.")

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT", "http://127.0.0.1:8333"),
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

for bucket in ["datasets", "models"]:
    try:
        s3.create_bucket(Bucket=bucket)
        print(f"Created: {bucket}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"Already exists: {bucket}")

print("\nBuckets available:")
for bucket in s3.list_buckets()["Buckets"]:
    print("-", bucket["Name"])

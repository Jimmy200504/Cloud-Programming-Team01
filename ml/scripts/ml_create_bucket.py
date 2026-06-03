#!/usr/bin/env python3
"""Create the ML S3 bucket, including account-regional namespace buckets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ml.config import load_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket")
    parser.add_argument("--account-regional", action="store_true")
    args = parser.parse_args()

    import boto3
    from botocore.exceptions import ClientError

    config = load_config()
    bucket = args.bucket or config.s3_bucket
    s3 = boto3.client("s3", region_name=config.aws_region)

    try:
        s3.head_bucket(Bucket=bucket)
        print(json.dumps({"bucket": bucket, "status": "exists"}, indent=2))
        return 0
    except ClientError as exc:
        if exc.response["Error"]["Code"] not in {"404", "NoSuchBucket"}:
            raise

    request = {
        "Bucket": bucket,
        "CreateBucketConfiguration": {
            "LocationConstraint": config.aws_region,
        },
    }
    if args.account_regional:
        request["BucketNamespace"] = "account-regional"

    response = s3.create_bucket(**request)
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    print(
        json.dumps(
            {
                "bucket": bucket,
                "status": "created",
                "response": response,
                "public_access_block": "enabled",
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


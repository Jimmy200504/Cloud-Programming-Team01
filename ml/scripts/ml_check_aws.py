#!/usr/bin/env python3
"""Check whether AWS credentials and required ML resources are reachable."""

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
    parser.add_argument("--create-collection", action="store_true")
    args = parser.parse_args()

    import boto3
    from botocore.exceptions import ClientError

    config = load_config()
    sts = boto3.client("sts", region_name=config.aws_region)
    s3 = boto3.client("s3", region_name=config.aws_region)
    rekognition = boto3.client("rekognition", region_name=config.aws_region)
    transcribe = boto3.client("transcribe", region_name=config.aws_region)
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=config.aws_region)

    result: dict[str, object] = {
        "region": config.aws_region,
        "bucket": config.s3_bucket,
        "collection_id": config.face_collection_id,
    }

    result["identity"] = sts.get_caller_identity()
    s3.head_bucket(Bucket=config.s3_bucket)
    result["s3_bucket_ok"] = True

    try:
        result["rekognition_collection"] = rekognition.describe_collection(
            CollectionId=config.face_collection_id
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException" or not args.create_collection:
            raise
        rekognition.create_collection(CollectionId=config.face_collection_id)
        result["rekognition_collection_created"] = True

    transcribe.list_transcription_jobs(MaxResults=1)
    result["transcribe_ok"] = True

    bedrock_runtime.converse(
        modelId=config.bedrock_model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": "Return this exact JSON only: {\"ok\": true}"}],
            }
        ],
        inferenceConfig={"maxTokens": 32, "temperature": 0},
    )
    result["bedrock_ok"] = True
    result["bedrock_model_id"] = config.bedrock_model_id

    print(json.dumps(result, indent=2, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

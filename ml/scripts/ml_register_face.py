#!/usr/bin/env python3
"""Register one user face image into the Rekognition collection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ml.aws_utils import image_arg_from_path  # noqa: E402
from ml.config import load_config  # noqa: E402


EXTERNAL_IMAGE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()

    if not EXTERNAL_IMAGE_ID_RE.match(args.user_id):
        parser.error("--user-id may only contain letters, numbers, underscore, dash, colon, and dot")

    import boto3

    config = load_config()
    rekognition = boto3.client("rekognition", region_name=config.aws_region)
    response = rekognition.index_faces(
        CollectionId=config.face_collection_id,
        Image=image_arg_from_path(args.image),
        ExternalImageId=args.user_id,
        DetectionAttributes=["DEFAULT"],
        MaxFaces=1,
        QualityFilter="AUTO",
    )
    print(json.dumps(response, indent=2, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

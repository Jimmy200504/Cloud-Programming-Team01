#!/usr/bin/env python3
"""Run final AWS ML functions against local Pi image/audio paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ml import (  # noqa: E402
    ml_authenticate_face,
    ml_detect_food,
    ml_parse_expiration_date,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--face-image", required=True)
    parser.add_argument("--food-image", required=True)
    parser.add_argument("--expiration-audio", required=True)
    parser.add_argument("--expected-user-id")
    parser.add_argument("--captured-at", default="2026-06-03T10:30:00+08:00")
    parser.add_argument("--timezone", default="Asia/Taipei")
    parser.add_argument("--quiet", action="store_true", help="Only print final JSON.")
    args = parser.parse_args()

    total_start = perf_counter()
    responses: dict[str, Any] = {}
    timings: dict[str, float] = {}

    responses["face"], timings["face"] = _timed(
        "face auth",
        quiet=args.quiet,
        fn=lambda: ml_authenticate_face(
            {
                "request_id": "ml-smoke-face",
                "device_id": "smart-fridge-pi-001",
                "image": {"type": "local_path", "value": args.face_image},
                "expected_user_id": args.expected_user_id,
            }
        ),
    )
    responses["food"], timings["food"] = _timed(
        "food classification",
        quiet=args.quiet,
        fn=lambda: ml_detect_food(
            {
                "request_id": "ml-smoke-food",
                "device_id": "smart-fridge-pi-001",
                "image": {"type": "local_path", "value": args.food_image},
            }
        ),
    )
    responses["expiration"], timings["expiration"] = _timed(
        "expiration transcription + duration",
        quiet=args.quiet,
        fn=lambda: ml_parse_expiration_date(
            {
                "request_id": "ml-smoke-expiration",
                "device_id": "smart-fridge-pi-001",
                "timezone": args.timezone,
                "captured_at": args.captured_at,
                "audio": {"type": "local_path", "value": args.expiration_audio},
            }
        ),
    )
    timings["total"] = round(perf_counter() - total_start, 3)
    responses["_timing_seconds"] = timings

    print(json.dumps(responses, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all(responses[name]["status"] == "success" for name in ("face", "food", "expiration")) else 1


def _timed(name: str, *, quiet: bool, fn: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], float]:
    if not quiet:
        print(f"[START] {name}", flush=True)
    start = perf_counter()
    response = fn()
    elapsed = round(perf_counter() - start, 3)
    if not quiet:
        status = response.get("status", "unknown")
        print(f"[DONE]  {name}: {elapsed}s status={status}", flush=True)
    return response, elapsed


if __name__ == "__main__":
    raise SystemExit(main())

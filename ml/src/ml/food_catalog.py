"""Food catalog loading and validation."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from ml.errors import MLError, MLErrorCode


def load_food_catalog(path: str | None = None) -> list[dict[str, Any]]:
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    else:
        payload = json.loads(
            files("ml.config_data").joinpath("food_catalog.json").read_text(encoding="utf-8")
        )

    if not isinstance(payload, list) or not payload:
        raise MLError(MLErrorCode.INVALID_INPUT, "Food catalog must be a non-empty JSON array.")

    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise MLError(MLErrorCode.INVALID_INPUT, "Food catalog items must be objects.")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise MLError(MLErrorCode.INVALID_INPUT, "Food catalog item `id` is required.")
        if item_id in seen:
            raise MLError(MLErrorCode.INVALID_INPUT, "Food catalog contains duplicate ids.", {"id": item_id})
        seen.add(item_id)
    return payload


def catalog_ids(catalog: list[dict[str, Any]]) -> set[str]:
    return {str(item["id"]) for item in catalog}


"""Typed helpers for request and response payloads.

The public API intentionally accepts and returns dictionaries so HMI and Lambda
wrappers can integrate without importing custom classes. These aliases keep the
implementation readable while preserving that contract.
"""

from __future__ import annotations

from typing import Any, TypeAlias

JSONDict: TypeAlias = dict[str, Any]
MediaRef: TypeAlias = dict[str, str]


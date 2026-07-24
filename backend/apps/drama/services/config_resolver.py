# -*- coding: utf-8 -*-
"""配置覆盖策略解析（移植自 tools/lib/config_resolver.py）。"""
from __future__ import annotations

import copy
import fnmatch
from typing import Any, Iterable

from apps.core.exceptions import CONFIG_OVERLAY_FORBIDDEN, BusinessException


def flatten_leaves(data: dict[str, Any], prefix: str = "") -> Iterable[tuple[str, Any]]:
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten_leaves(value, path)
        else:
            yield path, value


def deep_set(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise BusinessException(
                CONFIG_OVERLAY_FORBIDDEN,
                f"路径与现有标量冲突: {path}",
                http_status=403,
            )
        current = child
    current[parts[-1]] = copy.deepcopy(value)


class ConfigResolver:
    """校验并应用 ops overlay。"""

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def apply_overlay(
        self,
        seed_files: dict[str, dict[str, Any]],
        overlay: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        resolved = copy.deepcopy(seed_files)
        allowed_files = self.policy.get("overlay_files") or {}
        for file_path, changes in (overlay.get("overrides") or {}).items():
            if file_path not in allowed_files:
                raise BusinessException(
                    CONFIG_OVERLAY_FORBIDDEN,
                    f"禁止覆盖文件: {file_path}",
                    http_status=403,
                )
            if file_path not in resolved:
                raise BusinessException(
                    CONFIG_OVERLAY_FORBIDDEN,
                    f"缺少种子配置: {file_path}",
                    http_status=403,
                )
            patterns = (allowed_files[file_path] or {}).get("allowed_paths") or []
            for leaf_path, value in flatten_leaves(changes):
                if not any(fnmatch.fnmatch(leaf_path, pattern) for pattern in patterns):
                    raise BusinessException(
                        CONFIG_OVERLAY_FORBIDDEN,
                        f"禁止覆盖路径: {file_path}#{leaf_path}",
                        http_status=403,
                    )
                deep_set(resolved[file_path], leaf_path, value)
        return resolved

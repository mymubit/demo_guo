"""配置覆盖、项目派生和运行参数投影参考实现。"""
from __future__ import annotations

import copy
import fnmatch
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from .condition_eval import deep_get, evaluate


def flatten_leaves(data: Dict[str, Any], prefix: str = "") -> Iterable[Tuple[str, Any]]:
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten_leaves(value, path)
        else:
            yield path, value


def deep_set(data: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"路径与现有标量冲突: {path}")
        current = child
    current[parts[-1]] = copy.deepcopy(value)


class OverlayPolicyError(ValueError):
    """后台覆盖越权或格式错误。"""


class ConfigResolver:
    def __init__(self, policy: Dict[str, Any]) -> None:
        self.policy = policy

    def apply_overlay(
        self,
        seed_files: Dict[str, Dict[str, Any]],
        overlay: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        resolved = copy.deepcopy(seed_files)
        allowed_files = self.policy.get("overlay_files") or {}
        for file_path, changes in (overlay.get("overrides") or {}).items():
            if file_path not in allowed_files:
                raise OverlayPolicyError(f"禁止覆盖文件: {file_path}")
            if file_path not in resolved:
                raise OverlayPolicyError(f"缺少种子配置: {file_path}")
            patterns = (allowed_files[file_path] or {}).get("allowed_paths") or []
            for leaf_path, value in flatten_leaves(changes):
                if not any(fnmatch.fnmatch(leaf_path, pattern) for pattern in patterns):
                    raise OverlayPolicyError(f"禁止覆盖路径: {file_path}#{leaf_path}")
                deep_set(resolved[file_path], leaf_path, value)
        return resolved

    def project_runtime_params(
        self,
        project_settings: Dict[str, Any],
        projection: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        context = copy.deepcopy(project_settings)
        context["deliverables"] = deep_get(
            project_settings, "creation_preferences.delivery_items"
        )
        for target, mappings in projection.items():
            condition = mappings.get("when")
            if condition and not evaluate(condition, context):
                continue
            params: Dict[str, Any] = {}
            for key, source_path in mappings.items():
                if key == "when":
                    continue
                value = deep_get(project_settings, source_path)
                if value is not None:
                    params[key] = copy.deepcopy(value)
            result[target] = params
        return result


@dataclass(frozen=True)
class ConfigRevision:
    revision: int
    value: Dict[str, Any]
    updated_by: str
    change_reason: str
    updated_at: str


class ConfigRevisionStore:
    """内存参考实现；网站应替换为带事务和权限的持久化存储。"""

    def __init__(self) -> None:
        self._history: List[ConfigRevision] = []

    def append(
        self,
        value: Dict[str, Any],
        updated_by: str,
        change_reason: str,
    ) -> ConfigRevision:
        revision = ConfigRevision(
            revision=len(self._history) + 1,
            value=copy.deepcopy(value),
            updated_by=updated_by,
            change_reason=change_reason,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(revision)
        return revision

    def rollback(self, revision: int, actor: str, reason: str) -> ConfigRevision:
        source = self.get(revision)
        return self.append(source.value, actor, reason)

    def get(self, revision: int) -> ConfigRevision:
        if revision < 1 or revision > len(self._history):
            raise KeyError(f"配置版本不存在: {revision}")
        return self._history[revision - 1]

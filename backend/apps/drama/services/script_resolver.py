from __future__ import annotations

from typing import Any


def resolve_latest_script(
    artifacts: dict[str, Any],
    episode_range: str | None = None,
) -> dict[str, Any]:
    for key in ("episode_scripts", "external_script"):
        value = artifacts.get(key)
        if value is None:
            continue
        if episode_range and isinstance(value, dict) and episode_range in value:
            return {"resolved_script_key": key, "value": value[episode_range]}
        return {"resolved_script_key": key, "value": value}
    raise ValueError("不存在可解析的 latest_script")

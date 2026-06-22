# -*- coding: utf-8 -*-
"""
Chunk 分片服务 — drama.* 新体系。

处理长内容 Agent（剧本执笔师、IP改编师等）的流式分片产物。
旧的 script/outline/polish 等 artifact_key 已替换为 drama.* 体系。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# drama.* 角色产物 → 分片流类型映射
# kind: 产物类型
# array_keys: 可能包含数组内容的 JSON 键路径（用于流式拼接）
DRAMA_ARTIFACT_CHUNK_MAP: Dict[str, Dict[str, Any]] = {
    # 剧本执笔师 - 最大产物，需要分片
    "episode_scripts": {
        "kind": "episode_scripts",
        "array_keys": ("episodes",),
    },
    # 情节架构师 - 分集大纲
    "series_outline": {
        "kind": "series_outline",
        "array_keys": ("episodes", "stages"),
    },
    # 修稿师/对白专家 - 也输出 episode_scripts
    # (同 episode_scripts，复用上面的配置)

    # 情绪架构师 - 情绪蓝图
    "emotion_blueprint": {
        "kind": "emotion_blueprint",
        "array_keys": ("episodes",),
    },
    # 节奏设计师 - 情绪曲线
    "emotion_curve": {
        "kind": "emotion_curve",
        "array_keys": ("episodes",),
    },
    # 分镜导演 - 分镜表
    "storyboard": {
        "kind": "storyboard",
        "array_keys": ("scenes",),
    },
}

# drama.* agent_id → 主要产物键映射
DRAMA_AGENT_PRIMARY_ARTIFACT: Dict[str, str] = {
    "drama.script-writer": "episode_scripts",
    "drama.dialogue-expert": "episode_scripts",
    "drama.script-editor": "episode_scripts",
    "drama.plot-architect": "series_outline",
    "drama.emotion-architect": "emotion_blueprint",
    "drama.rhythm-designer": "emotion_curve",
    "drama.storyboard-director": "storyboard",
    "drama.ip-adapter": "adaptation_plan",
}


def get_chunk_config(artifact_key: str) -> Optional[Dict[str, Any]]:
    """获取指定 artifact_key 的分片配置。"""
    return DRAMA_ARTIFACT_CHUNK_MAP.get(artifact_key)


def get_agent_primary_artifact(agent_id: str) -> Optional[str]:
    """获取指定 drama.* Agent 的主要产物键。"""
    return DRAMA_AGENT_PRIMARY_ARTIFACT.get(agent_id)


def resolve_chunk_kind(agent_id: str, params: Optional[Dict[str, Any]] = None) -> str:
    """根据 drama.* agent_id 解析分片产物类型。"""
    config = get_chunk_config(agent_id)
    if config:
        return config.get("kind", "episode_scripts")
    primary = get_agent_primary_artifact(agent_id)
    return primary or "episode_scripts"


def last_chunk_index(project: Any, kind: str = "episode_scripts") -> int:
    """获取最后一个分片的索引（用于续生成断点）。"""
    try:
        from apps.creation.artifact_service import get_artifact
        payload = get_artifact(project, kind) or {}
        items = payload.get("episodes", payload.get("scenes", []))
        if isinstance(items, list) and items:
            last = items[-1]
            return int(last.get("episodeNumber", last.get("index", len(items))))
    except Exception:  # noqa: BLE001
        pass
    return 0


def upsert_chunk(project: Any, kind: str, episode_number: int, content: Dict[str, Any]) -> None:
    """
    更新或插入分片内容到产物存储（drama.* 体系）。
    分片数据合并到 episode_scripts/series_outline 等产物中。
    """
    try:
        from apps.creation.artifact_service import get_artifact, save_artifact
        payload = get_artifact(project, kind) or {}
        items = payload.get("episodes", payload.get("scenes", []))
        if not isinstance(items, list):
            items = []
        # 更新或追加
        found = False
        for item in items:
            if item.get("episodeNumber") == episode_number or item.get("index") == episode_number:
                item.update(content)
                found = True
                break
        if not found:
            items.append({**content, "episodeNumber": episode_number})
        payload["episodes"] = sorted(items, key=lambda x: x.get("episodeNumber", x.get("index", 0)))
        save_artifact(project, kind, payload)
    except Exception:  # noqa: BLE001
        pass


def list_chunks(project: Any, *, kind: str = "episode_scripts", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    列出项目的流式分片产物（供前端分页读取）。
    drama.* 体系中，分片存储在 ProjectFusionArtifact 中。
    """
    try:
        from apps.creation.artifact_service import get_artifact

        payload = get_artifact(project, kind) or {}
        items = []
        if isinstance(payload, dict):
            # episode_scripts: {"episodes": [...]}
            for key in ("episodes", "scenes", "items"):
                raw = payload.get(key, [])
                if isinstance(raw, list):
                    items = raw
                    break
        paginated = items[offset:offset + limit]
        return {
            "kind": kind,
            "total": len(items),
            "offset": offset,
            "limit": limit,
            "items": paginated,
        }
    except Exception:  # noqa: BLE001
        return {"kind": kind, "total": 0, "offset": offset, "limit": limit, "items": []}

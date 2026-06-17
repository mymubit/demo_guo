# -*- coding: utf-8 -*-
"""
技能 Prompt 双读兼容层（Hint Resolver）

解决 P0 阶段标准化过程中的过渡问题：
- 优先从 AgentSkillDefinition 表读取 system_hint（运营可编辑）
- 未命中时 fallback 到原 hardcoded 提示词（保持线上不变）
- 灰度控制：通过 Admin 开关决定是否走 DB 版本

使用场景：
    from apps.skill.skills.skill_hint_resolver import resolve_system_hint

    hint = resolve_system_hint(
        skill_id="structure-generator",
        fallback_hint=_SUB_SKILL_SYSTEM_HINTS["structure-generator"],
        user_id=ctx.user_id,
        project_id=str(ctx.project_id),
    )

设计要点：
1. 进程内 TTL 缓存（默认 5 分钟）减少 DB 压力
2. SystemConfig.SKILL_HINT_DB_MODE 全局开关控制是否启用 DB 模式
3. 单技能灰度：gray_traffic_salt + user_id 哈希 % 100 < gray_weight
4. clear_cache() 供 Admin / Admin 后台修改提示词后强制刷新
5. 记录 hint_source（db / fallback / cached_db / cached_fallback）到日志便于监控
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# 进程内缓存：skill_id -> (system_hint, cached_at, version, hint_source)
_HINT_CACHE: Dict[str, Tuple[str, float, str, str]] = {}
_CACHE_TTL_SECONDS = 300  # 5 分钟

# 来源标签（写入日志与返回字典的 hint_source 字段）
HINT_SOURCE_DB = "db"
HINT_SOURCE_FALLBACK = "fallback"
HINT_SOURCE_CACHED_DB = "cached_db"
HINT_SOURCE_CACHED_FALLBACK = "cached_fallback"


def _now() -> float:
    """获取当前时间戳（秒，浮点）。"""
    return time.time()


def _is_cache_valid(cached_at: float) -> bool:
    """判断缓存是否仍在 TTL 内。"""
    return (_now() - cached_at) < _CACHE_TTL_SECONDS


def _is_db_mode_enabled() -> bool:
    """
    读取 SystemConfig.SKILL_HINT_DB_MODE 全局开关。

    返回 True 表示所有技能优先尝试 DB；返回 False 表示保持 legacy 模式。
    任意异常都降级为 False（保守：保持原硬编码提示词不变）。
    """
    try:
        from apps.system_config.services import SystemConfigService

        return SystemConfigService.get_bool("SKILL_HINT_DB_MODE", default_val=False)
    except Exception as exc:  # noqa: BLE001
        logger.debug("[HintResolver] 读取 SKILL_HINT_DB_MODE 失败: %s", exc)
        return False


def _hash_user_to_bucket(skill_id: str, user_id: Optional[int], salt: str) -> int:
    """
    将 user_id 哈希到 0-99 桶。

    算法：sha1(salt:user_id:skill_id) % 100，保证同一用户在同一技能上的分流稳定。
    灰度对照：bucket < gray_weight 即命中灰度。
    """
    if user_id is None:
        return -1
    raw = f"{salt}:{user_id}:{skill_id}".encode("utf-8")
    return int(hashlib.sha1(raw).hexdigest(), 16) % 100


def _fetch_db_hint(skill_id: str) -> Optional[Dict[str, Any]]:
    """
    从 AgentSkillDefinition 表查询 system_hint 与灰度元数据。

    优先匹配 lifecycle_status=active 的最新一条；若仅有 gray 状态，
    也返回以便单技能灰度判断。
    返回 dict: {"system_hint": str, "version": str, "gray_weight": int,
                "gray_traffic_salt": str, "lifecycle_status": str}
    未命中时返回 None。
    """
    try:
        from apps.skill.models import AgentSkillDefinition

        candidates = list(
            AgentSkillDefinition.objects.filter(skill_id=skill_id).order_by(
                "-published_at", "-updated_at", "-created_at"
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[HintResolver] DB 查询失败 skill=%s: %s", skill_id, exc)
        return None

    if not candidates:
        return None

    # 1) 优先 active（gray_weight=100）
    for row in candidates:
        if row.lifecycle_status == AgentSkillDefinition.LIFECYCLE_ACTIVE:
            return {
                "system_hint": row.system_hint or "",
                "version": row.version or "",
                "gray_weight": int(row.gray_weight or 0),
                "gray_traffic_salt": row.gray_traffic_salt or "",
                "lifecycle_status": row.lifecycle_status,
            }

    # 2) 其次 gray（用于单技能灰度判断）
    for row in candidates:
        if row.lifecycle_status == AgentSkillDefinition.LIFECYCLE_GRAY:
            return {
                "system_hint": row.system_hint or "",
                "version": row.version or "",
                "gray_weight": int(row.gray_weight or 0),
                "gray_traffic_salt": row.gray_traffic_salt or "",
                "lifecycle_status": row.lifecycle_status,
            }

    # 3) draft / deprecated 等：DB 中存在但未生效，仍返回以便调用方决定
    row = candidates[0]
    return {
        "system_hint": row.system_hint or "",
        "version": row.version or "",
        "gray_weight": int(row.gray_weight or 0),
        "gray_traffic_salt": row.gray_traffic_salt or "",
        "lifecycle_status": row.lifecycle_status,
    }


def _should_use_db(
    skill_id: str,
    db_row: Dict[str, Any],
    *,
    user_id: Optional[int],
    force_db: bool,
) -> bool:
    """
    判定本次调用是否使用 DB 版本的 system_hint。

    规则：
    1. force_db=True：始终 True
    2. 全局开关 SKILL_HINT_DB_MODE=on：True
    3. 技能处于 gray 状态：使用 gray_traffic_salt + user_id % 100 < gray_weight 决定
       - 无 user_id 时默认走 DB（保守便于测试）
    4. 其他情况 False（fallback）
    """
    if force_db:
        return True
    if _is_db_mode_enabled():
        return True

    lifecycle = db_row.get("lifecycle_status", "")
    if lifecycle == "gray":
        weight = int(db_row.get("gray_weight", 0))
        if weight <= 0:
            return False
        salt = db_row.get("gray_traffic_salt") or skill_id
        if user_id is None:
            # 无用户上下文（如内部批跑）默认走 DB 灰度
            return True
        bucket = _hash_user_to_bucket(skill_id, user_id, salt)
        return bucket < weight

    return False


def resolve_system_hint(
    skill_id: str,
    fallback_hint: str,
    *,
    user_id: Optional[int] = None,
    project_id: Optional[str] = None,
    force_db: bool = False,
) -> str:
    """
    解析技能 system hint。

    优先级：
    1. 强制 DB 模式（force_db=True）→ 始终读 DB，无 DB 数据时返回 fallback
    2. 全局开关 SKILL_HINT_DB_MODE=on → 读 DB，未命中时返回 fallback
    3. 单技能灰度：lifecycle_status=gray 时按 user_id 哈希分流
    4. Legacy 模式（默认）→ 返回 fallback

    Args:
        skill_id: 技能 ID（如 "structure-generator"）
        fallback_hint: 原硬编码的 system hint 字符串
        user_id: 当前用户 ID（用于单技能灰度分流；可空）
        project_id: 项目 ID（仅用于日志追踪，无逻辑作用）
        force_db: 强制走 DB（用于测试和单技能灰度；DB 无数据时返回 fallback）

    Returns:
        最终使用的 system hint 字符串
    """
    sid = (skill_id or "").strip()
    if not sid:
        return fallback_hint or ""

    fallback = fallback_hint or ""

    # 0) 缓存命中（且非 force_db）→ 直接返回
    if not force_db and sid in _HINT_CACHE:
        cached_hint, cached_at, cached_version, cached_source = _HINT_CACHE[sid]
        if _is_cache_valid(cached_at):
            logger.debug(
                "[HintResolver] cache hit skill=%s source=%s version=%s",
                sid, cached_source, cached_version,
            )
            return cached_hint

    # 1) 读取 DB 行
    db_row = _fetch_db_hint(sid)

    # 2) 判定是否走 DB
    use_db = False
    if db_row and db_row.get("system_hint"):
        use_db = _should_use_db(
            sid, db_row, user_id=user_id, force_db=force_db,
        )

    # 3) 返回 + 缓存 + 日志
    if use_db:
        chosen = db_row["system_hint"]
        version = db_row.get("version", "")
        source = HINT_SOURCE_DB
    else:
        chosen = fallback
        version = ""
        source = HINT_SOURCE_FALLBACK

    _HINT_CACHE[sid] = (chosen, _now(), version, source)

    if chosen is fallback:
        logger.info(
            "[HintResolver] resolve skill=%s project=%s user=%s → source=%s "
            "(lifecycle=%s, gray_weight=%s)",
            sid, project_id, user_id, source,
            (db_row or {}).get("lifecycle_status", "-"),
            (db_row or {}).get("gray_weight", 0),
        )
    else:
        logger.info(
            "[HintResolver] resolve skill=%s project=%s user=%s → source=%s version=%s",
            sid, project_id, user_id, source, version,
        )

    return chosen


def get_hint_source(skill_id: str) -> str:
    """
    返回最近一次 resolve 的来源标签（db / fallback / cached_db / cached_fallback）。
    缓存过期或无记录时返回空字符串。
    主要用于监控与单元测试。
    """
    sid = (skill_id or "").strip()
    if sid not in _HINT_CACHE:
        return ""
    _hint, cached_at, _version, source = _HINT_CACHE[sid]
    if not _is_cache_valid(cached_at):
        return ""
    return source


def clear_cache(skill_id: Optional[str] = None) -> int:
    """
    清除 hint 缓存。

    Args:
        skill_id: 指定技能 ID 时仅清除该条；为空时清除全部。

    Returns:
        实际清除的条数。
    """
    global _HINT_CACHE
    if skill_id:
        existed = _HINT_CACHE.pop(skill_id, None)
        cleared = 1 if existed is not None else 0
    else:
        cleared = len(_HINT_CACHE)
        _HINT_CACHE = {}
    logger.info("[HintResolver] clear_cache skill_id=%s cleared=%s", skill_id, cleared)
    return cleared


def get_cache_stats() -> Dict[str, Any]:
    """
    返回当前缓存统计信息，便于调试与监控。
    """
    now = _now()
    valid = 0
    expired = 0
    for _sid, (_hint, cached_at, _v, _s) in _HINT_CACHE.items():
        if _is_cache_valid(cached_at):
            valid += 1
        else:
            expired += 1
    return {
        "total": len(_HINT_CACHE),
        "valid": valid,
        "expired": expired,
        "ttl_seconds": _CACHE_TTL_SECONDS,
    }

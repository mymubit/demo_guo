# -*- coding: utf-8
"""SkillRuleConfig hybrid 模式下 content vs Item hash 校验（skill-agent/15 M4）。"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _stable_hash(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_hybrid_integrity(config) -> Optional[Dict[str, str]]:
    """hybrid 模式下比对 Config.content 与 active Item bodies；不一致则 warn。"""
    from apps.skill.models import SkillRuleConfig, SkillRuleItem

    if getattr(config, "content_source", SkillRuleConfig.CONTENT_HYBRID) != SkillRuleConfig.CONTENT_HYBRID:
        return None
    if not isinstance(config.content, dict):
        return None
    items = SkillRuleItem.objects.filter(
        config=config,
        status=SkillRuleConfig.STATUS_ACTIVE,
        item_type=SkillRuleItem.TYPE_RULE,
    ).order_by("sort_order", "rule_key")
    if not items.exists():
        return None
    item_digest = _stable_hash([{"k": i.rule_key, "b": i.body} for i in items])
    content_digest = _stable_hash(config.content)
    if item_digest != content_digest:
        logger.warning(
            "[SkillRuleHybrid] content hash mismatch config=%s section=%s item=%s content=%s",
            config.id,
            config.section,
            item_digest[:12],
            content_digest[:12],
        )
        return {"item_hash": item_digest, "content_hash": content_digest}
    return None

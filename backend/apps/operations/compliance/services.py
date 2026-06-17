"""合规规则服务。"""
from __future__ import annotations

import logging
import re
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from apps.operations.constants import ComplianceLevel
from apps.operations.exceptions import ComplianceRuleError

from .models import (
    ComplianceRule,
    ComplianceRuleVersion,
    SensitiveWord,
    TopicBlacklist,
    ViolationLog,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────

@transaction.atomic
def upsert_sensitive_word(
    *, word: str, category: str, level: str,
    description: str = "", is_active: bool = True, operator: str = "",
) -> SensitiveWord:
    obj, _ = SensitiveWord.objects.update_or_create(
        word=word[:128],
        defaults={
            "category": category, "level": level,
            "description": description[:255],
            "is_active": is_active, "created_by": operator or obj_created_by(word),
        },
    )
    return obj


def obj_created_by(word: str) -> str:
    return ""


@transaction.atomic
def toggle_sensitive_word(word: SensitiveWord, *, is_active: bool) -> SensitiveWord:
    word.is_active = is_active
    word.save(update_fields=["is_active", "updated_at"])
    return word


@transaction.atomic
def upsert_topic_blacklist(
    *, name: str, keywords: list, category: str, level: str,
    reason: str = "", is_active: bool = True, operator: str = "",
) -> TopicBlacklist:
    obj, _ = TopicBlacklist.objects.update_or_create(
        name=name[:128],
        defaults={
            "keywords": keywords or [],
            "category": category, "level": level,
            "reason": reason, "is_active": is_active,
            "created_by": operator,
        },
    )
    return obj


@transaction.atomic
def upsert_compliance_rule(
    *, name: str, description: str, category: str, level: str,
    rule_expr: dict, scope: str = "all",
    is_active: bool = True, operator: str = "",
) -> ComplianceRule:
    obj, _ = ComplianceRule.objects.update_or_create(
        name=name[:128],
        defaults={
            "description": description, "category": category,
            "level": level, "rule_expr": rule_expr or {},
            "scope": scope, "is_active": is_active,
            "created_by": operator,
        },
    )
    return obj


# ──────────────────────────────────────────────
# 检查
# ──────────────────────────────────────────────

def check_text(text: str, *, scope: str = "all") -> list[dict]:
    """对文本做合规检查。返回命中的 [{type, level, matched, rule, action}]。"""
    text = (text or "").strip()
    if not text:
        return []
    hits: list[dict] = []

    # 1) 敏感词
    for w in SensitiveWord.objects.filter(is_active=True).only("word", "level", "category"):
        if w.word and w.word in text:
            hits.append({
                "type": "sensitive_word",
                "category": w.category,
                "level": w.level,
                "matched": w.word,
                "rule": w.word,
                "action": _action_for_level(w.level),
            })

    # 2) 题材黑名单（关键词任意命中）
    for t in TopicBlacklist.objects.filter(is_active=True).only("name", "level", "keywords"):
        for kw in (t.keywords or []):
            if kw and kw in text:
                hits.append({
                    "type": "topic_blacklist",
                    "category": t.category,
                    "level": t.level,
                    "matched": kw,
                    "rule": t.name,
                    "action": _action_for_level(t.level),
                })
                break

    # 3) 复合规则
    for r in ComplianceRule.objects.filter(is_active=True).only(
        "name", "level", "category", "rule_expr", "scope"
    ):
        if r.scope != "all" and r.scope != scope:
            continue
        if _rule_match(r.rule_expr, text):
            hits.append({
                "type": "compliance_rule",
                "category": r.category,
                "level": r.level,
                "matched": text[:120],
                "rule": r.name,
                "action": _action_for_level(r.level),
            })

    return hits


def _action_for_level(level: str) -> str:
    if level == ComplianceLevel.P0:
        return "block"
    if level == ComplianceLevel.P1:
        return "warn"
    return "record"


def _rule_match(expr: dict, text: str) -> bool:
    """简单规则匹配：require / exclude 关键词 + 正则。"""
    if not expr:
        return False
    require = expr.get("require_words") or []
    exclude = expr.get("exclude_words") or []
    pattern = expr.get("pattern")

    if require and not all((w and w in text) for w in require):
        return False
    if exclude and any((w and w in text) for w in exclude):
        return False
    if pattern:
        try:
            if not re.search(pattern, text):
                return False
        except re.error:
            return False
    return bool(require or exclude or pattern)


# ──────────────────────────────────────────────
# 违规记录
# ──────────────────────────────────────────────

@transaction.atomic
def record_violations(
    *, user=None, project=None, hits: Iterable[dict], source: str = "auto",
) -> list[ViolationLog]:
    logs = []
    for h in hits or []:
        if not h:
            continue
        logs.append(ViolationLog.objects.create(
            user=user, project=project,
            category=h.get("category", "other"),
            level=h.get("level", ComplianceLevel.P2),
            source=source,
            matched_text=str(h.get("matched", ""))[:2000],
            rule_name=str(h.get("rule", ""))[:128],
            action_taken=str(h.get("action", "record"))[:64],
        ))
    if logs:
        logger.info("compliance.violation user=%s project=%s count=%s", user, project, len(logs))
    return logs


def has_blocking_hit(hits: list[dict]) -> bool:
    return any(h.get("action") == "block" for h in hits or [])


# ──────────────────────────────────────────────
# 版本快照
# ──────────────────────────────────────────────

@transaction.atomic
def publish_version(*, note: str = "", operator: str = "") -> ComplianceRuleVersion:
    """发布当前规则库为新版本（快照）。"""
    snapshot = {
        "sensitive_words": list(
            SensitiveWord.objects.values("word", "category", "level", "is_active", "description")
        ),
        "topic_blacklist": list(
            TopicBlacklist.objects.values("name", "keywords", "category", "level", "is_active", "reason")
        ),
        "rules": list(
            ComplianceRule.objects.values("name", "description", "category", "level", "rule_expr", "scope", "is_active")
        ),
    }
    last = ComplianceRuleVersion.objects.order_by("-published_at").first()
    n = 1 if not last else (int(last.version.lstrip("v") or 0) + 1)
    v = ComplianceRuleVersion.objects.create(
        version=f"v{n:04d}",
        snapshot=snapshot,
        note=note[:1000],
        published_by=operator[:64],
    )
    return v


@transaction.atomic
def handle_violation(log_id: int, *, operator: str, note: str = "") -> ViolationLog:
    try:
        v = ViolationLog.objects.get(pk=log_id)
    except ViolationLog.DoesNotExist:
        raise ComplianceRuleError("违规记录不存在")
    v.handled = True
    v.handled_by = operator[:64]
    v.handled_at = timezone.now()
    v.handle_note = note[:1000]
    v.save(update_fields=["handled", "handled_by", "handled_at", "handle_note"])
    return v

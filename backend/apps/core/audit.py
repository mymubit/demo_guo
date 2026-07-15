# -*- coding: utf-8 -*-
"""审计日志工具。"""
from __future__ import annotations

import logging
from typing import Any, Optional

from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger("apps.core.audit")


def audit_log(
    action: str,
    *,
    actor: Optional[AbstractBaseUser | str] = None,
    project_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    """结构化审计日志，供运维检索。"""
    actor_name = _actor_name(actor)
    payload = {
        "action": action,
        "actor": actor_name,
        "project_id": project_id,
        "detail": detail or {},
    }
    logger.info("audit %s", payload)


def _actor_name(actor: Optional[AbstractBaseUser | str]) -> str:
    if actor is None:
        return "system"
    if isinstance(actor, str):
        return actor
    return getattr(actor, "username", None) or str(actor.pk)

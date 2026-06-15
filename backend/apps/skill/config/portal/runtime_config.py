# -*- coding: utf-8 -*-
"""运行时开关 — SkillConfig DB 优先，环境变量 / settings 兜底。"""
from __future__ import annotations

import os
from typing import List

from django.conf import settings


class RuntimeConfigService:
    @staticmethod
    def _csv(raw: str) -> List[str]:
        return [part.strip() for part in str(raw or "").split(",") if part.strip()]

    @classmethod
    def dj_queue_queues(cls) -> List[str]:
        from apps.skill.config.portal.skill_settings import SkillConfigService

        configured = cls._csv(SkillConfigService.get("runtime.dj_queue.queues", ""))
        if configured:
            return configured
        env_val = os.getenv("DJ_QUEUE_QUEUES", "").strip()
        if env_val:
            return cls._csv(env_val)
        return list(getattr(settings, "DJ_QUEUE_QUEUES", []) or ["creation", "default", "evolve"])

    @classmethod
    def dj_queue_mode(cls) -> str:
        from apps.skill.config.portal.skill_settings import SkillConfigService

        configured = (SkillConfigService.get("runtime.dj_queue.mode", "") or "").strip()
        if configured:
            return configured
        return os.getenv("DJ_QUEUE_MODE", getattr(settings, "DJ_QUEUE_MODE", "async") or "async")

    @classmethod
    def dj_queue_worker_threads(cls) -> int:
        from apps.skill.config.portal.skill_settings import SkillConfigService

        configured = (SkillConfigService.get("runtime.dj_queue.worker_threads", "") or "").strip()
        if configured.isdigit():
            return max(1, int(configured))
        env_val = os.getenv("DJ_QUEUE_WORKER_THREADS", "").strip()
        if env_val.isdigit():
            return max(1, int(env_val))
        return max(1, int(getattr(settings, "DJ_QUEUE_WORKER_THREADS", 2) or 2))

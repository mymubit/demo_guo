# -*- coding: utf-8 -*-
"""LLM 调用日志持久化与查询。"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from apps.drama.models import DramaGenerationJob, DramaLlmCallLog, DramaProject
from apps.drama.services.llm_call_context import get_llm_call_context, set_last_llm_log_id

logger = logging.getLogger(__name__)

_PREVIEW_CHARS = 240

_ADMIN_ROLE_LABELS = {
    "admin.connectivity-test": "连通测试",
}

_role_label_cache: dict[str, str] = {}


def resolve_role_label(role: str) -> str:
    """将 agent_id 解析为中文角色名（优先 registry name_zh）。"""
    if not role:
        return ""
    cached = _role_label_cache.get(role)
    if cached is not None:
        return cached
    if role in _ADMIN_ROLE_LABELS:
        label = _ADMIN_ROLE_LABELS[role]
        _role_label_cache[role] = label
        return label
    try:
        from apps.drama.services.skills_loader import get_skills_loader

        entry = get_skills_loader().get_role_entry(role)
        label = str(entry.get("name_zh") or entry.get("name") or role)
    except Exception:
        label = role.replace("drama.", "").replace("admin.", "")
    _role_label_cache[role] = label
    return label


def _truncate_error(text: str, limit: int = 4000) -> str:
    """仅错误信息允许截断；三栏原文（system/user/response）禁止截断。"""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…(已截断，原文 {len(text)} 字符)"


def _store_raw_text(text: str, *, field: str) -> str:
    """
    调用日志三栏原文完整落库，便于排障。

    仅在极端超限时告警并硬截断（默认 5MB），正常评测剧本不会触发。
    """
    max_chars = int(getattr(settings, "LLM_CALL_LOG_MAX_TEXT_CHARS", 5_000_000) or 5_000_000)
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    logger.warning(
        "llm_call_log %s exceeded hard cap %s chars (len=%s); truncating for DB safety",
        field,
        max_chars,
        len(text),
    )
    return text[:max_chars] + f"\n…(已截断，原文 {len(text)} 字符)"


def _extract_response_text(response_json: dict[str, Any] | None) -> str:
    if not response_json:
        return ""
    try:
        return str(response_json["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError):
        return ""


def _extract_usage(response_json: dict[str, Any] | None) -> dict[str, int | None]:
    usage = (response_json or {}).get("usage") or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


class LlmCallLogService:
    @classmethod
    def is_enabled(cls) -> bool:
        return getattr(settings, "LLM_CALL_LOG_ENABLED", True)

    @classmethod
    @transaction.atomic
    def record(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        model_name: str,
        base_url: str,
        status: str,
        latency_ms: int,
        response_json: dict[str, Any] | None = None,
        response_text: str | None = None,
        http_status: int | None = None,
        error_message: str = "",
        project_id: str | None = None,
        job_id: str | None = None,
        role: str = "",
        purpose: str = "",
        actor: str = "system",
    ) -> DramaLlmCallLog | None:
        if not cls.is_enabled():
            return None

        ctx = get_llm_call_context()
        project_id = project_id or (ctx.project_id if ctx else None)
        job_id = job_id or (ctx.job_id if ctx else None)
        role = role or (ctx.role if ctx else "")
        purpose = purpose or (ctx.purpose if ctx else DramaLlmCallLog.Purpose.ARTIFACT_GENERATION)
        actor = actor or (ctx.actor if ctx else "system")

        seq_in_job = 0
        job = None
        if job_id:
            job = DramaGenerationJob.objects.filter(pk=job_id).first()
            if job:
                seq_in_job = job.llm_call_logs.count()

        project = None
        if project_id:
            project = DramaProject.objects.filter(pk=project_id).first()
        elif job and job.project_id:
            project = job.project

        body = response_json if isinstance(response_json, dict) else None

        text = response_text if response_text is not None else _extract_response_text(response_json)
        usage = _extract_usage(response_json if isinstance(response_json, dict) else None)

        try:
            log = DramaLlmCallLog.objects.create(
                project=project,
                generation_job=job,
                actor=actor,
                role=role,
                purpose=purpose,
                seq_in_job=seq_in_job,
                model_name=model_name,
                base_url=base_url,
                system_prompt=_store_raw_text(system_prompt, field="system_prompt"),
                user_prompt=_store_raw_text(user_prompt, field="user_prompt"),
                response_text=_store_raw_text(text, field="response_text"),
                response_body=body if isinstance(body, dict) else None,
                status=status,
                http_status=http_status,
                error_message=_truncate_error(error_message, 4000),
                latency_ms=latency_ms,
                prompt_tokens=usage["prompt_tokens"],
                completion_tokens=usage["completion_tokens"],
                total_tokens=usage["total_tokens"],
                provider_request_id=str((response_json or {}).get("id") or ""),
            )
            set_last_llm_log_id(str(log.id))
            logger.info(
                "llm_call_log role=%s purpose=%s status=%s latency_ms=%s job=%s",
                role,
                purpose,
                status,
                latency_ms,
                job_id,
            )
            return log
        except Exception:
            logger.exception("写入 LLM 调用日志失败")
            return None

    @classmethod
    def serialize_summary(cls, log: DramaLlmCallLog) -> dict[str, Any]:
        project = getattr(log, "project", None)
        project_title = ""
        if project is not None:
            project_title = (getattr(project, "title", None) or "").strip()
        job = getattr(log, "generation_job", None)
        job_status = getattr(job, "status", None) if job is not None else None
        job_error = ""
        if job is not None:
            job_error = (getattr(job, "error_message", None) or "").strip()
        return {
            "id": str(log.id),
            "project_id": str(log.project_id) if log.project_id else None,
            "project_title": project_title or None,
            "job_id": str(log.generation_job_id) if log.generation_job_id else None,
            "job_status": job_status or None,
            "job_error_message": job_error or None,
            "actor": log.actor,
            "role": log.role,
            "role_label": resolve_role_label(log.role),
            "purpose": log.purpose,
            "status": log.status,
            "model_name": log.model_name,
            "base_url": log.base_url,
            "latency_ms": log.latency_ms,
            "http_status": log.http_status,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "error_message": log.error_message or None,
            "seq_in_job": log.seq_in_job,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "system_prompt_preview": (log.system_prompt or "")[:_PREVIEW_CHARS] or None,
            "user_prompt_preview": (log.user_prompt or "")[:_PREVIEW_CHARS] or None,
            "response_preview": (log.response_text or "")[:_PREVIEW_CHARS] or None,
        }

    @classmethod
    def serialize_detail(cls, log: DramaLlmCallLog) -> dict[str, Any]:
        data = cls.serialize_summary(log)
        data.update(
            {
                "system_prompt": log.system_prompt,
                "user_prompt": log.user_prompt,
                "response_text": log.response_text,
                "response_body": log.response_body,
                "provider_request_id": log.provider_request_id or None,
            }
        )
        return data

    @classmethod
    def list_for_job(
        cls,
        job: DramaGenerationJob,
        *,
        role: str | None = None,
        limit: int = 50,
    ) -> QuerySet[DramaLlmCallLog]:
        qs = DramaLlmCallLog.objects.select_related("project", "generation_job").filter(
            generation_job=job
        )
        if role:
            qs = qs.filter(role=role)
        return qs.order_by("seq_in_job", "created_at")[:limit]

    @classmethod
    def list_for_project(
        cls,
        project: DramaProject,
        *,
        job_id: str | None = None,
        role: str | None = None,
        limit: int = 50,
    ) -> QuerySet[DramaLlmCallLog]:
        qs = DramaLlmCallLog.objects.select_related("project", "generation_job").filter(
            project=project
        )
        if job_id:
            qs = qs.filter(generation_job_id=job_id)
        if role:
            qs = qs.filter(role=role)
        return qs.order_by("-created_at")[:limit]

    @classmethod
    def list_global(
        cls,
        *,
        project_id: str | None = None,
        job_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> QuerySet[DramaLlmCallLog]:
        qs = DramaLlmCallLog.objects.select_related("project", "generation_job").all()
        if project_id:
            qs = qs.filter(project_id=project_id)
        if job_id:
            qs = qs.filter(generation_job_id=job_id)
        if role:
            qs = qs.filter(role=role)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")[:limit]

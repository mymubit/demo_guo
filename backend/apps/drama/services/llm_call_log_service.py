# -*- coding: utf-8 -*-
"""LLM 调用日志持久化与查询。"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from apps.drama.models import (
    DramaGenerationJob,
    DramaLlmCallLog,
    DramaProject,
    V3CommandRun,
    V3Project,
)
from apps.drama.services.llm_call_context import get_llm_call_context, get_injection_manifest, set_last_llm_log_id

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


_model_label_cache: dict[str, str] = {}


def resolve_model_label(model_name: str) -> str:
    """优先用供应商配置的展示名，避免接入点 ID（ep-…）直接暴露。"""
    key = (model_name or "").strip()
    if not key:
        return ""
    cached = _model_label_cache.get(key)
    if cached is not None:
        return cached
    label = key
    try:
        from apps.drama.models import DramaLlmProvider

        provider = (
            DramaLlmProvider.objects.filter(model_name=key)
            .order_by("-is_active", "-updated_at")
            .first()
        )
        if provider and (provider.name or "").strip():
            label = provider.name.strip()
    except Exception:
        label = key
    _model_label_cache[key] = label
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
    """兼容 OpenAI / 部分国产网关的 usage 字段别名。"""
    usage = (response_json or {}).get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}

    def _as_int(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    prompt = _as_int(usage.get("prompt_tokens"))
    if prompt is None:
        prompt = _as_int(usage.get("input_tokens"))
    completion = _as_int(usage.get("completion_tokens"))
    if completion is None:
        completion = _as_int(usage.get("output_tokens"))
    total = _as_int(usage.get("total_tokens"))
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion

    cached = _as_int(usage.get("cached_tokens"))
    if cached is None:
        cached = _as_int(usage.get("prompt_cache_hit_tokens"))
    if cached is None:
        cached = _as_int(usage.get("cache_read_input_tokens"))
    if cached is None:
        details = usage.get("prompt_tokens_details")
        if isinstance(details, dict):
            cached = _as_int(details.get("cached_tokens"))
    if cached is None:
        details = usage.get("input_tokens_details")
        if isinstance(details, dict):
            cached = _as_int(details.get("cached_tokens"))

    if cached is not None and prompt is not None and cached > prompt:
        cached = prompt

    return {
        "prompt_tokens": prompt,
        "cached_prompt_tokens": cached,
        "completion_tokens": completion,
        "total_tokens": total,
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
        v3_command_run_id: str | None = None,
        v3_project_id: str | None = None,
        role: str = "",
        purpose: str = "",
        actor: str = "system",
        injection_manifest: dict[str, Any] | None = None,
    ) -> DramaLlmCallLog | None:
        if not cls.is_enabled():
            return None

        ctx = get_llm_call_context()
        project_id = project_id or (ctx.project_id if ctx else None)
        job_id = job_id or (ctx.job_id if ctx else None)
        v3_command_run_id = v3_command_run_id or (
            ctx.v3_command_run_id if ctx else None
        )
        v3_project_id = v3_project_id or (ctx.v3_project_id if ctx else None)
        role = role or (ctx.role if ctx else "")
        purpose = purpose or (ctx.purpose if ctx else DramaLlmCallLog.Purpose.ARTIFACT_GENERATION)
        actor = actor or (ctx.actor if ctx else "system")
        if injection_manifest is None:
            injection_manifest = get_injection_manifest()

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

        v3_run = None
        if v3_command_run_id:
            v3_run = V3CommandRun.objects.filter(pk=v3_command_run_id).first()

        v3_project = None
        if v3_project_id:
            v3_project = V3Project.objects.filter(pk=v3_project_id).first()
        elif v3_run is not None and v3_run.project_id:
            v3_project = v3_run.project

        body = response_json if isinstance(response_json, dict) else None

        text = response_text if response_text is not None else _extract_response_text(response_json)
        usage = _extract_usage(response_json if isinstance(response_json, dict) else None)

        try:
            log = DramaLlmCallLog.objects.create(
                project=project,
                generation_job=job,
                v3_command_run=v3_run,
                v3_project=v3_project,
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
                cached_prompt_tokens=usage.get("cached_prompt_tokens"),
                completion_tokens=usage["completion_tokens"],
                total_tokens=usage["total_tokens"],
                provider_request_id=str((response_json or {}).get("id") or ""),
                injection_manifest=injection_manifest if isinstance(injection_manifest, dict) else None,
            )
            set_last_llm_log_id(str(log.id))
            try:
                from apps.drama.orchestrator.usage_rollup import apply_call_to_rollup

                apply_call_to_rollup(log)
            except Exception:
                logger.exception("用量日汇总增量失败 call_log=%s", log.id)
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
            "v3_command_run_id": (
                str(log.v3_command_run_id) if log.v3_command_run_id else None
            ),
            "v3_project_id": str(log.v3_project_id) if log.v3_project_id else None,
            "actor": log.actor,
            "role": log.role,
            "role_label": resolve_role_label(log.role),
            "purpose": log.purpose,
            "status": log.status,
            "model_name": log.model_name,
            "model_label": resolve_model_label(log.model_name or ""),
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
            "injection_system_chars": (
                (log.injection_manifest or {}).get("system_chars")
                if isinstance(log.injection_manifest, dict)
                else None
            ),
            "injection_truncated": _manifest_any_truncated(log.injection_manifest),
        }

    @classmethod
    def serialize_v3_call(
        cls, log: DramaLlmCallLog, *, full: bool = False
    ) -> dict[str, Any]:
        """V3 Logs API 用：无 api_key；run 详情可截断，call 详情全量。"""
        system = log.system_prompt or ""
        user = log.user_prompt or ""
        response = log.response_text or ""
        if not full:
            system = system[:_PREVIEW_CHARS]
            user = user[:_PREVIEW_CHARS]
            response = response[:_PREVIEW_CHARS]
        return {
            "id": str(log.id),
            "role": log.role,
            "purpose": log.purpose,
            "status": log.status,
            "model_name": log.model_name,
            "model_label": resolve_model_label(log.model_name or ""),
            "base_url": log.base_url,
            "latency_ms": log.latency_ms,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "system_prompt": system,
            "user_prompt": user,
            "response_text": response,
            "error_message": log.error_message or "",
            "http_status": log.http_status,
            "v3_command_run_id": (
                str(log.v3_command_run_id) if log.v3_command_run_id else None
            ),
            "v3_project_id": str(log.v3_project_id) if log.v3_project_id else None,
            "system_prompt_preview": (log.system_prompt or "")[:_PREVIEW_CHARS] or None,
            "user_prompt_preview": (log.user_prompt or "")[:_PREVIEW_CHARS] or None,
            "response_preview": (log.response_text or "")[:_PREVIEW_CHARS] or None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    @classmethod
    def serialize_detail(cls, log: DramaLlmCallLog) -> dict[str, Any]:
        from apps.drama.services.injection_alerts import (
            compute_injection_alerts,
            highest_alert_level,
        )

        data = cls.serialize_summary(log)
        manifest = log.injection_manifest if isinstance(log.injection_manifest, dict) else None
        alerts = compute_injection_alerts(manifest, call_status=log.status or "")
        data.update(
            {
                "system_prompt": log.system_prompt,
                "user_prompt": log.user_prompt,
                "response_text": log.response_text,
                "response_body": log.response_body,
                "provider_request_id": log.provider_request_id or None,
                "injection_manifest": log.injection_manifest,
                "injection_alerts": alerts,
                "injection_alert_level": highest_alert_level(alerts),
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


def _manifest_any_truncated(manifest: Any) -> bool | None:
    if not isinstance(manifest, dict):
        return None
    layers = manifest.get("layers") or {}
    if not isinstance(layers, dict):
        return False
    for stat in layers.values():
        if isinstance(stat, dict) and stat.get("truncated"):
            return True
    rules = manifest.get("rules") or {}
    if isinstance(rules, dict) and rules.get("truncated"):
        return True
    return False

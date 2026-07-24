# -*- coding: utf-8 -*-
"""V3 同步命令：模型供应商连通性试连。

试连必须直连指定 provider（GET /models），禁止走 chat_with_failover 主备链。
"""
from __future__ import annotations

import time
from typing import Any
from uuid import UUID

import logging

import requests
from django.db import transaction

from apps.drama.models import DramaLlmCallLog, DramaLlmProvider, V3CommandRun
from apps.drama.services.llm_call_context import llm_call_scope
from apps.drama.services.llm_call_log_service import LlmCallLogService
from apps.drama.services.secret_crypto import decrypt_secret

logger = logging.getLogger(__name__)

_PROBE_CONNECT_TIMEOUT = 5
_PROBE_READ_TIMEOUT = 15
_ROLE = "v3.model-probe"


class ProviderTestError(Exception):
    """试连失败（人话消息）。"""


def test_provider_connectivity(
    *,
    provider_id: UUID | str,
    actor: str = "system",
) -> dict[str, Any]:
    """
    对指定供应商发最小连通性探测（GET {base_url}/models）。

    成功/失败均尽量写 CONNECTIVITY_TEST 日志；永不记录 api_key。
    返回：{ ok, status_code?, latency_ms?, message, provider_id }
    """
    try:
        provider = DramaLlmProvider.objects.get(pk=provider_id)
    except (DramaLlmProvider.DoesNotExist, ValueError, TypeError) as exc:
        raise ProviderTestError("供应商不存在") from exc

    api_key = decrypt_secret(provider.api_key_encrypted) or ""
    base_url = (provider.base_url or "").strip()
    if not base_url or not api_key:
        raise ProviderTestError("Base URL 或 API Key 未配置")

    url = base_url.rstrip("/") + "/models"
    started = time.monotonic()
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=(_PROBE_CONNECT_TIMEOUT, _PROBE_READ_TIMEOUT),
        )
    except requests.RequestException as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        _record_log(
            provider=provider,
            actor=actor,
            ok=False,
            latency_ms=latency_ms,
            http_status=None,
            response_text="",
            error_message=str(exc)[:2000],
        )
        raise ProviderTestError(f"连通失败：网络异常（{exc.__class__.__name__}）") from exc

    latency_ms = int((time.monotonic() - started) * 1000)
    ok = response.status_code < 400
    body_preview = (response.text or "")[:2000]
    _record_log(
        provider=provider,
        actor=actor,
        ok=ok,
        latency_ms=latency_ms,
        http_status=response.status_code,
        response_text=body_preview,
        error_message="" if ok else body_preview,
    )
    if ok:
        return {
            "ok": True,
            "provider_id": str(provider.id),
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "message": "连通成功",
        }
    raise ProviderTestError(f"连通失败：HTTP {response.status_code}")


def _record_log(
    *,
    provider: DramaLlmProvider,
    actor: str,
    ok: bool,
    latency_ms: int,
    http_status: int | None,
    response_text: str,
    error_message: str,
) -> None:
    try:
        LlmCallLogService.record(
            system_prompt="",
            user_prompt="GET /models",
            model_name=provider.model_name or "",
            base_url=provider.base_url or "",
            status=(
                DramaLlmCallLog.Status.SUCCESS if ok else DramaLlmCallLog.Status.ERROR
            ),
            latency_ms=latency_ms,
            http_status=http_status,
            response_text=response_text,
            error_message=error_message,
            purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST,
            role=_ROLE,
            actor=actor or "system",
        )
    except Exception:
        logger.exception("写入 CONNECTIVITY_TEST 日志失败（试连主流程继续）")


def run_test_model_provider_command(
    *,
    owner,
    command_type: str,
    payload: dict,
    idempotency_key: str = "",
) -> V3CommandRun:
    """同步 test_model_provider 入口。"""
    with transaction.atomic():
        run = V3CommandRun.objects.create(
            owner=owner,
            command_type=command_type,
            status=V3CommandRun.Status.RUNNING,
            idempotency_key=idempotency_key or "",
            request_payload=payload or {},
        )
        try:
            if command_type != "test_model_provider":
                raise ProviderTestError("未知试连命令")
            provider_id = (payload or {}).get("provider_id")
            if not provider_id:
                raise ProviderTestError("缺少 provider_id，请指定要试连的供应商")
            actor = getattr(owner, "username", None) or str(getattr(owner, "pk", "system"))
            v3_project_id = (
                str(run.project_id) if getattr(run, "project_id", None) else None
            )
            with llm_call_scope(
                v3_command_run_id=str(run.id),
                v3_project_id=v3_project_id,
                role=_ROLE,
                purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST,
                actor=actor,
            ):
                result = test_provider_connectivity(
                    provider_id=provider_id,
                    actor=actor,
                )
            run.status = V3CommandRun.Status.SUCCEEDED
            run.result_payload = result
            run.error_message = ""
            run.save(
                update_fields=[
                    "status",
                    "result_payload",
                    "error_message",
                    "updated_at",
                ]
            )
        except ProviderTestError as exc:
            run.status = V3CommandRun.Status.FAILED
            run.error_message = str(exc)
            run.save(update_fields=["status", "error_message", "updated_at"])
        return run

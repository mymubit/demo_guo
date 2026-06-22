# -*- coding: utf-8 -*-
"""User-facing error message helpers."""
from __future__ import annotations

import re
from typing import Any, Union
from urllib.parse import urlparse

TECHNICAL_MARKERS = (
    "traceback",
    "httpsconnectionpool",
    "connectionpool",
    "urllib3",
    "requests.exceptions",
    "connectionerror",
    "socket.gaierror",
    "nameresolutionerror",
    "sslerror",
    "modulenotfounderror",
    "importerror",
    "attributeerror",
    'file "',
    "django.db",
    "operationalerror",
    "integrityerror",
    "programmingerror",
    "jsondecodeerror",
    "stack trace",
    "exception group",
)

FUSION_NODE_LABELS = {
    # drama.* 新体系展示名
    "drama.topic-planner": "选题策划",
    "drama.world-architect": "世界构建",
    "drama.character-designer": "人设设计",
    "drama.plot-architect": "情节大纲",
    "drama.script-writer": "剧本创作",
    "drama.quality-reporter": "质量评审",
    "drama.compliance-guard": "合规检测",
}

_NODE_ERROR_RE = re.compile(r"^(node-\d+-[\w-]+):\s*(.+)$", re.IGNORECASE)
_UPSTREAM_ARTIFACT_RE = re.compile(r"missing upstream artifact:\s*([\w_]+)", re.IGNORECASE)

_UPSTREAM_ARTIFACT_LABELS = {
    "project_brief": "立项简报",
    "world_setting": "世界观设定",
    "character_bible": "人物小传",
    "series_outline": "分集大纲",
    "episode_scripts": "剧本正文",
    "emotion_blueprint": "情绪蓝图",
    "emotion_curve": "情绪曲线",
    "quality_report": "质量报告",
    "compliance_report": "合规报告",
    "delivery_pack": "交付包",
}


def humanize_upstream_artifact_message(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return text
    match = _UPSTREAM_ARTIFACT_RE.search(text)
    if not match:
        return text
    key = match.group(1)
    label = _UPSTREAM_ARTIFACT_LABELS.get(key, key)
    return f"Please complete {label} first."


def _host_from_base_url(base_url: str) -> str:
    if not base_url:
        return ""
    try:
        return urlparse(base_url).netloc or base_url
    except Exception:
        return base_url


def _is_volcano_host(base_url: str) -> bool:
    from apps.skill.llm.volcengine_config import is_volcano_host

    return is_volcano_host(base_url)


def volcano_alternate_base_url(base_url: str) -> str:
    from apps.skill.llm.volcengine_config import volcano_alternate_base_url as _alternate

    return _alternate(base_url)


def _volcano_404_hint(*, base_url: str, model: str, response_body: str = "") -> str:
    body_lower = (response_body or "").lower()
    if "invalidendpointornotfound" in body_lower or "model.notfound" in body_lower:
        return "Model endpoint was not found or the current key has no access."
    return f"Volcano model endpoint was not found for model {model or 'unknown'}."


def looks_technical(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    lower = raw.lower()
    if any(marker in lower for marker in TECHNICAL_MARKERS):
        return True
    return raw.count("\n") >= 2 and ("  File " in raw or " at " in raw)


def humanize_llm_request_error(
    exc: Union[BaseException, str],
    *,
    base_url: str = "",
    model: str = "",
    response_body: str = "",
) -> str:
    text = str(exc).lower()
    host = _host_from_base_url(base_url)
    host_lower = host.lower()
    model_str = str(model or "").strip()

    if "failed to resolve" in text or "getaddrinfo failed" in text or "nameresolutionerror" in text:
        if "example.com" in text:
            return "Base URL is still an example address. Please configure the real model service URL."
        return f"Could not resolve API host{': ' + host if host else ''}. Please check Base URL."
    if "connection refused" in text:
        return f"Connection was refused{': ' + host if host else ''}. Please check the service address and port."
    if "proxyerror" in text or "unable to connect to proxy" in text:
        return "Could not connect through the current proxy. Please check proxy or VPN settings."
    if "timed out" in text or "timeout" in text:
        return "The model request timed out. Please retry later."
    if "ssl" in text or "certificate" in text:
        return "HTTPS certificate validation failed. Please check the Base URL."

    resp = getattr(exc, "response", None)
    if resp is not None and getattr(resp, "status_code", None):
        code = resp.status_code
        if code == 401:
            return "API key is invalid or expired."
        if code == 403:
            return "Access was denied. Please check key permissions or account balance."
        if code == 404:
            if _is_volcano_host(base_url):
                return _volcano_404_hint(base_url=base_url, model=model_str, response_body=response_body)
            if "bigmodel.cn" in host_lower:
                return "API endpoint was not found. Please check the BigModel Base URL and model name."
            return "API endpoint was not found. Base URL should usually end with /v1 or /api/v3."
        if code == 429:
            return "Rate limit or quota was exceeded. Please retry later."
        if code == 400:
            if response_body:
                return f"Model request parameters are invalid: {response_body[:200]}"
            return "Model request parameters are invalid."
        if code >= 500:
            return f"Model provider returned HTTP {code}. Please retry later."
        return f"Model provider returned HTTP {code}."

    if "max retries exceeded" in text or "connectionerror" in text:
        return f"Could not connect to the model service{': ' + host if host else ''}. Please check Base URL, API key, and network."

    return "The model request failed. Please check Base URL, API key, and network."


def humanize_user_message(
    raw: Any,
    default: str = "Operation failed. Please retry later.",
    *,
    max_len: int = 500,
) -> str:
    text = str(raw or "").strip()
    if not text:
        return default
    for prefix in ("Server internal error", "LLM request failed:", "Read LLM config failed:"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip() or text
    text = humanize_upstream_artifact_message(text)
    if not looks_technical(text):
        return text[:max_len]
    return humanize_llm_request_error(text)[:max_len]


def safe_api_message(exc: Any, default: str = "Operation failed. Please retry later.") -> str:
    raw = str(exc).strip() if exc else ""
    if not raw:
        return default
    return humanize_user_message(raw, default=default)


def humanize_pipeline_error(
    raw: Any,
    default: str = "Creation workflow failed. Please retry later.",
) -> str:
    text = str(raw or "").strip()
    if not text:
        return default
    match = _NODE_ERROR_RE.match(text)
    if match:
        node_id, rest = match.group(1), match.group(2)
        label = FUSION_NODE_LABELS.get(node_id, "Creation step")
        rest_msg = humanize_user_message(rest, default="This step failed.")
        return f"{label}: {rest_msg}"
    return humanize_user_message(text, default=default)

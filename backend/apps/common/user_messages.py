# -*- coding: utf-8 -*-
"""面向用户的错误文案：过滤底层技术异常，保留业务中文提示。"""
from __future__ import annotations

import re
from typing import Any, Optional, Union
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
    "node-1-input": "立项信息",
    "node-2-structure": "结构与世界观",
    "node-3-character": "人设开发",
    "node-4-outline": "分集大纲",
    "node-5-script": "剧本创作",
    "node-6-review": "质量审查",
    "node-8-score": "剧本评分",
}

_NODE_ERROR_RE = re.compile(r"^(node-\d+-[\w-]+):\s*(.+)$", re.IGNORECASE)
_UPSTREAM_ARTIFACT_RE = re.compile(r"缺少上游产物:\s*([\w_]+)")

_UPSTREAM_ARTIFACT_LABELS = {
    "project_brief": "立项策划",
    "structure_plan": "结构与世界观",
    "character_bible": "角色设计",
    "series_outline": "大纲与创作规划",
    "episode_scripts": "剧集剧本",
}


def humanize_upstream_artifact_message(raw: Any) -> str:
    """将「缺少上游产物: character_bible」转为面向用户的步骤提示。"""
    text = str(raw or "").strip()
    if not text:
        return text
    match = _UPSTREAM_ARTIFACT_RE.search(text)
    if not match:
        return text
    label = _UPSTREAM_ARTIFACT_LABELS.get(match.group(1), match.group(1))
    return f"请先生成「{label}」"


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
    from apps.skill.llm.volcengine_chat import is_volcano_endpoint_id
    from apps.skill.llm.volcengine_config import (
        get_volcano_coding_base_url,
        get_volcano_payg_base_url,
    )

    payg_url = get_volcano_payg_base_url()
    coding_url = get_volcano_coding_base_url()
    url = (base_url or "").rstrip("/")
    is_coding = "/api/coding" in url
    body_lower = (response_body or "").lower()
    hints = []
    model_str = str(model or "").strip()

    if "invalidendpointornotfound" in body_lower or "model.notfound" in body_lower:
        hints.append("推理接入点或 Model ID 不存在、未开通，或当前 Key 无权访问")

    if is_coding:
        hints.append(
            "当前为 Coding Plan 地址；若 Key 来自按量付费方舟，请在厂商区将「火山 Key 类型」改为按量付费，"
            f"Base URL 将自动设为 {payg_url}"
        )
        hints.append(
            f"Coding Plan 模型名如 deepseek-v4-flash、doubao-seed-2.0-pro（当前 {model_str or '未填'}），"
            "需在 Coding Plan 订阅内开通"
        )
    else:
        if not is_volcano_endpoint_id(model_str):
            hints.append(
                f"按量付费 Chat API 推荐 model 填 ep-xxxxxxxx（控制台 → 在线推理 → 推理接入点复制）；"
                f"当前为「{model_str or '未填'}」且账号可能未开通该 Model ID"
            )
            hints.append(
                "也可在 .env 配置 VOLCANO_EP_* 环境变量，系统会自动把 Model ID 映射到 ep"
            )
        else:
            hints.append("请确认该 ep 接入点已在控制台创建且状态为运行中")
        hints.append(
            "若 Key 确为 Coding Plan 订阅专用，请将「火山 Key 类型」改为 Coding Plan，"
            f"Base URL 将自动设为 {coding_url}"
        )

    hints.append(
        f"Chat API 地址应为 {payg_url}（不要含 /chat/completions，参见火山方舟 Chat API 文档）"
    )
    return "接口不存在（404）：" + "；".join(hints)


def looks_technical(text: str) -> bool:
    """判断字符串是否像 Python/HTTP 底层异常。"""
    raw = str(text or "").strip()
    if not raw:
        return False
    lower = raw.lower()
    if any(marker in lower for marker in TECHNICAL_MARKERS):
        return True
    if raw.count("\n") >= 2 and ("  File " in raw or " at " in raw):
        return True
    return False


def humanize_llm_request_error(
    exc: Union[BaseException, str],
    *,
    base_url: str = "",
    model: str = "",
    response_body: str = "",
) -> str:
    """将 requests/urllib3 原始异常转为运营可读的提示。"""
    text = str(exc).lower()
    host = _host_from_base_url(base_url)
    host_lower = host.lower()
    model_str = str(model or "").strip()

    if "failed to resolve" in text or "getaddrinfo failed" in text or "nameresolutionerror" in text:
        if "example.com" in text:
            return (
                "无法连接：Base URL 仍是示例地址 api.example.com，请改为真实服务商地址"
                "（如 https://api.openai.com/v1 或 DeepSeek 等）。"
            )
        return f"无法解析 API 域名{'「' + host + '」' if host else ''}，请检查 Base URL 是否填写正确。"

    if "connection refused" in text:
        return f"连接被拒绝{'（' + host + '）' if host else ''}，请确认服务地址与端口。"

    if "timed out" in text or "timeout" in text:
        return "连接超时，请检查网络或稍后重试。"

    if "ssl" in text or "certificate" in text:
        return "HTTPS 证书校验失败，请确认 Base URL 使用了正确的 https 地址。"

    resp = getattr(exc, "response", None)
    if resp is not None and getattr(resp, "status_code", None):
        code = resp.status_code
        if code == 401:
            return "API Key 无效或已过期，请重新填写。"
        if code == 403:
            return "访问被拒绝（403），请检查密钥权限或账户余额。"
        if code == 404:
            if _is_volcano_host(base_url):
                return _volcano_404_hint(base_url=base_url, model=model_str, response_body=response_body)
            if "bigmodel.cn" in host_lower:
                return (
                    "接口不存在（404）：请确认 Base URL 为 https://open.bigmodel.cn/api/paas/v4，"
                    "模型名如 glm-5；不要包含 /chat/completions。"
                )
            return "接口不存在（404）：Base URL 应填到 /v1 或 /api/v3，不要包含 /chat/completions。"
        if code == 429:
            return "请求过于频繁或额度不足（429），请稍后重试。"
        if code == 400:
            body_lower = (response_body or "").lower()
            if "invalidsubscription" in body_lower or "codingplan" in body_lower:
                return (
                    "Coding Plan 订阅无效或已过期（HTTP 400）。"
                    "若使用方舟按量付费 API Key，请在厂商区将「火山 Key 类型」改为按量付费。"
                )
            if "json_object" in body_lower and "not supported" in body_lower:
                return (
                    "当前模型不支持 JSON 结构化输出（response_format），"
                    "系统已尝试自动降级；若仍失败请更换支持 JSON 模式的模型。"
                )
            if response_body:
                return f"模型接口参数错误（HTTP 400）：{response_body[:200]}"
        if code >= 500:
            return f"模型服务商异常（HTTP {code}），请稍后重试。"
        return f"模型接口返回错误（HTTP {code}），请检查配置。"

    if "max retries exceeded" in text or "connectionerror" in text:
        return f"无法连接到模型服务{'「' + host + '」' if host else ''}，请检查 Base URL、API Key 与网络。"

    return "大模型连接失败，请检查 Base URL、API Key 与网络后重试。"


def humanize_user_message(
    raw: Any,
    default: str = "操作失败，请稍后重试",
    *,
    max_len: int = 500,
) -> str:
    """业务中文短句原样保留；技术堆栈替换为 default 或 LLM 友好文案。"""
    text = str(raw or "").strip()
    if not text:
        return default

    for prefix in ("服务器内部错误:", "LLM 请求失败:", "读取 LLM 配置失败:"):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip() or text

    text = humanize_upstream_artifact_message(text)

    if not looks_technical(text):
        return text[:max_len]

    llm_hint = humanize_llm_request_error(text)
    if llm_hint != "大模型连接失败，请检查 Base URL、API Key 与网络后重试。":
        return llm_hint[:max_len]
    return default


def safe_api_message(exc: Any, default: str = "操作失败，请稍后重试") -> str:
    """API 视图捕获异常时使用。"""
    raw = str(exc).strip() if exc else ""
    if not raw:
        return default
    return humanize_user_message(raw, default=default)


def humanize_pipeline_error(
    raw: Any,
    default: str = "创作流程执行失败，请稍后重试",
) -> str:
    """流水线 node-id: exc 形式的用户可读文案。"""
    text = str(raw or "").strip()
    if not text:
        return default
    match = _NODE_ERROR_RE.match(text)
    if match:
        node_id, rest = match.group(1), match.group(2)
        label = FUSION_NODE_LABELS.get(node_id, "创作步骤")
        rest_msg = humanize_user_message(rest, default="该步骤执行失败")
        return f"{label}：{rest_msg}"
    return humanize_user_message(text, default=default)

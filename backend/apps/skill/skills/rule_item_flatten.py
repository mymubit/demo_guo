# -*- coding: utf-8 -*-
"""按 section 语义拆分 SkillRuleConfig → SkillRuleItem 草稿（基于真实 JSON 结构）。"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

from apps.skill.models import SkillRuleConfig, SkillRuleItem

# 整包聚合配置，已有按 section / scope 拆分的 active 记录，不再二次 flatten
SKIP_SECTIONS = frozenset(
    {
        "tier_full",
        "tier1-iron-rules",
        "tier2-genre-rules",
        "tier3-workflow-rules",
        "tier4-compliance-rules",
        "skill-rules-index",
        "skill-versions",
        "skill-thresholds",
    }
)

LIST_FIELD_KEYS = frozenset(
    {
        "requirements",
        "prohibitions",
        "constraints",
        "gate_conditions",
        "forbidden_phrases",
        "forbidden_patterns",
        "rules",
        "items",
        "checklist",
        "keywords",
        "p0_triggered",
        "formats",
        "effective_justice_words",
        "ancient_costume_justice",
        "private_justice_prohibition",
    }
)


def _slug_part(value: str, max_len: int = 48) -> str:
    text = re.sub(r"[^\w\-]+", "-", str(value or "").strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return (text or "item")[:max_len]


def _scope_slug(scope_type: str, scope_key: str) -> str:
    if scope_type == SkillRuleConfig.SCOPE_GLOBAL or not scope_key:
        return "global"
    return _slug_part(scope_key, 64)


def _build_rule_key(
    *,
    tier: int,
    scope_type: str,
    scope_key: str,
    section: str,
    path: str,
) -> str:
    return f"t{tier}.{_scope_slug(scope_type, scope_key)}.{_slug_part(section, 32)}.{_slug_part(path, 96)}"


def _draft(
    config: SkillRuleConfig,
    *,
    path: str,
    title: str,
    body: str,
    payload: Optional[Dict[str, Any]] = None,
    sort_order: int = 0,
    item_type: str = SkillRuleItem.TYPE_RULE,
) -> Dict[str, Any]:
    return {
        "rule_key": _build_rule_key(
            tier=config.tier,
            scope_type=config.scope_type,
            scope_key=config.scope_key,
            section=config.section,
            path=path,
        ),
        "title": (title or "规则")[:512],
        "body": str(body or "").strip(),
        "payload": payload or {},
        "sort_order": sort_order,
        "item_type": item_type,
    }


def _path_title(path: str, fallback: str = "规则") -> str:
    if not path:
        return fallback
    cleaned = path.replace("[", "/").replace("]", "")
    parts = [p for p in cleaned.split("/") if p and not p.isdigit()]
    if not parts:
        parts = [p for p in cleaned.split(".") if p]
    return " / ".join(parts[-2:])[:120] if parts else fallback


def _format_dict_item(data: Dict[str, Any]) -> tuple[str, str]:
    title = str(
        data.get("title")
        or data.get("label")
        or data.get("name")
        or data.get("element")
        or data.get("code")
        or "规则"
    )[:512]
    body = (
        data.get("body")
        or data.get("text")
        or data.get("standard")
        or data.get("content")
        or data.get("description")
        or data.get("requirement")
        or data.get("action")
        or data.get("rule")
    )
    if body is None:
        body = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        body = str(body)
    return title, body


def _flatten_root_string_list(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, list):
        return []
    items: List[Dict[str, Any]] = []
    for idx, text in enumerate(content):
        if not isinstance(text, str) or not text.strip():
            continue
        items.append(
            _draft(
                config,
                path=str(idx),
                title=text[:120],
                body=text,
                payload={"path": str(idx), "value": text},
                sort_order=idx,
            )
        )
    return items


def _flatten_meta(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    title = str(content.get("name") or config.section or "元信息")[:512]
    body = json.dumps(content, ensure_ascii=False, indent=2)
    return [
        _draft(
            config,
            path="meta",
            title=title,
            body=body,
            payload=content,
            sort_order=0,
            item_type=SkillRuleItem.TYPE_META,
        )
    ]


def _flatten_genre_full(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0

    for req in content.get("requirements") or []:
        if isinstance(req, dict):
            element = str(req.get("element") or "品类要求")
            standard = str(req.get("standard") or "")
            if not standard.strip():
                continue
            items.append(
                _draft(
                    config,
                    path=f"requirements.{_slug_part(element, 32)}",
                    title=element[:512],
                    body=standard,
                    payload={"kind": "requirement", **req},
                    sort_order=order,
                )
            )
            order += 1
        elif isinstance(req, str) and req.strip():
            items.append(
                _draft(
                    config,
                    path=f"requirements.{order}",
                    title=req[:120],
                    body=req,
                    payload={"kind": "requirement", "value": req},
                    sort_order=order,
                )
            )
            order += 1

    for idx, text in enumerate(content.get("prohibitions") or []):
        if not isinstance(text, str) or not text.strip():
            continue
        items.append(
            _draft(
                config,
                path=f"prohibitions.{idx}",
                title=text[:120],
                body=text,
                payload={"kind": "prohibition", "value": text},
                sort_order=order,
            )
        )
        order += 1

    scalar_labels = {
        "label": "题材标签",
        "core_emotion": "核心情绪",
        "ending_type": "结局类型",
        "forbidden_ending": "禁止结局",
        "target_audience": "目标受众",
        "sweet_bitter_alternation": "甜虐交替",
    }
    for key, label in scalar_labels.items():
        val = content.get(key)
        if val is None or val == "":
            continue
        items.append(
            _draft(
                config,
                path=f"scalar.{key}",
                title=label,
                body=str(val),
                payload={"kind": "scalar", "field": key, "value": val},
                sort_order=order,
            )
        )
        order += 1

    release = content.get("release_conditions")
    if isinstance(release, dict) and release:
        note = release.get("note") or release.get("requirement") or json.dumps(release, ensure_ascii=False)
        items.append(
            _draft(
                config,
                path="release_conditions",
                title="放行条件",
                body=str(note),
                payload={"kind": "release_conditions", **release},
                sort_order=order,
            )
        )
        order += 1

    return items


def _flatten_keyword_blacklist(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0

    replace_map = content.get("替换映射")
    if isinstance(replace_map, dict):
        for phrase, alts in replace_map.items():
            if not isinstance(phrase, str) or not phrase.strip():
                continue
            alt_list = [str(a) for a in alts] if isinstance(alts, list) else []
            body = f"避免套话「{phrase}」"
            if alt_list:
                body += f"，口语可改用：{'、'.join(alt_list)}"
            items.append(
                _draft(
                    config,
                    path=f"replace.{_slug_part(phrase, 32)}",
                    title=f"替换：{phrase}",
                    body=body,
                    payload={"kind": "keyword_replace", "phrase": phrase, "alternatives": alt_list},
                    sort_order=order,
                )
            )
            order += 1

    cliche = content.get("套话黑名单")
    if isinstance(cliche, dict):
        for category, phrases in cliche.items():
            if not isinstance(phrases, list):
                continue
            for idx, phrase in enumerate(phrases):
                if not isinstance(phrase, str) or not phrase.strip():
                    continue
                items.append(
                    _draft(
                        config,
                        path=f"cliche.{_slug_part(category, 16)}.{idx}",
                        title=phrase[:120],
                        body=f"禁止{category}套话：{phrase}",
                        payload={"kind": "cliche", "category": category, "phrase": phrase},
                        sort_order=order,
                    )
                )
                order += 1

    pauses = content.get("自然停顿词")
    if isinstance(pauses, list):
        for idx, word in enumerate(pauses):
            if not isinstance(word, str) or not word.strip():
                continue
            items.append(
                _draft(
                    config,
                    path=f"pause.{idx}",
                    title=word,
                    body=f"口语自然停顿可用：{word}",
                    payload={"kind": "pause_word", "word": word},
                    sort_order=order,
                )
            )
            order += 1

    detail = content.get("细节增强素材")
    if isinstance(detail, dict):
        for category, phrases in detail.items():
            if not isinstance(phrases, list):
                continue
            for idx, phrase in enumerate(phrases):
                if not isinstance(phrase, str) or not phrase.strip():
                    continue
                items.append(
                    _draft(
                        config,
                        path=f"detail.{_slug_part(category, 16)}.{idx}",
                        title=phrase[:120],
                        body=f"细节增强（{category}）：{phrase}",
                        payload={"kind": "detail", "category": category, "phrase": phrase},
                        sort_order=order,
                    )
                )
                order += 1

    return items


def _flatten_ai_tone_forbidden(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0

    desc = content.get("description")
    if isinstance(desc, str) and desc.strip():
        items.append(
            _draft(
                config,
                path="description",
                title="去 AI 腔说明",
                body=desc,
                payload={"kind": "description"},
                sort_order=order,
            )
        )
        order += 1

    for idx, phrase in enumerate(content.get("forbidden_phrases") or []):
        if not isinstance(phrase, str) or not phrase.strip():
            continue
        items.append(
            _draft(
                config,
                path=f"forbidden.{idx}",
                title=phrase[:120],
                body=f"禁止使用 AI 腔表达：{phrase}",
                payload={"kind": "forbidden_phrase", "phrase": phrase},
                sort_order=order,
            )
        )
        order += 1

    qs = content.get("quantitative_standard")
    if isinstance(qs, dict) and qs:
        lines = [f"{k}：{v}" for k, v in qs.items()]
        items.append(
            _draft(
                config,
                path="quantitative_standard",
                title="量化标准",
                body="\n".join(lines),
                payload={"kind": "quantitative_standard", **qs},
                sort_order=order,
            )
        )
        order += 1

    return items


def _flatten_pipeline_node(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0

    name = str(content.get("name") or "")
    desc = str(content.get("description") or "")
    if name or desc:
        summary = name
        if desc:
            summary = f"{name}：{desc}" if name else desc
        items.append(
            _draft(
                config,
                path="summary",
                title=name or config.scope_key or "节点规则",
                body=summary,
                payload={"kind": "node_summary", "node_id": content.get("node_id")},
                sort_order=order,
            )
        )
        order += 1

    for idx, text in enumerate(content.get("constraints") or []):
        if not isinstance(text, str) or not text.strip():
            continue
        items.append(
            _draft(
                config,
                path=f"constraints.{idx}",
                title=text[:120],
                body=text,
                payload={"kind": "constraint", "value": text},
                sort_order=order,
            )
        )
        order += 1

    for idx, text in enumerate(content.get("gate_conditions") or []):
        if not isinstance(text, str) or not text.strip():
            continue
        items.append(
            _draft(
                config,
                path=f"gate.{idx}",
                title=text[:120],
                body=f"放行条件：{text}",
                payload={"kind": "gate_condition", "value": text},
                sort_order=order,
            )
        )
        order += 1

    for field in ("quality_gates", "gate_rules"):
        val = content.get(field)
        if isinstance(val, list):
            for idx, entry in enumerate(val):
                if isinstance(entry, str) and entry.strip():
                    title, body = entry[:120], entry
                elif isinstance(entry, dict):
                    title, body = _format_dict_item(entry)
                else:
                    continue
                items.append(
                    _draft(
                        config,
                        path=f"{field}.{idx}",
                        title=title,
                        body=body,
                        payload={"kind": field, "value": entry},
                        sort_order=order,
                    )
                )
                order += 1

    return items


def _flatten_philosophy(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0

    for key in ("core_formula", "driving_force"):
        val = content.get(key)
        if val:
            items.append(
                _draft(
                    config,
                    path=key,
                    title=key,
                    body=str(val),
                    payload={"kind": "scalar", "field": key},
                    sort_order=order,
                )
            )
            order += 1

    for idx, archetype in enumerate(content.get("viewer_archetypes") or []):
        if not isinstance(archetype, dict):
            continue
        label = str(archetype.get("label") or f"观众原型{idx + 1}")
        body = (
            f"类型：{archetype.get('type', '')}\n"
            f"现实：{archetype.get('reality', '')}\n"
            f"梦境：{archetype.get('dream', '')}\n"
            f"适用题材：{', '.join(archetype.get('genres') or [])}"
        ).strip()
        items.append(
            _draft(
                config,
                path=f"viewer_archetypes.{idx}",
                title=label,
                body=body,
                payload={"kind": "viewer_archetype", **archetype},
                sort_order=order,
            )
        )
        order += 1

    metrics = content.get("dream_quality_metrics")
    if isinstance(metrics, dict):
        for key, val in metrics.items():
            if not val:
                continue
            items.append(
                _draft(
                    config,
                    path=f"dream_quality_metrics.{key}",
                    title=f"造梦指标·{key}",
                    body=str(val),
                    payload={"kind": "dream_metric", "field": key},
                    sort_order=order,
                )
            )
            order += 1

    return items


def _flatten_p0_items(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0
    for idx, entry in enumerate(content.get("items") or []):
        if not isinstance(entry, dict):
            continue
        title, body = _format_dict_item(entry)
        req = entry.get("requirement") or entry.get("action") or body
        items.append(
            _draft(
                config,
                path=f"items.{entry.get('code') or idx}",
                title=title,
                body=str(req),
                payload={"kind": "p0_item", **entry},
                sort_order=order,
            )
        )
        order += 1
    return items


def _flatten_named_string_lists(config: SkillRuleConfig, content: Any) -> List[Dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    items: List[Dict[str, Any]] = []
    order = 0
    for key, val in content.items():
        if key.startswith("_"):
            continue
        if isinstance(val, list):
            for idx, text in enumerate(val):
                if not isinstance(text, str) or not text.strip():
                    continue
                items.append(
                    _draft(
                        config,
                        path=f"{key}.{idx}",
                        title=text[:120],
                        body=text,
                        payload={"kind": key, "value": text},
                        sort_order=order,
                    )
                )
                order += 1
        elif isinstance(val, str) and val.strip():
            items.append(
                _draft(
                    config,
                    path=key,
                    title=key,
                    body=val,
                    payload={"kind": "scalar", "field": key, "value": val},
                    sort_order=order,
                )
            )
            order += 1
    return items


def _flatten_library_leaves(config: SkillRuleConfig, content: Any, *, root_path: str = "") -> List[Dict[str, Any]]:
    """嵌套词库/规则库：只拆字符串列表叶子与路径上的标量，禁止对 string 做字符级迭代。"""
    items: List[Dict[str, Any]] = []
    order = 0

    def walk(node: Any, path: str) -> None:
        nonlocal order
        if isinstance(node, str):
            text = node.strip()
            if not text or len(text) < 2:
                return
            items.append(
                _draft(
                    config,
                    path=path or "leaf",
                    title=_path_title(path, node[:120]),
                    body=node,
                    payload={"kind": "library_leaf", "path": path},
                    sort_order=order,
                )
            )
            order += 1
            return
        if isinstance(node, list):
            for idx, child in enumerate(node):
                walk(child, f"{path}[{idx}]" if path else str(idx))
            return
        if isinstance(node, dict):
            for key, child in node.items():
                if key.startswith("_"):
                    continue
                sub_path = f"{path}.{key}" if path else key
                if isinstance(child, str):
                    if not child.strip():
                        continue
                    items.append(
                        _draft(
                            config,
                            path=sub_path,
                            title=_path_title(sub_path, key),
                            body=child,
                            payload={"kind": "library_scalar", "path": sub_path},
                            sort_order=order,
                        )
                    )
                    order += 1
                elif isinstance(child, (list, dict)):
                    walk(child, sub_path)

    walk(content, root_path)
    return items


def _flatten_dict_smart(config: SkillRuleConfig, content: Dict[str, Any]) -> List[Dict[str, Any]]:
    """通用 dict：优先拆已知 list 字段，其余走 library 叶子遍历。"""
    items: List[Dict[str, Any]] = []
    order = 0
    consumed_keys: set[str] = set()

    for list_key in LIST_FIELD_KEYS:
        val = content.get(list_key)
        if not isinstance(val, list):
            continue
        consumed_keys.add(list_key)
        for idx, entry in enumerate(val):
            if isinstance(entry, str) and entry.strip():
                items.append(
                    _draft(
                        config,
                        path=f"{list_key}.{idx}",
                        title=entry[:120],
                        body=entry,
                        payload={"kind": list_key, "value": entry},
                        sort_order=order,
                    )
                )
                order += 1
            elif isinstance(entry, dict):
                title, body = _format_dict_item(entry)
                if body.strip():
                    items.append(
                        _draft(
                            config,
                            path=f"{list_key}.{entry.get('code') or entry.get('element') or idx}",
                            title=title,
                            body=body,
                            payload={"kind": list_key, **entry},
                            sort_order=order,
                        )
                    )
                    order += 1

    remainder = {k: v for k, v in content.items() if k not in consumed_keys and not k.startswith("_")}
    if remainder:
        for row in _flatten_library_leaves(config, remainder):
            row["sort_order"] = order
            order += 1
            items.append(row)

    return items


SECTION_FLATTENERS: Dict[str, Callable[[SkillRuleConfig, Any], List[Dict[str, Any]]]] = {
    "_meta": _flatten_meta,
    "genre_full": _flatten_genre_full,
    "ai-keywords-blacklist": _flatten_keyword_blacklist,
    "ai_tone_forbidden": _flatten_ai_tone_forbidden,
    "pipeline_node_full": _flatten_pipeline_node,
    "philosophy": _flatten_philosophy,
    "writing_prohibitions": lambda cfg, c: _flatten_root_string_list(cfg, c),
    "writing_requirements": lambda cfg, c: _flatten_root_string_list(cfg, c),
    "new_2026_p0_items": _flatten_p0_items,
    "fuse_behavior": _flatten_named_string_lists,
    "justice_tail_rule": _flatten_named_string_lists,
}


def flatten_config(config: SkillRuleConfig) -> List[Dict[str, Any]]:
    section = (config.section or "custom").strip()
    if section in SKIP_SECTIONS:
        return []

    content = config.content
    handler = SECTION_FLATTENERS.get(section)
    if handler:
        return [row for row in handler(config, content) if row.get("body")]

    if section == "_meta" or (isinstance(content, dict) and set(content.keys()) <= {"_meta"} and "_meta" in content):
        return _flatten_meta(config, content.get("_meta") if isinstance(content, dict) else content)

    if isinstance(content, list):
        return _flatten_root_string_list(config, content)

    if isinstance(content, dict):
        if "requirements" in content or "prohibitions" in content:
            return _flatten_genre_full(config, content)
        if "forbidden_phrases" in content:
            return _flatten_ai_tone_forbidden(config, content)
        if "替换映射" in content or "套话黑名单" in content:
            return _flatten_keyword_blacklist(config, content)
        if "constraints" in content or "gate_conditions" in content:
            return _flatten_pipeline_node(config, content)
        if "items" in content and all(isinstance(x, dict) for x in (content.get("items") or [])[:1] or [True]):
            return _flatten_p0_items(config, content)
        return _flatten_dict_smart(config, content)

    if isinstance(content, str) and content.strip():
        return [
            _draft(
                config,
                path="root",
                title=content[:120],
                body=content,
                payload={"value": content},
                sort_order=0,
            )
        ]
    return []

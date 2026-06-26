# -*- coding: utf-8 -*-
"""各 schema_version 专用产物展示器。"""
from __future__ import annotations

import re
from typing import Any, List

from apps.drama.presentation.base import (
    a_level_reverse_cards,
    adaptation_breakdown_cards,
    append_cards,
    append_dict_kv,
    append_list,
    append_paragraph,
    append_scalar_kv,
    assessment_report_block,
    build_character_id_map,
    build_compliance_report_view,
    build_episode_outline_batches,
    build_quality_dimensions,
    build_stage_grouped_outlines,
    cards_block,
    character_roster_block,
    character_roster_entries,
    character_bible_block,
    checks_block,
    deliverable_sections_block,
    dict_to_kv_rows,
    emotion_externalization_cards,
    episode_metrics_list_block,
    episode_outline_card_item,
    episode_outline_number,
    format_deviation_node,
    format_emotion_marker,
    format_emotion_node_line,
    format_list_items,
    format_scalar,
    kv_block,
    label,
    list_block,
    list_block_from_items,
    market_report_block,
    metrics_block,
    project_brief_block,
    score_board_block,
    series_outline_block,
    world_setting_block,
    narrative_plan_block,
    nested_check_rows,
    normalize_payload,
    normalize_review_issues,
    outline_overview_block,
    paragraph_block,
    parse_episode_range,
    parse_episode_script_content,
    plan_items_block,
    plan_overview_block,
    quality_report_block,
    relationship_graph_block,
    relationship_graph_entries,
    resolve_character_role,
    reversal_cards,
    review_issues_block,
    review_overview_block,
    rows_from_dict,
    script_episodes_block,
    stage_outlines_block,
    build_labeled_step_items,
    split_labeled_line,
    space_card_item,
    steps_block,
    storyboard_to_cards,
    view,
    visual_prompt_episode_blocks,
)
from apps.drama.presentation.text_localize import localize_phrase_label


def _string_list(val: Any) -> list[str]:
    if not isinstance(val, list):
        return []
    return [str(item).strip() for item in val if str(item or "").strip()]


def _format_episode_range_display(text: Any) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    ep_span = re.match(r"^(?:E|EP|e|ep)?(\d+)\s*[-–—~至到]\s*(?:E|EP|e|ep)?(\d+)$", raw)
    if ep_span:
        return f"第{int(ep_span.group(1))}-{int(ep_span.group(2))}集"
    parsed = parse_episode_range(raw)
    if parsed:
        return f"第{parsed[0]}-{parsed[1]}集"
    return raw


def _narrative_string_list(items: Any, *, limit: int = 12) -> List[str]:
    if isinstance(items, str):
        items = _coerce_string_list_from_presenter(items)
    if not isinstance(items, list):
        return []
    return [str(item).strip() for item in items[:limit] if str(item or "").strip()]


def _coerce_string_list_from_presenter(value: str) -> List[str]:
    text = str(value or "").strip()
    if not text:
        return []
    if "；" in text or ";" in text:
        parts = re.split(r"[；;]+", text)
        return [part.strip() for part in parts if part.strip()]
    return [text]


def _parse_narrative_mechanic_item(item: Any) -> dict | None:
    if isinstance(item, dict):
        title = str(item.get("mechanism_type") or "叙事机制").strip()
        detail = str(item.get("implementation_details") or "").strip()
        if title or detail:
            return {"title": title or "叙事机制", "body": detail}
        return None
    text = str(item or "").strip()
    if not text:
        return None
    if "：" in text:
        title, _, detail = text.partition("：")
        return {"title": title.strip() or "叙事机制", "body": detail.strip()}
    if ":" in text:
        title, _, detail = text.partition(":")
        return {"title": title.strip() or "叙事机制", "body": detail.strip()}
    return {"title": "叙事机制", "body": text}


def _parse_narrative_beats(raw: Any, *, limit: int = 12) -> List[dict]:
    beats: List[dict] = []
    for text in _narrative_string_list(raw, limit=limit):
        match = re.match(r"^([^：:]+)[：:]([\s\S]+)$", text)
        if match:
            beats.append({"time": match.group(1).strip(), "content": match.group(2).strip()})
        else:
            beats.append({"time": "", "content": text})
    return beats


def present_narrative_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "narrative-plan.v1", [])

    core_objective = str(body.get("narrative_core_objective") or "").strip()
    target_range = _format_episode_range_display(body.get("target_episode_range"))

    mechanics: List[dict] = []
    for item in body.get("narrative_mechanics") or []:
        parsed = _parse_narrative_mechanic_item(item)
        if parsed:
            mechanics.append(parsed)

    episodes: List[dict] = []
    for index, item in enumerate(body.get("episode_narrative_designs") or []):
        if not isinstance(item, dict):
            continue
        ep_no = episode_outline_number(item, fallback=index + 1)
        focus = str(item.get("narrative_focus") or "").strip()
        episodes.append(
            {
                "episode_no": ep_no,
                "title": f"第{ep_no}集",
                "focus": focus,
                "emotion_design": str(item.get("audience_emotion_design") or "").strip(),
                "beats": _parse_narrative_beats(item.get("narrative_beat_timing"), limit=10),
                "beat_timeline": _narrative_string_list(item.get("narrative_beat_timing"), limit=10),
                "techniques": _narrative_string_list(item.get("key_narrative_techniques"), limit=8),
                "worldview_points": _narrative_string_list(item.get("worldview_delivery_points"), limit=8),
            }
        )

    consistency = str(body.get("narrative_consistency_check") or "").strip()
    blocks: List[dict] = []
    if core_objective or target_range or mechanics or episodes or consistency:
        blocks.append(
            narrative_plan_block(
                core_objective=core_objective,
                target_range=target_range,
                mechanics=mechanics,
                episodes=episodes,
                consistency_check=consistency,
            )
        )

    summary_parts = [part for part in (target_range, core_objective[:80] if core_objective else "") if part]
    summary = " · ".join(summary_parts[:2])
    return view(artifact_key, "narrative-plan.v1", blocks, summary=summary)


def _market_display_value(key: str, val: Any) -> str:
    if val in (None, "", [], {}):
        return ""
    if key == "target_platform":
        text = str(val).strip()
        return label(text) or text
    if key == "core_genre":
        text = str(val).strip()
        if not text:
            return ""
        localized = localize_phrase_label(text)
        if localized:
            return localized
        parts = []
        for part in text.split("-"):
            part = part.strip()
            if not part:
                continue
            parts.append(localize_phrase_label(part) or label(part) or part)
        if parts:
            return " · ".join(parts)
    return format_scalar(val)


def _is_market_report_composite(body: dict) -> bool:
    """v3.1 复合输出：market-radar + formula-analysis + tear-down-6d 合并为 market_report。"""
    return any(
        key in body
        for key in (
            "explosive_index",
            "hotspot_analysis",
            "dream_three_indicators",
            "six_dimensional_deconstruction",
            "reusable_templates",
        )
    )


def _present_market_report_composite(artifact_key: str, body: dict) -> dict:
    blocks: List[dict] = []
    header_metrics: List[dict] = []
    sections: List[dict] = []

    explosive = body.get("explosive_index")
    level = ""
    comprehensive_score = None
    if isinstance(explosive, dict):
        level = str(explosive.get("level") or "").strip()
        comprehensive_score = explosive.get("comprehensive_score")
        if level:
            header_metrics.append({"label": "爆款等级", "value": level})
        if comprehensive_score is not None:
            header_metrics.append({"label": "综合得分", "value": format_scalar(comprehensive_score)})
        dim = explosive.get("dimension_detail")
        if isinstance(dim, dict) and dim:
            dimensions = [
                {"name": label(key), "score": format_scalar(val)}
                for key, val in dim.items()
                if val not in (None, "", [], {})
            ]
            if dimensions:
                blocks.append(
                    score_board_block(
                        "爆款十维评分",
                        grade=level,
                        total=comprehensive_score,
                        dimensions=dimensions,
                    )
                )

    hotspot = body.get("hotspot_analysis")
    if isinstance(hotspot, dict):
        heat = hotspot.get("current_track_heat")
        if heat is not None:
            header_metrics.append({"label": "赛道热度", "value": format_scalar(heat)})
        hotspot_items: List[dict] = []
        for key in ("user_portrait", "platform_demand_spot", "competitive_landscape"):
            val = hotspot.get(key)
            if val not in (None, "", [], {}):
                hotspot_items.append({"title": label(key), "body": format_scalar(val)})
        if hotspot_items:
            sections.append({"title": "热点市场分析", "tone": "indigo", "items": hotspot_items})

    dream = body.get("dream_three_indicators")
    if isinstance(dream, dict):
        dream_items: List[dict] = []
        for key in ("dream_sense_score", "pay_willingness_score", "emotional_resonance_score"):
            val = dream.get(key)
            if val is not None:
                dream_items.append({"title": label(key), "body": f"{format_scalar(val)} / 10"})
        if dream_items:
            sections.append({"title": "梦境三指标", "tone": "violet", "items": dream_items})

    six_d = body.get("six_dimensional_deconstruction")
    if isinstance(six_d, dict):
        six_items: List[dict] = []
        for key, val in six_d.items():
            if val not in (None, "", [], {}):
                six_items.append({"title": label(key), "body": format_scalar(val)})
        if six_items:
            sections.append({"title": "六维拉片解构", "tone": "violet", "items": six_items})

    templates = body.get("reusable_templates")
    if isinstance(templates, list) and templates:
        template_items: List[dict] = []
        for idx, tpl in enumerate(templates, start=1):
            text = str(tpl).strip()
            if not text:
                continue
            template_items.append(
                {
                    "title": f"模板 {idx}",
                    "body": text,
                    "variant": "highlight" if idx == 1 else "default",
                }
            )
        if template_items:
            sections.append({"title": "可复用爆款模板", "tone": "emerald", "items": template_items})

    if header_metrics or sections:
        blocks.append(
            market_report_block(
                metrics=header_metrics,
                sections=sections,
            )
        )

    summary_parts = []
    if level:
        summary_parts.append(f"爆款 {level}")
    if comprehensive_score is not None:
        summary_parts.append(f"得分 {comprehensive_score}")
    summary = " · ".join(summary_parts)
    return view(artifact_key, "market-report.v1", blocks, summary=summary)


def _present_market_report_legacy(artifact_key: str, body: dict) -> dict:
    basic = body.get("drama_basic_info")
    drama_name = ""
    metrics: List[dict] = []
    if isinstance(basic, dict):
        drama_name = str(basic.get("drama_name") or "").strip()
        if basic.get("total_episodes") is not None:
            metrics.append({"label": "总集数", "value": format_scalar(basic["total_episodes"])})
        platform = basic.get("target_platform")
        if platform not in (None, "", [], {}):
            metrics.append(
                {"label": "目标平台", "value": _market_display_value("target_platform", platform)}
            )
        genre = basic.get("core_genre")
        if genre not in (None, "", [], {}):
            metrics.append({"label": "核心题材", "value": _market_display_value("core_genre", genre)})

    sections: List[dict] = []

    platform_analysis = body.get("platform_market_analysis")
    if isinstance(platform_analysis, dict):
        platform_items: List[dict] = []
        for key in (
            "target_audience_portrait",
            "Douyin_short_drama_current_trend",
            "douyin_short_drama_current_trend",
        ):
            val = platform_analysis.get(key)
            if val in (None, "", [], {}):
                continue
            platform_items.append({"title": label(key), "body": _market_display_value(key, val)})
        if platform_items:
            sections.append({"title": "平台市场分析", "tone": "indigo", "items": platform_items})

    competitiveness = body.get("core_project_competitiveness_analysis")
    if isinstance(competitiveness, dict):
        comp_items: List[dict] = []
        for key in ("IP_foundation", "genre_matching_degree"):
            val = competitiveness.get(key)
            if val not in (None, "", [], {}):
                comp_items.append({"title": label(key), "body": format_scalar(val)})
        if comp_items:
            sections.append({"title": "项目竞争力", "tone": "violet", "items": comp_items})

    commercial = body.get("commercial_operation_forecast")
    if isinstance(commercial, dict):
        commercial_items: List[dict] = []
        for key in ("expected_data_performance", "derivative_expansion_path"):
            val = commercial.get(key)
            if val in (None, "", [], {}):
                continue
            commercial_items.append(
                {
                    "title": label(key),
                    "body": _market_display_value(key, val),
                    "variant": "highlight" if key == "expected_data_performance" else "default",
                }
            )
        if commercial_items:
            sections.append({"title": "商业运营预测", "tone": "emerald", "items": commercial_items})

    risk = body.get("risk_warning_and_suggestion")
    if isinstance(risk, dict):
        risk_items: List[dict] = []
        content_risk = risk.get("content_risk_avoidance")
        if isinstance(content_risk, str) and content_risk.strip():
            risk_items.append(
                {
                    "title": label("content_risk_avoidance"),
                    "body": content_risk.strip(),
                    "variant": "warning",
                }
            )
        release = risk.get("release_strategy_suggestion")
        if isinstance(release, str) and release.strip():
            risk_items.append(
                {
                    "title": label("release_strategy_suggestion"),
                    "body": release.strip(),
                    "variant": "accent",
                }
            )
        if risk_items:
            sections.append({"title": "风险提示与建议", "tone": "amber", "items": risk_items})

    blocks: List[dict] = []
    if drama_name or metrics or sections:
        blocks.append(
            market_report_block(
                drama_name=drama_name,
                metrics=metrics,
                sections=sections,
            )
        )

    summary_parts = [part for part in (drama_name, metrics[0]["value"] if metrics else "") if part]
    summary = " · ".join(summary_parts[:2])
    return view(artifact_key, "market-report.v1", blocks, summary=summary)


def present_market_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "market-report.v1", [])
    if _is_market_report_composite(body):
        return _present_market_report_composite(artifact_key, body)
    return _present_market_report_legacy(artifact_key, body)


def present_market_analysis(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "market-analysis.v1", blocks)

    heat = body.get("theme_heat_rating")
    if not isinstance(heat, dict):
        heat = {}
    match_degree = body.get("爆款特征_matching_degree")

    metrics = []
    if heat.get("current_popularity_score") is not None:
        metrics.append({"label": "当前热度", "value": format_scalar(heat["current_popularity_score"])})
    if heat.get("user_demand_growth_rate") is not None:
        metrics.append({"label": "需求增长", "value": f"{format_scalar(heat['user_demand_growth_rate'])}%"})
    if match_degree is not None:
        metrics.append({"label": "爆款匹配度", "value": format_scalar(match_degree)})
    if metrics:
        blocks.append(metrics_block("市场概览", metrics))

    if heat:
        rows = rows_from_dict(heat, ("trend_tag", "market_saturation", "current_popularity_score"))
        if rows:
            blocks.append(kv_block("题材热度", rows))
        tags = heat.get("core_hot_labels")
        if isinstance(tags, list) and tags:
            blocks.append(list_block("核心热词", [str(x) for x in tags]))

    platform = body.get("platform_traffic_preference")
    if isinstance(platform, dict) and platform:
        rows = rows_from_dict(
            platform,
            ("target_platform", "audience_portrait", "explicit_platform_benefit"),
        )
        if rows:
            blocks.append(kv_block("平台流量偏好", rows))
        tags = platform.get("traffic_weight_tags")
        if isinstance(tags, list) and tags:
            blocks.append(list_block("流量权重标签", [str(x) for x in tags]))

    append_cards(blocks, body, "competitive_product_analysis", "竞品对标")
    topic = body.get("topic_suggestion")
    if isinstance(topic, dict) and topic:
        append_paragraph(blocks, topic, "estimated_market_performance", "预期市场表现")
        append_list(blocks, topic, "optimization_direction", "优化方向")

    score = heat.get("current_popularity_score")
    summary = f"热度 {score} · 匹配度 {match_degree}" if score is not None or match_degree is not None else ""
    return view(artifact_key, "market-analysis.v1", blocks, summary=summary)


def present_formula_analysis(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "formula-analysis.v1", blocks)

    explosive = body.get("explosive_index_calculation")
    if isinstance(explosive, dict):
        metrics = []
        if explosive.get("final_explosive_score") is not None:
            metrics.append({"label": "爆款指数", "value": format_scalar(explosive["final_explosive_score"])})
        if explosive.get("explosive_level"):
            metrics.append({"label": "爆款等级", "value": str(explosive["explosive_level"])})
        dim = explosive.get("dimension_scores")
        if isinstance(dim, dict):
            for key, val in dim.items():
                metrics.append({"label": label(key), "value": format_scalar(val)})
        if metrics:
            blocks.append(metrics_block("爆款指数", metrics))

    dream = body.get("dream_index_evaluation")
    if isinstance(dream, dict):
        metrics = []
        for key in ("sense_of_security", "sense_of_satisfaction", "sense_of_reality"):
            if dream.get(key) is not None:
                metrics.append({"label": label(key), "value": format_scalar(dream[key])})
        if metrics:
            blocks.append(metrics_block("梦境三指标", metrics))
        append_paragraph(blocks, dream, "evaluation_note", "评估说明")

    append_dict_kv(
        blocks,
        body,
        "revenue_forecast",
        "收益预估",
        ("estimated_total_play", "estimated_revenue_input_ratio"),
    )
    append_list(blocks, body, "traffic_password_extraction", "流量密码")
    append_cards(blocks, body, "paid_card_design_framework", "付费卡点设计")

    summary = ""
    if isinstance(explosive, dict) and explosive.get("final_explosive_score") is not None:
        summary = f"爆款指数 {explosive['final_explosive_score']}"
    return view(artifact_key, "formula-analysis.v1", blocks, summary=summary)


def _is_project_brief_composite(body: dict) -> bool:
    """v3.1 立项简报：goal_conflict / rating / cross_section 等复合结构。"""
    return any(
        key in body
        for key in (
            "goal_conflict",
            "rating",
            "cross_section_entry",
            "rhythm_arrangement",
            "compliance_check",
            "dream_three_indicators",
        )
    )


def _present_project_brief_composite(artifact_key: str, body: dict) -> dict:
    goal = body.get("goal_conflict")
    if not isinstance(goal, dict):
        goal = {}

    cross = str(body.get("cross_section_entry") or "").strip()
    headline = str(goal.get("core_goal") or body.get("core_idea") or "").strip()
    opening_hook = cross

    metrics: List[dict] = []
    dream = body.get("dream_three_indicators")
    if isinstance(dream, dict):
        for key in ("dream_sense_score", "pay_willingness_score", "emotional_resonance_score"):
            val = dream.get(key)
            if val is not None:
                metrics.append({"label": label(key), "value": f"{format_scalar(val)}/10"})

    sections: List[dict] = []
    goal_items: List[dict] = []
    for key, variant in (
        ("core_goal", "accent"),
        ("core_conflict", "default"),
        ("opening_stablish", "highlight"),
    ):
        val = goal.get(key)
        if val not in (None, "", [], {}):
            title = "核心目标" if key == "core_goal" else label(key)
            goal_items.append(
                {
                    "title": title,
                    "body": format_scalar(val),
                    "variant": variant,
                }
            )
    if goal_items:
        sections.append({"title": "目标与冲突", "tone": "gold", "layout": "stack", "items": goal_items})

    positioning_items: List[dict] = []
    audience = body.get("target_audience")
    if audience not in (None, "", [], {}):
        positioning_items.append(
            {"title": label("target_audience"), "body": format_scalar(audience), "variant": "highlight"}
        )
    rhythm = body.get("rhythm_arrangement")
    if rhythm not in (None, "", [], {}):
        positioning_items.append({"title": label("rhythm_arrangement"), "body": format_scalar(rhythm)})
    compliance = body.get("compliance_check")
    if compliance not in (None, "", [], {}):
        positioning_items.append(
            {"title": label("compliance_check"), "body": format_scalar(compliance), "variant": "accent"}
        )
    if positioning_items:
        sections.append({"title": "项目定位", "tone": "indigo", "layout": "insight", "items": positioning_items})

    hook_ratings: List[dict] = []
    rating = body.get("rating")
    if isinstance(rating, dict):
        for grade_key, grade in (("s_level", "S"), ("a_level", "A"), ("b_level", "B")):
            val = rating.get(grade_key)
            if val not in (None, "", [], {}):
                hook_ratings.append(
                    {
                        "grade": grade,
                        "title": label(grade_key),
                        "body": format_scalar(val),
                    }
                )

    selling_points = build_labeled_step_items(body.get("differentiated_selling_points") or [])

    blocks: List[dict] = []
    if headline or opening_hook or metrics or sections or hook_ratings or selling_points:
        blocks.append(
            project_brief_block(
                headline=headline,
                opening_hook=opening_hook,
                metrics=metrics,
                sections=sections,
                hook_ratings=hook_ratings,
                selling_points=selling_points,
            )
        )

    summary = headline[:80] if headline else ""
    return view(artifact_key, "project-brief.v1", blocks, summary=summary)


def _present_project_brief_legacy(artifact_key: str, body: dict) -> dict:
    blocks: List[dict] = []
    core = str(body.get("core_idea") or "").strip()
    project_name = str(body.get("title") or "").strip()
    if core:
        blocks.append(
            {
                "type": "hero",
                "title": project_name or "核心创意",
                "subtitle": core,
                "variant": "brief",
            }
        )

    positioning_fields = (
        ("genre_positioning", "genre_positioning"),
        ("target_audience", "target_audience"),
        ("dream_index_forecast", "dream_index_forecast"),
    )
    positioning_cards: List[dict] = []
    for label_key, field_key in positioning_fields:
        val = str(body.get(field_key) or "").strip()
        if val:
            positioning_cards.append({"title": label(label_key), "body": val})
    if positioning_cards:
        blocks.append(
            {
                "type": "cards",
                "title": "项目定位",
                "variant": "profile",
                "layout": "grid_3",
                "items": positioning_cards,
            }
        )

    selling = _string_list(body.get("differentiated_selling_points"))
    if selling:
        step_items = build_labeled_step_items(selling)
        if step_items:
            blocks.append(steps_block("差异化卖点", step_items))

    return view(artifact_key, "project-brief.v1", blocks, summary=core)


def present_project_brief(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "project-brief.v1", [])
    if _is_project_brief_composite(body):
        return _present_project_brief_composite(artifact_key, body)
    return _present_project_brief_legacy(artifact_key, body)


def present_project_review(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "project-review.v1", blocks)

    conclusion = str(body.get("review_conclusion") or "")
    passed = "通过" in conclusion
    metrics = []
    for key, metric_label in (
        ("total_score", "总分"),
        ("market_feasibility_score", "市场可行性"),
        ("creation_feasibility_score", "创作可行性"),
        ("compliance_risk_score", "合规风险"),
    ):
        if body.get(key) is not None:
            metrics.append({"label": metric_label, "value": format_scalar(body[key])})

    notes = body.get("review_notes")
    note_items: List[str] = []
    if isinstance(notes, list):
        note_items = [str(x) for x in notes[:10]]
    elif isinstance(notes, str) and notes.strip():
        note_items = [notes.strip()]

    blocks.append(
        assessment_report_block(
            "立项复审",
            passed=passed if conclusion else None,
            metrics=metrics,
            detail=conclusion,
            notes=note_items,
        )
    )
    return view(artifact_key, "project-review.v1", blocks, summary=conclusion)


def present_lapian_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "lapian-report.v1", blocks)

    append_paragraph(blocks, body, "new_mode", "新模式识别")

    for key in ("emotion_curve", "dialogue_design", "reusable_template"):
        items = body.get(key)
        if isinstance(items, list) and items:
            block = list_block_from_items(label(key), items[:12])
            if block:
                blocks.append(block)

    for key in ("rhythm_control", "camera_language"):
        section = body.get(key)
        if isinstance(section, dict):
            rows = dict_to_kv_rows(section)
            if rows:
                blocks.append(kv_block(label(key), rows))

    analysis = body.get("character_analysis")
    if isinstance(analysis, dict):
        role_labels = {
            "female_protagonist": "女主",
            "male_protagonist": "男主",
            "antagonist": "反派",
        }
        rows = []
        for key, val in analysis.items():
            if isinstance(val, str) and val.strip():
                rows.append({"key": role_labels.get(key, label(key)), "value": val.strip()})
        if rows:
            blocks.append(kv_block("人设分析", rows))

    structures = body.get("structure_analysis")
    if isinstance(structures, list):
        cards = []
        for item in structures[:10]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            segments = item.get("segment_breakdown")
            body_text = "\n".join(str(x) for x in segments[:6]) if isinstance(segments, list) else ""
            cards.append({"title": f"第{ep_id}集结构", "subtitle": "", "body": body_text[:500]})
        if cards:
            blocks.append(cards_block("结构拆解", cards))

    return view(artifact_key, "lapian-report.v1", blocks)


def _normalize_world_setting_body(body: dict) -> dict:
    """兼容 v3.1 字段别名：core_space / core_rules / forbidden_constraint。"""
    out = dict(body)
    if body.get("core_space") is not None and not body.get("core_spaces"):
        space = body["core_space"]
        if isinstance(space, str):
            out["core_spaces"] = [space] if space.strip() else []
        elif isinstance(space, list):
            out["core_spaces"] = space
    if body.get("core_rules") is not None and not body.get("core_world_rules"):
        rules = body["core_rules"]
        out["core_world_rules"] = rules if isinstance(rules, list) else [rules]
    if body.get("forbidden_constraint") is not None and not body.get("taboo_constraints"):
        taboo = body["forbidden_constraint"]
        if isinstance(taboo, list):
            out["taboo_constraints"] = taboo
        elif taboo not in (None, "", [], {}):
            out["taboo_constraints"] = [str(taboo)]
    return out


def _is_world_setting_v31(body: dict) -> bool:
    return any(
        key in body
        for key in ("core_space", "core_rules", "forbidden_constraint")
    )


def _parse_core_space_scenes(text: str) -> tuple[str, List[dict]]:
    line = str(text or "").strip()
    if not line:
        return "", []

    segments = re.split(r"(?=[①②③④⑤⑥⑦⑧⑨⑩])", line)
    if len(segments) <= 1:
        title, body = split_labeled_line(line)
        if title and body:
            return "", [{"title": title, "body": body}]
        return "", [{"title": "核心空间", "body": line}]

    intro = segments[0].strip().rstrip("：:").strip()
    items: List[dict] = []
    for seg in segments[1:]:
        seg = seg.strip()
        if not seg:
            continue
        marker = seg[0] if seg[0] in "①②③④⑤⑥⑦⑧⑨⑩" else ""
        body_text = seg[1:].strip() if marker else seg
        if not body_text:
            continue
        title, body = split_labeled_line(body_text)
        if title and body:
            items.append({"title": title, "body": body, "marker": marker})
        else:
            items.append(
                {
                    "title": f"核心场景 {marker}" if marker else f"核心场景 {len(items) + 1}",
                    "body": body_text,
                    "marker": marker,
                }
            )
    return intro, items


def _present_world_setting_composite(artifact_key: str, body: dict) -> dict:
    era = str(body.get("era_background") or "").strip()

    space_intro = ""
    space_scenes: List[dict] = []
    core_space = body.get("core_space")
    if core_space not in (None, "", [], {}):
        if isinstance(core_space, str):
            space_intro, space_scenes = _parse_core_space_scenes(core_space)
        elif isinstance(core_space, list):
            for idx, item in enumerate(core_space, 1):
                text = str(item).strip()
                if not text:
                    continue
                _, parsed = _parse_core_space_scenes(text)
                space_scenes.extend(parsed or [{"title": f"核心场景 {idx}", "body": text}])

    spaces = _string_list(body.get("core_spaces"))
    if spaces and not space_scenes:
        for idx, text in enumerate(spaces, 1):
            card = space_card_item(text, fallback_title=f"核心场景 {idx}")
            space_scenes.append({"title": card["title"], "body": card["body"]})

    power = body.get("power_structure")
    power_text = ""
    if isinstance(power, str):
        power_text = power.strip()
    elif isinstance(power, dict) and power:
        power_text = " · ".join(
            f"{name}：{format_scalar(desc)}"
            for name, desc in power.items()
            if desc not in (None, "", [], {})
        )
    elif isinstance(power, list) and power:
        power_text = "；".join(str(item).strip() for item in power if str(item or "").strip())

    rules_raw = body.get("core_rules") or body.get("core_world_rules")
    core_rules = build_labeled_step_items(_string_list(rules_raw) if isinstance(rules_raw, list) else [])

    forbidden = body.get("forbidden_constraint") or body.get("taboo_constraints")
    forbidden_text = ""
    if isinstance(forbidden, str):
        forbidden_text = forbidden.strip()
    elif isinstance(forbidden, list) and forbidden:
        forbidden_text = "；".join(str(item).strip() for item in forbidden if str(item or "").strip())

    blocks: List[dict] = []
    if era or space_scenes or power_text or core_rules or forbidden_text:
        blocks.append(
            world_setting_block(
                era_background=era,
                space_intro=space_intro,
                space_scenes=space_scenes,
                power_structure=power_text,
                core_rules=core_rules,
                forbidden_constraint=forbidden_text,
            )
        )

    summary = era[:80] if era else (space_scenes[0]["body"][:80] if space_scenes else "")
    return view(artifact_key, "world-setting.v1", blocks, summary=summary)


def _present_world_setting_legacy(artifact_key: str, body: dict) -> dict:
    blocks: List[dict] = []
    era = str(body.get("era_background") or "").strip()
    if era:
        blocks.append(
            {
                "type": "hero",
                "title": label("era_background"),
                "subtitle": era,
                "variant": "brief",
            }
        )

    spaces = _string_list(body.get("core_spaces"))
    if spaces:
        space_items = [
            space_card_item(text, fallback_title=f"核心场景 {idx}")
            for idx, text in enumerate(spaces[:8], 1)
        ]
        layout = "grid_3" if len(space_items) >= 3 else "grid_2" if len(space_items) == 2 else "stack"
        blocks.append(
            {
                "type": "cards",
                "title": label("core_spaces"),
                "variant": "profile",
                "layout": layout,
                "items": space_items,
            }
        )

    power = body.get("power_structure")
    if isinstance(power, str) and power.strip():
        blocks.append(
            {
                "type": "cards",
                "title": label("power_structure"),
                "variant": "profile",
                "layout": "stack",
                "items": [{"title": "结构说明", "body": power.strip()}],
            }
        )
    elif isinstance(power, dict) and power:
        power_items = [
            {"title": str(name), "body": format_scalar(desc)}
            for name, desc in power.items()
            if desc not in (None, "", [], {})
        ]
        if power_items:
            layout = "grid_2" if len(power_items) >= 2 else "stack"
            blocks.append(
                {
                    "type": "cards",
                    "title": label("power_structure"),
                    "variant": "profile",
                    "layout": layout,
                    "items": power_items,
                }
            )
    elif isinstance(power, list) and power:
        step_items = build_labeled_step_items(power)
        if step_items:
            blocks.append(steps_block(label("power_structure"), step_items))

    special_rules = _string_list(body.get("special_rules"))
    if special_rules:
        if len(special_rules) == 1:
            blocks.append(
                {
                    "type": "callout",
                    "title": label("special_rules"),
                    "text": special_rules[0],
                    "variant": "accent",
                }
            )
        else:
            step_items = build_labeled_step_items(special_rules)
            if step_items:
                blocks.append(steps_block(label("special_rules"), step_items))

    rules = _string_list(body.get("core_world_rules"))
    if rules:
        step_items = build_labeled_step_items(rules)
        if step_items:
            blocks.append(steps_block(label("core_world_rules"), step_items))

    taboo = body.get("taboo_constraints")
    if isinstance(taboo, str) and taboo.strip():
        blocks.append(
            {
                "type": "callout",
                "title": label("taboo_constraints"),
                "text": taboo.strip(),
                "variant": "warning",
            }
        )
    elif isinstance(taboo, list) and taboo:
        step_items = build_labeled_step_items(taboo)
        if step_items:
            blocks.append(
                {
                    "type": "steps",
                    "title": label("taboo_constraints"),
                    "variant": "warning",
                    "items": step_items,
                }
            )

    summary = era or (spaces[0][:240] if spaces else "")
    return view(artifact_key, "world-setting.v1", blocks, summary=summary)


def present_world_setting(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "world-setting.v1", [])
    body = _normalize_world_setting_body(body)
    if _is_world_setting_v31(body):
        return _present_world_setting_composite(artifact_key, body)
    return _present_world_setting_legacy(artifact_key, body)


def present_character_bible(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "character-bible.v1", [])
    if _is_character_bible_v31(body):
        return _present_character_bible_composite(artifact_key, body)
    return _present_character_bible_legacy(artifact_key, body)


def _is_character_bible_v31(body: dict) -> bool:
    if any(
        key in body
        for key in ("relationship_map", "core_supporting_roles", "total_relation_roles", "dream_check")
    ):
        return True
    chars = body.get("characters")
    if not isinstance(chars, list):
        return False
    for char in chars:
        if isinstance(char, dict) and any(k in char for k in ("Want", "Need", "Ghost", "Lie", "Flaw", "char_id")):
            return True
    return False


def _normalize_character_card(char: dict, *, role_tier: str, role_label: str = "") -> dict:
    cid = str(char.get("char_id") or char.get("character_id") or "").strip()
    age = char.get("age")
    return {
        "name": str(char.get("name") or "未命名").strip(),
        "char_id": cid or None,
        "role_tier": role_tier,
        "role_label": role_label or resolve_character_role(char) or "",
        "age": format_scalar(age) if age not in (None, "", [], {}) else "",
        "want": str(char.get("Want") or char.get("want") or char.get("surface_desire") or "").strip(),
        "need": str(char.get("Need") or char.get("need") or char.get("deep_need") or "").strip(),
        "ghost": str(char.get("Ghost") or char.get("ghost") or char.get("core_fear") or "").strip(),
        "lie": str(char.get("Lie") or char.get("lie") or "").strip(),
        "flaw": str(char.get("Flaw") or char.get("flaw") or char.get("character_flaw") or "").strip(),
        "arc": str(char.get("arc") or "").strip(),
        "timbre_tag": str(char.get("timbre_tag") or char.get("voice_tag") or "").strip(),
        "visual_tag": str(char.get("visual_tag") or "").strip(),
        "relation": str(char.get("relation") or "").strip(),
    }


def _parse_relationship_map_line(text: str) -> dict | None:
    line = str(text or "").strip()
    if not line:
        return None
    rel_sep = next((sep for sep in ("↔", "←→", "<->") if sep in line), None)
    if not rel_sep:
        return {"title": line, "body": "", "source_name": "", "target_name": "", "relationship_type": ""}

    source_part, target_part = line.split(rel_sep, 1)
    source = source_part.strip()
    target = target_part.strip()
    desc = ""
    for colon in ("：", ":"):
        if colon in target:
            target, _, desc = target.partition(colon)
            target = target.strip()
            desc = desc.strip()
            break
    title = f"{source} ↔ {target}" if source and target else line
    return {
        "title": title,
        "source_name": source,
        "target_name": target,
        "body": desc,
        "relationship_type": desc[:48] if desc else "",
    }


def _present_character_bible_composite(artifact_key: str, body: dict) -> dict:
    protagonists = [
        _normalize_character_card(char, role_tier="protagonist", role_label="绝对主角")
        for char in (body.get("characters") or [])[:4]
        if isinstance(char, dict)
    ]
    supporting = [
        _normalize_character_card(char, role_tier="supporting", role_label="核心配角")
        for char in (body.get("core_supporting_roles") or [])[:6]
        if isinstance(char, dict)
    ]
    relation_roles = [
        _normalize_character_card(char, role_tier="relation", role_label="关系角色")
        for char in (body.get("total_relation_roles") or [])[:6]
        if isinstance(char, dict)
    ]

    relationships: List[dict] = []
    rel_map = body.get("relationship_map")
    if isinstance(rel_map, list):
        for raw in rel_map[:20]:
            if isinstance(raw, str):
                parsed = _parse_relationship_map_line(raw)
                if parsed:
                    relationships.append(parsed)
            elif isinstance(raw, dict):
                relationships.extend(relationship_graph_entries([raw]))

    network = body.get("relationship_network")
    if network:
        id_map = build_character_id_map(body)
        for char in body.get("core_supporting_roles") or []:
            if isinstance(char, dict):
                cid = char.get("char_id") or char.get("character_id")
                name = char.get("name")
                if cid and name:
                    id_map[str(cid)] = str(name)
        relationships.extend(relationship_graph_entries(network, id_map=id_map))

    dream_raw = body.get("dream_check")
    dream_check: dict = {}
    if isinstance(dream_raw, dict):
        dream_check = {
            "safety_score": dream_raw.get("safety_score"),
            "is_blocking": dream_raw.get("is_blocking"),
            "note": str(dream_raw.get("note") or "").strip(),
        }

    blocks: List[dict] = []
    if protagonists or supporting or relation_roles or relationships or dream_check:
        blocks.append(
            character_bible_block(
                protagonists=protagonists,
                supporting_roles=supporting,
                relation_roles=relation_roles,
                relationships=relationships,
                dream_check=dream_check,
            )
        )

    names = [c["name"] for c in protagonists if c.get("name")]
    summary = " · ".join(names[:2])
    return view(artifact_key, "character-bible.v1", blocks, summary=summary)


def _present_character_bible_legacy(artifact_key: str, payload: Any) -> dict:
    body = payload if isinstance(payload, dict) else {}
    blocks: List[dict] = []

    id_map = build_character_id_map(body)
    roster = character_roster_entries(body.get("characters"))
    if roster:
        blocks.append(character_roster_block(roster))

    network = body.get("relationship_network")
    rel_items = relationship_graph_entries(network, id_map=id_map)
    if rel_items:
        blocks.append(relationship_graph_block(rel_items))

    return view(artifact_key, "character-bible.v1", blocks)


def present_dream_check(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "dream-check.v1", blocks)

    result = str(body.get("check_result") or "")
    passed = "通过" in result
    metrics = []
    scores = body.get("dimension_scores")
    if isinstance(scores, dict) and scores:
        metrics = [{"label": label(k), "value": format_scalar(v)} for k, v in scores.items()]

    notes: List[str] = []
    feedback = body.get("detail_feedback")
    if isinstance(feedback, dict):
        for key, val in feedback.items():
            if isinstance(val, str) and val.strip():
                notes.append(f"{label(str(key))}：{val.strip()}")
    suggestion = body.get("suggestion")
    if isinstance(suggestion, str) and suggestion.strip():
        notes.append(suggestion.strip())

    blocks.append(
        assessment_report_block(
            "梦境指标校验",
            passed=passed if result else None,
            metrics=metrics,
            detail=result,
            notes=notes,
        )
    )
    return view(artifact_key, "dream-check.v1", blocks, summary=result)


def present_emotion_blueprint(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "emotion-blueprint.v1", blocks)

    qdn = body.get("qdn_emotion_model")
    metrics = []
    if isinstance(qdn, dict):
        for key, val in qdn.items():
            if not isinstance(val, dict):
                continue
            name = val.get("dimension_name") or label(str(key))
            target = val.get("global_target")
            if target is not None:
                metrics.append({"label": str(name), "value": format_scalar(target)})
    if metrics:
        blocks.append(metrics_block("QDN 情绪模型", metrics))

    targets = body.get("episode_emotion_targets")
    if isinstance(targets, list):
        episodes = []
        for item in targets[:15]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            episodes.append(
                {
                    "episode_no": str(ep_id),
                    "title": f"第{ep_id}集 · {item.get('episode_name', '')}".strip(" ·"),
                    "subtitle": f"情绪节点 {item.get('total_emotion_nodes', '—')}",
                    "body": "",
                }
            )
        if episodes:
            blocks.append(episode_metrics_list_block("分集情绪目标", episodes))

    ext_cards = emotion_externalization_cards(body.get("emotion_externalization_dictionary") or {})
    if ext_cards:
        blocks.append(cards_block("情绪外化词典", ext_cards))

    return view(artifact_key, "emotion-blueprint.v1", blocks)


def present_series_outline(
    artifact_key: str,
    payload: Any,
    *,
    planned_episodes: int | None = None,
    outline_progress: dict | None = None,
) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "series-outline.v1", [])
    progress_ctx = outline_progress if isinstance(outline_progress, dict) else {}
    if _is_series_outline_v31(body):
        return _present_series_outline_composite(
            artifact_key,
            body,
            planned_episodes=planned_episodes,
            outline_progress=progress_ctx,
        )
    return _present_series_outline_legacy(
        artifact_key,
        body,
        planned_episodes=planned_episodes,
        outline_progress=progress_ctx,
    )


_SERIES_STAGE_DEFS: tuple[tuple[str, str], ...] = (
    ("opening", "开篇"),
    ("warming", "升温"),
    ("climax", "高潮"),
    ("turning", "转折"),
    ("sprint", "冲刺"),
    ("ending", "结局"),
)


def _is_series_outline_v31(body: dict) -> bool:
    if isinstance(body.get("six_stage_structure"), dict):
        return True
    if isinstance(body.get("foreshadowing_list"), list) and body.get("foreshadowing_list"):
        return True
    outlines = body.get("episode_outlines")
    if not isinstance(outlines, list) or not outlines:
        return False
    sample = outlines[0] if isinstance(outlines[0], dict) else {}
    return any(key in sample for key in ("ev_et_tp", "episode_num", "goal_conflict", "dual_track_rhythm", "ending_hook"))


def _normalize_foreshadowing_items(items: Any) -> List[dict]:
    if not isinstance(items, list):
        return []
    normalized: List[dict] = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        normalized.append(
            {
                "type": str(item.get("type") or "").strip(),
                "content": content,
                "buried": item.get("episode_buried"),
                "payoff": item.get("episode_payoff"),
            }
        )
    return normalized


def _build_v31_stage_groups(six_stage: dict, episode_cards: List[dict]) -> List[dict]:
    from apps.drama.series_stage_utils import (
        CANONICAL_STAGE_KEYS,
        normalize_six_stage_structure,
        stage_text_fields,
    )

    normalized = normalize_six_stage_structure(six_stage if isinstance(six_stage, dict) else {})
    title_map = dict(_SERIES_STAGE_DEFS)
    stages: List[dict] = []
    for idx, key in enumerate(CANONICAL_STAGE_KEYS, 1):
        val = normalized.get(key)
        if not isinstance(val, dict):
            continue
        if not stage_text_fields(val) and not str(val.get("episode_range") or "").strip():
            continue
        ep_range = str(val.get("episode_range") or "").strip()
        parsed = parse_episode_range(ep_range)
        stage_eps = []
        if parsed:
            start, end = parsed
            stage_eps = [card for card in episode_cards if start <= card.get("episode_no", 0) <= end]
        proportion = val.get("proportion")
        subtitle_parts = [part for part in (ep_range, f"{proportion}%" if proportion is not None else "") if part]
        stages.append(
            {
                "index": idx,
                "key": key,
                "title": title_map.get(key, key),
                "subtitle": " · ".join(subtitle_parts),
                "summary": stage_text_fields(val),
                "proportion": proportion,
                "highlights": [],
                "episodes": stage_eps,
            }
        )
    return stages


def _present_series_outline_composite(
    artifact_key: str,
    body: dict,
    *,
    planned_episodes: int | None = None,
    outline_progress: dict | None = None,
) -> dict:
    from apps.drama.outline_progress import collect_series_outline_episodes

    progress = outline_progress if isinstance(outline_progress, dict) else {}
    outline_rows = collect_series_outline_episodes(body)
    episode_cards: List[dict] = []
    for index, item in enumerate(outline_rows):
        if not isinstance(item, dict):
            continue
        card = episode_outline_card_item(item, fallback_index=index)
        if card:
            episode_cards.append(card)

    planned = planned_episodes or progress.get("planned") or body.get("total_episodes")
    try:
        planned = int(planned) if planned not in (None, "", [], {}) else 0
    except (TypeError, ValueError):
        planned = 0
    generated_count = progress.get("generated")
    if generated_count in (None, "", [], {}):
        generated_count = len(episode_cards)
    else:
        generated_count = int(generated_count)

    six_stage = body.get("six_stage_structure")
    stages: List[dict] = []
    if isinstance(six_stage, dict):
        stages = _build_v31_stage_groups(six_stage, episode_cards)

    foreshadowing = _normalize_foreshadowing_items(body.get("foreshadowing_list"))
    batch_size = int(progress.get("batch_size") or 10)
    planned_total = planned or generated_count
    episode_batches = build_episode_outline_batches(
        episode_cards,
        planned=planned_total,
        batch_size=batch_size,
    )

    blocks: List[dict] = []
    if stages or foreshadowing or episode_cards or planned:
        blocks.append(
            series_outline_block(
                total_episodes=planned_total,
                generated_episodes=generated_count,
                missing_episodes=progress.get("missing_episodes") or [],
                suggested_range=str(progress.get("suggested_range") or ""),
                episode_batches=episode_batches,
                stages=stages,
                foreshadowing=foreshadowing,
                episodes=episode_cards,
            )
        )

    summary = ""
    if stages and stages[0].get("summary"):
        summary = str(stages[0]["summary"])[:120]
    elif episode_cards:
        summary = episode_cards[0].get("subtitle") or episode_cards[0].get("title") or ""
    return view(artifact_key, "series-outline.v1", blocks, summary=str(summary)[:240])


def _present_series_outline_legacy(artifact_key: str, payload: Any) -> dict:
    body = payload if isinstance(payload, dict) else {}
    blocks: List[dict] = []
    summary = ""

    rhythm = body.get("rhythm_dual_track_validation")
    rhythm_checks: List[dict] = []
    reverse_cards: List[dict] = []
    if isinstance(rhythm, dict):
        rhythm_field_keys = (
            "crisis_depth_check",
            "emotion_platform_check",
            "plot_rhythm_check",
            "emotion_rhythm_check",
            "interaction_design_verification",
        )
        for key in rhythm_field_keys:
            val = rhythm.get(key)
            if isinstance(val, str) and val.strip():
                rhythm_checks.append({"label": label(key), "text": val.strip()})
        reverse_points = rhythm.get("a_level_reverse_points") or []
        if isinstance(reverse_points, list):
            reverse_cards = a_level_reverse_cards(reverse_points)

    outlines = body.get("episode_outlines")
    total_episodes = body.get("total_episodes")
    if total_episodes in (None, "", [], {}) and isinstance(outlines, list) and outlines:
        ep_numbers = [
            episode_outline_number(item, fallback=index + 1)
            for index, item in enumerate(outlines)
            if isinstance(item, dict)
        ]
        if ep_numbers:
            total_episodes = max(ep_numbers)

    if (
        total_episodes not in (None, "", [], {})
        or rhythm_checks
        or reverse_cards
    ):
        blocks.append(
            outline_overview_block(
                total_episodes=total_episodes,
                checks=rhythm_checks,
                reverse_points=reverse_cards,
            )
        )
        summary = rhythm_checks[0]["text"][:240] if rhythm_checks else ""

    stage_narrative = body.get("six_stage_narrative")
    if isinstance(outlines, list) and stage_narrative:
        grouped = build_stage_grouped_outlines(stage_narrative, outlines)
        if grouped:
            blocks.append(stage_outlines_block("分集大纲", grouped))
        elif outlines:
            flat_cards = [
                card
                for index, item in enumerate(outlines[:40])
                if isinstance(item, dict)
                and (card := episode_outline_card_item(item, fallback_index=index))
            ]
            if flat_cards:
                blocks.append(
                    stage_outlines_block(
                        "分集大纲",
                        [
                            {
                                "index": 1,
                                "title": "全剧分集",
                                "subtitle": f"共 {len(flat_cards)} 集",
                                "summary": "",
                                "highlights": [],
                                "episodes": flat_cards,
                            }
                        ],
                    )
                )

    return view(artifact_key, "series-outline.v1", blocks, summary=summary)


def present_hook_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "hook-plan.v1", blocks)

    s_hook = body.get("s_class_hook")
    hero_text = ""
    checks: List[dict] = []
    if isinstance(s_hook, dict):
        hero_text = str(s_hook.get("hook_content") or "")
        calc = s_hook.get("hook_calculation")
        if calc:
            checks.append({"label": "S 级钩子公式", "text": str(calc)})

    a_hooks = body.get("a_class_hooks")
    plan_items: List[dict] = []
    if isinstance(a_hooks, list):
        for item in a_hooks[:12]:
            if not isinstance(item, dict):
                continue
            plan_items.append(
                {
                    "title": str(item.get("hook_id") or "A 级钩子"),
                    "subtitle": "",
                    "body": str(item.get("hook_content") or "")[:600],
                }
            )

    systems = body.get("episode_hook_systems")
    if isinstance(systems, list):
        for item in systems[:15]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            golden = item.get("golden_30s")
            subtitle = ""
            if isinstance(golden, dict):
                subtitle = str(golden.get("0_3s_visual_impact") or "")[:120]
            b_hook = item.get("b_class_hook")
            body_text = ""
            if isinstance(b_hook, dict):
                body_text = str(b_hook.get("hook_content") or "")
            plan_items.append(
                {
                    "title": f"第{ep_id}集钩子体系" if ep_id else "分集钩子",
                    "subtitle": subtitle,
                    "body": body_text[:400],
                }
            )

    if hero_text or checks:
        blocks.append(plan_overview_block("钩子计划", hero_text=hero_text[:240], checks=checks))
    if plan_items:
        blocks.append(plan_items_block("钩子清单", plan_items))

    return view(artifact_key, "hook-plan.v1", blocks)


def present_conflict_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "conflict-plan.v1", blocks)

    core = body.get("core_conflict_system")
    metrics: List[dict] = []
    if isinstance(core, dict):
        for key, val in core.items():
            if format_scalar(val) != "—":
                metrics.append({"label": label(str(key)), "value": format_scalar(val)})

    plan_items: List[dict] = []
    scenes = body.get("key_confrontation_scenes")
    if isinstance(scenes, list):
        for item in scenes[:10]:
            if not isinstance(item, dict):
                continue
            plan_items.append(
                {
                    "title": str(item.get("scene_name") or f"场景 {item.get('scene_id', '')}"),
                    "subtitle": str(item.get("conflict_type") or ""),
                    "body": str(item.get("conflict_upgrade_path") or "")[:500],
                }
            )

    if metrics:
        blocks.append(plan_overview_block("冲突计划", metrics=metrics))
    if plan_items:
        blocks.append(plan_items_block("关键对峙场景", plan_items))

    return view(artifact_key, "conflict-plan.v1", blocks)


def present_reversal_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "reversal-plan.v1", blocks)

    plan_items: List[dict] = []
    for key in (
        "truth_reversals",
        "identity_reversals",
        "situation_reversals",
        "motivation_reversals",
        "relationship_reversals",
    ):
        items = body.get(key)
        if not isinstance(items, list) or not items:
            continue
        cards = reversal_cards([x for x in items if isinstance(x, dict)])
        for card in cards:
            plan_items.append(
                {
                    "title": f"{label(key)} · {card.get('title', '')}".strip(" ·"),
                    "subtitle": card.get("subtitle") or "",
                    "body": card.get("body") or "",
                }
            )

    if plan_items:
        blocks.append(plan_items_block("反转计划", plan_items))
    return view(artifact_key, "reversal-plan.v1", blocks)


def present_emotion_curve(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "emotion-curve.v1", blocks)

    curve = body.get("full_series_emotion_curve")
    metrics: List[dict] = []
    checks: List[dict] = []
    if isinstance(curve, dict):
        if curve.get("total_episodes") is not None:
            metrics.append({"label": "总集数", "value": format_scalar(curve["total_episodes"])})
        for check_key in ("hook_density_check", "crisis_period_et_check", "final_episode_peak_check"):
            check = curve.get(check_key)
            if isinstance(check, dict) and check.get("note"):
                checks.append({"label": label(check_key), "text": str(check["note"])})

    plan_items: List[dict] = []
    markers = body.get("episode_level_emotion_markers")
    if isinstance(markers, list):
        for item in markers[:15]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            body_parts = []
            for nested_key in ("emotion_peak", "emotion_trough", "plot_turning_point"):
                nested = item.get(nested_key)
                if isinstance(nested, dict):
                    for sub_k, sub_v in nested.items():
                        body_parts.append(f"{label(sub_k)}：{sub_v}")
            plan_items.append({"title": f"第{ep_id}集", "subtitle": "", "body": "\n".join(body_parts)[:500]})

    zone = body.get("emotion_platform_zone_check")
    if isinstance(zone, dict) and zone.get("note"):
        checks.append({"label": "情绪平台区校验", "text": str(zone["note"])})

    if metrics or checks:
        blocks.append(plan_overview_block("情绪曲线", metrics=metrics, checks=checks))
    if plan_items:
        blocks.append(plan_items_block("分集情绪标记", plan_items))

    return view(artifact_key, "emotion-curve.v1", blocks)


def present_psychology_guide(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "psychology-guide.v1", blocks)

    immersion = body.get("immersion_design") or {}
    if isinstance(immersion, dict):
        rows = dict_to_kv_rows(immersion)
        if rows:
            blocks.append(kv_block("沉浸设计", rows))

    gaps = body.get("cognitive_gap_design") or []
    if isinstance(gaps, list):
        cards = []
        for item in gaps[:10]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            cards.append(
                {
                    "title": f"第{ep_id}集认知差",
                    "subtitle": str(item.get("known_info") or "")[:80],
                    "body": str(item.get("information_difference_trigger") or "")[:500],
                }
            )
        if cards:
            blocks.append(cards_block("认知差设计", cards))

    expectation = body.get("expectation_management") or {}
    if isinstance(expectation, dict):
        for exp_key, exp_val in expectation.items():
            if not isinstance(exp_val, dict):
                continue
            rows = []
            for sub_key in ("established_expectation", "subversion_design"):
                if exp_val.get(sub_key):
                    rows.append({"key": label(sub_key), "value": str(exp_val[sub_key])[:300]})
            if rows:
                blocks.append(kv_block(label(str(exp_key)), rows))

    triggers = body.get("emotion_resonance_trigger") or []
    if isinstance(triggers, list):
        cards = []
        for item in triggers[:10]:
            if not isinstance(item, dict):
                continue
            cards.append(
                {
                    "title": str(item.get("resonance_point") or "共鸣点"),
                    "subtitle": "",
                    "body": str(item.get("trigger_design") or "")[:500],
                }
            )
        if cards:
            blocks.append(cards_block("情绪共鸣触发", cards))

    return view(artifact_key, "psychology-guide.v1", blocks)


def present_episode_scripts(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    episodes_raw = body.get("episodes") if isinstance(body, dict) else []
    if not isinstance(episodes_raw, list):
        episodes_raw = []

    episodes = []
    for item in episodes_raw[:40]:
        if not isinstance(item, dict):
            continue
        ep_no = item.get("episodeNumber")
        script_content = item.get("scriptContent")
        beats: List[dict] = []
        embedded_checkpoint = ""
        if script_content not in (None, "", [], {}):
            beats, embedded_checkpoint = parse_episode_script_content(script_content)

        scene_count = len({beat["sceneHeader"] for beat in beats if beat.get("sceneHeader")})
        episodes.append(
            {
                "episodeNumber": ep_no,
                "title": str(item.get("title") or f"第{ep_no}集"),
                "memoryCheckPoint": embedded_checkpoint,
                "sceneCount": scene_count,
                "beats": beats,
            }
        )

    blocks = (
        [script_episodes_block("分集剧本", episodes, total_episodes=len(episodes))]
        if episodes
        else []
    )
    summary = f"共 {len(episodes)} 集剧本" if episodes else ""
    return view(artifact_key, "episode-scripts.v1", blocks, summary=summary)


def present_visual_prompts(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "visual-prompts.v1", blocks)

    value = body.get("value")
    if isinstance(value, list) and value and isinstance(value[0], dict):
        blocks.extend(visual_prompt_episode_blocks(value))
    elif isinstance(value, str) and value.strip():
        blocks.append(paragraph_block("视觉提示词", value.strip()))

    return view(artifact_key, "visual-prompts.v1", blocks)


def present_adaptation_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "adaptation-plan.v1", blocks)

    info = body.get("project_basic_info")
    if isinstance(info, dict):
        rows = dict_to_kv_rows(
            info,
            key_labels={
                "genre": "题材",
                "platform": "平台",
                "core_theme": "核心主题",
                "total_episodes": "总集数",
            },
        )
        if rows:
            blocks.append(kv_block("项目基本信息", rows))

    rhythm = body.get("rhythm_control")
    if isinstance(rhythm, dict):
        rows = dict_to_kv_rows(rhythm)
        if rows:
            blocks.append(kv_block("节奏控制", rows))

    breakdown = body.get("episode_breakdown")
    if isinstance(breakdown, list):
        cards = adaptation_breakdown_cards([x for x in breakdown if isinstance(x, dict)])
        if cards:
            blocks.append(cards_block("分集改编拆解", cards))

    return view(artifact_key, "adaptation-plan.v1", blocks)


def present_review_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "review-report.v1", [])

    passed_raw = body.get("passed")
    pacing_raw = body.get("pacingPassed")
    passed = bool(passed_raw) if passed_raw is not None else None
    pacing_passed = bool(pacing_raw) if pacing_raw is not None else None
    issues = normalize_review_issues(body.get("issues"))

    blocks: List[dict] = [
        review_overview_block(
            passed=passed,
            pacing_passed=pacing_passed,
            issue_count=len(issues),
        )
    ]
    if issues:
        blocks.append(review_issues_block("问题清单", issues))

    if passed is True and not issues:
        summary = "审查通过，未发现问题"
    elif passed is True:
        summary = f"审查通过，记录 {len(issues)} 项待优化问题"
    elif passed is False:
        summary = f"审查未通过，共 {len(issues)} 项问题"
    else:
        summary = f"共 {len(issues)} 项问题" if issues else ""

    return view(artifact_key, "review-report.v1", blocks, summary=summary)


def present_reader_review(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "reader-review.v1", blocks)

    retention = body.get("first_episode_retention_forecast") or {}
    if isinstance(retention, dict):
        metrics = []
        if retention.get("score") is not None:
            metrics.append({"label": "首集留存分", "value": format_scalar(retention["score"])})
        if metrics:
            blocks.append(metrics_block("首集留存预估", metrics))
        if retention.get("empathy_performance"):
            blocks.append(paragraph_block("共情表现", str(retention["empathy_performance"])))

    payment = body.get("payment_conversion_forecast") or {}
    if isinstance(payment, dict):
        metrics = []
        if payment.get("estimated_payment_rate") is not None:
            metrics.append({"label": "预估付费率", "value": f"{payment['estimated_payment_rate']}%"})
        if payment.get("total_payment_card_points") is not None:
            metrics.append({"label": "付费卡点数", "value": format_scalar(payment["total_payment_card_points"])})
        if metrics:
            blocks.append(metrics_block("付费转化预估", metrics))
        grades = payment.get("grade_distribution") or []
        if isinstance(grades, list) and grades:
            blocks.append(list_block("卡点分级", [str(x) for x in grades[:5]]))

    append_list(blocks, body, "abandon_risk_points", "弃剧风险点")

    emotion = body.get("emotion_performance") or {}
    if isinstance(emotion, dict):
        for list_key, list_title in (
            ("top_3_touching_scenes", "最触达场景"),
            ("top_3_abandon_nodes", "最易弃剧节点"),
        ):
            items = emotion.get(list_key) or []
            if isinstance(items, list) and items:
                blocks.append(list_block(list_title, [str(x) for x in items[:5]]))

    return view(artifact_key, "reader-review.v1", blocks)


def present_emotion_audit(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "emotion-audit.v1", blocks)

    repairs = body.get("repair_suggestions")
    if isinstance(repairs, list):
        cards = []
        for item in repairs[:10]:
            if not isinstance(item, dict):
                continue
            cards.append(
                {
                    "title": f"第{item.get('target_episode', '—')}集 · {item.get('insert_position', '')}".strip(" ·"),
                    "subtitle": "",
                    "body": str(item.get("insert_event") or "")[:500],
                }
            )
        if cards:
            blocks.append(cards_block("修复建议", cards))

    plateau = body.get("continuous_plateau_zone")
    if isinstance(plateau, list) and plateau:
        blocks.append(list_block("连续平台区", format_list_items(plateau, limit=10)))

    deviations = body.get("over_deviation_episodes")
    if isinstance(deviations, list):
        cards = []
        for item in deviations[:10]:
            if not isinstance(item, dict):
                continue
            nodes = item.get("deviation_nodes")
            body_lines = [format_deviation_node(node) for node in (nodes or []) if isinstance(node, dict)]
            cards.append(
                {
                    "title": f"第{item.get('episodeNumber', '—')}集偏离",
                    "subtitle": f"共 {len(body_lines)} 个偏离节点" if body_lines else "",
                    "body": "\n\n".join(body_lines)[:600],
                }
            )
        if cards:
            blocks.append(cards_block("偏离集数", cards))

    extractions = body.get("episode_emotion_extraction")
    if isinstance(extractions, list):
        episodes = []
        for item in extractions[:15]:
            if not isinstance(item, dict):
                continue
            ep_no = item.get("episodeNumber") or ""
            peak_raw = item.get("emotion_peak_ev")
            valley_raw = item.get("emotion_valley_et")
            peak_val = peak_raw.get("value") if isinstance(peak_raw, dict) else None
            valley_val = valley_raw.get("value") if isinstance(valley_raw, dict) else None
            subtitle = ""
            if peak_val is not None and valley_val is not None:
                subtitle = f"峰值 {peak_val} / 低谷 {valley_val}"
            peak = format_emotion_marker(peak_raw)
            valley = format_emotion_marker(valley_raw)
            body_parts = []
            if peak:
                body_parts.append(f"峰值：{peak}")
            if valley:
                body_parts.append(f"低谷：{valley}")
            tps = item.get("emotion_tp")
            if isinstance(tps, list) and tps:
                body_parts.append("转折点：")
                body_parts.extend(format_list_items(tps, limit=5))
            nodes = item.get("actual_emotion_nodes")
            if isinstance(nodes, list) and nodes:
                body_parts.append("情绪节点：")
                body_parts.extend(format_emotion_node_line(n) for n in nodes if isinstance(n, dict))
            episodes.append(
                {
                    "episode_no": str(ep_no),
                    "title": f"第{ep_no}集情绪",
                    "subtitle": subtitle[:120],
                    "body": "\n".join(body_parts)[:600],
                }
            )
        if episodes:
            blocks.append(episode_metrics_list_block("分集情绪提取", episodes))

    return view(artifact_key, "emotion-audit.v1", blocks)


def present_quality_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "quality-report.v1", [])

    dimensions = build_quality_dimensions(body.get("scores"), body.get("details"))
    rating = str(body.get("rating") or "").strip()
    total_score = body.get("total_score")
    fuse_raw = body.get("fuse_triggered")
    fuse_triggered = bool(fuse_raw) if fuse_raw is not None else None

    summary = ""
    if rating and total_score not in (None, "", [], {}):
        summary = f"{rating} 级 · 总分 {format_scalar(total_score)}"

    blocks: List[dict] = [
        quality_report_block(
            rating=rating,
            total_score=total_score,
            max_total=100,
            fuse_triggered=fuse_triggered,
            dimensions=dimensions,
        )
    ]

    return view(artifact_key, "quality-report.v1", blocks, summary=summary[:240])


def present_word_count_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "word-count-report.v1", blocks)

    overview = body.get("global_overview")
    if isinstance(overview, dict):
        rows = []
        for key, val in overview.items():
            if format_scalar(val) != "—":
                rows.append({"key": label(str(key)), "value": format_scalar(val)})
        if rows:
            blocks.append(kv_block("全局概览", rows))

    episodes_raw = body.get("episode_detail_list")
    if isinstance(episodes_raw, list):
        episodes = []
        for item in episodes_raw[:20]:
            if not isinstance(item, dict):
                continue
            ep_no = item.get("episode_number") or ""
            compliance = item.get("compliance_check")
            subtitle = ""
            if isinstance(compliance, dict) and compliance.get("status"):
                subtitle = str(compliance["status"])
            episodes.append(
                {
                    "episode_no": str(ep_no),
                    "title": f"第{ep_no}集",
                    "subtitle": subtitle,
                    "body": " · ".join(
                        filter(
                            None,
                            [
                                f"总字数 {item['total_cjk_chars']}" if item.get("total_cjk_chars") else "",
                                f"台词比 {item['dialogue_ratio']}%" if item.get("dialogue_ratio") else "",
                                str(item.get("adjust_suggestion") or ""),
                            ],
                        )
                    )[:500],
                }
            )
        if episodes:
            blocks.append(episode_metrics_list_block("分集字数明细", episodes))

    return view(artifact_key, "word-count-report.v1", blocks)


def present_style_check(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "style-check.v1", blocks)

    verdict = str(body.get("final_verification") or "")
    passed = "通过" in verdict or "对齐" in verdict
    notes: List[str] = []
    drama_type = body.get("drama_type")
    if drama_type not in (None, "", [], {}):
        notes.append(f"剧种类型：{format_scalar(drama_type)}")

    drift = body.get("style_drift_detection_result")
    if isinstance(drift, dict):
        for row in nested_check_rows(drift):
            notes.append(f"{row['key']}：{row['value']}")

    repairs = body.get("drift_repair_record")
    if isinstance(repairs, list) and repairs:
        notes.extend(format_list_items(repairs, limit=10))

    blocks.append(
        assessment_report_block(
            "风格校验",
            passed=passed if verdict else None,
            metrics=[],
            detail=verdict,
            notes=notes,
        )
    )
    return view(artifact_key, "style-check.v1", blocks, summary=verdict)


def present_visual_pack(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "visual-pack.v1", blocks)

    anchors = body.get("character_visual_anchors") or []
    if isinstance(anchors, list):
        cards = []
        for item in anchors[:10]:
            if not isinstance(item, dict):
                continue
            cards.append(
                {
                    "title": str(item.get("name") or "角色"),
                    "subtitle": str(item.get("character_id") or ""),
                    "body": str(item.get("fixed_appearance") or "")[:500],
                }
            )
        if cards:
            blocks.append(cards_block("角色视觉锚点", cards))

    for key, title in (("single_frame_prompts", "单帧提示词"), ("video_prompts", "视频提示词")):
        items = body.get(key) or []
        if not isinstance(items, list):
            continue
        cards = []
        for item in items[:15]:
            if not isinstance(item, dict):
                continue
            cards.append(
                {
                    "title": f"场景 {item.get('scene_id', '—')}",
                    "subtitle": "",
                    "body": str(item.get("prompt") or "")[:600],
                }
            )
        if cards:
            blocks.append(cards_block(title, cards))

    return view(artifact_key, "visual-pack.v1", blocks)


def present_storyboard(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "storyboard.v1", blocks)

    items = body.get("storyboard_list")
    if isinstance(items, list):
        cards = storyboard_to_cards([x for x in items if isinstance(x, dict)])
        if cards:
            blocks.append(cards_block("分镜脚本", cards))

    summary = f"共 {len(items)} 个镜头" if isinstance(items, list) and items else ""
    return view(artifact_key, "storyboard.v1", blocks, summary=summary)


def present_post_assets(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "post-assets.v1", blocks)

    duration = body.get("duration_adjustment") or {}
    if isinstance(duration, dict):
        if duration.get("adjust_note"):
            blocks.append(paragraph_block("时长调整说明", str(duration["adjust_note"])))
        details = duration.get("adjust_details") or []
        if isinstance(details, list) and details:
            if isinstance(details, list) and details:
                block = list_block_from_items("调整明细", details[:10])
                if block:
                    blocks.append(block)

    for key, title in (("dubbing_emotion_script", "配音情绪脚本"), ("vertical_screen_subtitles", "竖屏字幕")):
        items = body.get(key) or []
        if not isinstance(items, list):
            continue
        cards = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue
            ep_no = item.get("episode_number") or ""
            sub_items = item.get("emotion_timeline") if key == "dubbing_emotion_script" else item.get("subtitle_list")
            body_text = ""
            if isinstance(sub_items, list):
                body_text = "\n".join(format_list_items(sub_items, limit=20))[:800]
            cards.append({"title": f"第{ep_no}集", "subtitle": "", "body": body_text})
        if cards:
            blocks.append(cards_block(title, cards))

    return view(artifact_key, "post-assets.v1", blocks)


def present_marketing_kit(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "marketing-kit.v1", blocks)

    sections: List[dict] = []
    for key, title in (("titles", "标题候选"), ("streaming_titles", "流媒体标题")):
        items = body.get(key)
        if isinstance(items, list) and items:
            sections.append({"title": title, "kind": "list", "items": [str(x) for x in items[:12]]})

    synopses = body.get("synopses")
    if isinstance(synopses, dict):
        rows = dict_to_kv_rows(
            synopses,
            key_labels={"mini_50": "50字简介", "standard_100": "100字简介", "long_200": "200字简介"},
        )
        if rows:
            sections.append({"title": "剧情简介", "kind": "kv", "rows": rows})

    payment = body.get("payment_copy")
    if isinstance(payment, dict):
        rows = dict_to_kv_rows(payment, key_labels={"s_level_card": "S级付费文案", "a_level_card": "A级付费文案"})
        if rows:
            sections.append({"title": "付费文案", "kind": "kv", "rows": rows})

    strategy = body.get("platform_diff_strategy")
    if isinstance(strategy, dict):
        platform_labels = {"douyin": "抖音", "wechat": "微信", "kuaishou": "快手"}
        rows = []
        for plat_key, plat_val in strategy.items():
            if isinstance(plat_val, str) and plat_val.strip():
                rows.append({"key": platform_labels.get(plat_key, str(plat_key)), "value": plat_val[:300]})
        if rows:
            sections.append({"title": "平台差异化策略", "kind": "kv", "rows": rows})

    if sections:
        blocks.append(deliverable_sections_block("营销物料", sections))

    return view(artifact_key, "marketing-kit.v1", blocks)


def present_compliance_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "compliance-report.v1", [])

    block = build_compliance_report_view(body)
    summary = block.get("conclusion") or ("合规通过" if block.get("passed") else "合规未通过")
    return view(artifact_key, "compliance-report.v1", [block], summary=summary[:240])


def present_delivery_pack(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "delivery-pack.v1", blocks)

    sections: List[dict] = []
    if body.get("quality_score") is not None:
        sections.append(
            {
                "title": "交付质量",
                "kind": "metrics",
                "items": [{"label": "质量分", "value": format_scalar(body["quality_score"])}],
            }
        )

    evaluation = body.get("evaluation_summary")
    if isinstance(evaluation, str) and evaluation.strip():
        sections.append({"title": "评估摘要", "kind": "paragraph", "text": evaluation.strip()})

    files = body.get("delivery_file_list")
    if isinstance(files, list) and files:
        sections.append({"title": "交付文件清单", "kind": "list", "items": [str(x) for x in files[:20]]})

    quality_ok = body.get("quality_check_result")
    if quality_ok is not None:
        sections.append(
            {
                "title": "质量检查结果",
                "kind": "kv",
                "rows": [{"key": "状态", "value": "通过" if quality_ok is True else format_scalar(quality_ok)}],
            }
        )

    compliance_ok = body.get("compliance_check_result")
    if compliance_ok is not None:
        sections.append(
            {
                "title": "合规检查结果",
                "kind": "kv",
                "rows": [{"key": "状态", "value": format_scalar(compliance_ok)}],
            }
        )

    word_count = body.get("word_count_check_result")
    if isinstance(word_count, dict):
        rows = dict_to_kv_rows(word_count)
        if rows:
            sections.append({"title": "字数检查结果", "kind": "kv", "rows": rows})

    if sections:
        blocks.append(deliverable_sections_block("交付包", sections))

    return view(artifact_key, "delivery-pack.v1", blocks)


def present_evolution_proposal(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "evolution-proposal.v1", blocks)

    track1 = body.get("轨道一_技能进化提案")
    if isinstance(track1, dict):
        pattern = track1.get("共性缺陷模式判定")
        if isinstance(pattern, str) and pattern.strip():
            blocks.append(paragraph_block("共性缺陷模式", pattern.strip()))
        skills = track1.get("SKILL更新提案")
        if isinstance(skills, list):
            cards = []
            for item in skills[:10]:
                if not isinstance(item, dict):
                    continue
                cards.append(
                    {
                        "title": str(item.get("target_skill_file") or "技能更新"),
                        "subtitle": f"优先级：{item.get('priority', '—')}",
                        "body": str(item.get("update_content") or "")[:500],
                    }
                )
            if cards:
                blocks.append(cards_block("技能进化提案", cards))

    inspirations = body.get("轨道二_灵感归档条目")
    if isinstance(inspirations, list):
        cards = []
        for item in inspirations[:15]:
            if not isinstance(item, dict):
                continue
            title = str(
                item.get("hook_mechanism")
                or item.get("reversal_mechanism")
                or item.get("structure_innovation")
                or item.get("classic_dialogue")
                or "灵感条目"
            )
            cards.append(
                {
                    "title": title,
                    "subtitle": str(item.get("applicable_scene") or ""),
                    "body": str(item.get("core_logic") or item.get("source_script_position") or "")[:500],
                }
            )
        if cards:
            blocks.append(cards_block("灵感归档", cards))

    return view(artifact_key, "evolution-proposal.v1", blocks)


def present_polished_script(artifact_key: str, payload: Any) -> dict:
    """精修剧本 — 结构与 episode-scripts 相同，schema 为 polished-script.v1。"""
    result = present_episode_scripts(artifact_key, payload)
    result["schema_version"] = "polished-script.v1"
    return result


def present_production_pack(artifact_key: str, payload: Any) -> dict:
    """制作发行物料包 — 复用 delivery-pack 展示逻辑。"""
    result = present_delivery_pack(artifact_key, payload)
    result["schema_version"] = "production-pack.v1"
    return result


SCHEMA_PRESENTERS = {
    # v3.1 十二角色 SSOT
    "project-brief.v1": present_project_brief,
    "market-report.v1": present_market_report,
    "world-setting.v1": present_world_setting,
    "character-bible.v1": present_character_bible,
    "series-outline.v1": present_series_outline,
    "narrative-plan.v1": present_narrative_plan,
    "episode-scripts.v1": present_episode_scripts,
    "review-report.v1": present_review_report,
    "quality-report.v1": present_quality_report,
    "polished-script.v1": present_polished_script,
    "production-pack.v1": present_production_pack,
    "compliance-report.v1": present_compliance_report,
    # 历史产物 / fixture 兼容
    "market-analysis.v1": present_market_analysis,
    "formula-analysis.v1": present_formula_analysis,
    "project-review.v1": present_project_review,
    "lapian-report.v1": present_lapian_report,
    "dream-check.v1": present_dream_check,
    "emotion-blueprint.v1": present_emotion_blueprint,
    "hook-plan.v1": present_hook_plan,
    "conflict-plan.v1": present_conflict_plan,
    "reversal-plan.v1": present_reversal_plan,
    "emotion-curve.v1": present_emotion_curve,
    "psychology-guide.v1": present_psychology_guide,
    "visual-prompts.v1": present_visual_prompts,
    "adaptation-plan.v1": present_adaptation_plan,
    "reader-review.v1": present_reader_review,
    "emotion-audit.v1": present_emotion_audit,
    "word-count-report.v1": present_word_count_report,
    "style-check.v1": present_style_check,
    "visual-pack.v1": present_visual_pack,
    "storyboard.v1": present_storyboard,
    "post-assets.v1": present_post_assets,
    "marketing-kit.v1": present_marketing_kit,
    "delivery-pack.v1": present_delivery_pack,
    "evolution-proposal.v1": present_evolution_proposal,
}

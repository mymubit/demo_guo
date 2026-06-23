# -*- coding: utf-8 -*-
"""各 schema_version 专用产物展示器。"""
from __future__ import annotations

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
    build_quality_dimensions,
    build_stage_grouped_outlines,
    cards_block,
    character_roster_block,
    character_roster_entries,
    checks_block,
    deliverable_sections_block,
    dict_to_kv_rows,
    emotion_externalization_cards,
    episode_metrics_list_block,
    format_deviation_node,
    format_emotion_marker,
    format_emotion_node_line,
    format_list_items,
    format_scalar,
    kv_block,
    label,
    list_block,
    list_block_from_items,
    metrics_block,
    nested_check_rows,
    normalize_payload,
    normalize_review_issues,
    outline_overview_block,
    paragraph_block,
    parse_episode_script_content,
    plan_items_block,
    plan_overview_block,
    quality_report_block,
    relationship_graph_block,
    relationship_graph_entries,
    reversal_cards,
    review_issues_block,
    review_overview_block,
    rows_from_dict,
    script_episodes_block,
    stage_outlines_block,
    storyboard_to_cards,
    view,
    visual_prompt_episode_blocks,
    world_sections_block,
)

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


def present_project_brief(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "project-brief.v1", blocks)

    core = str(body.get("core_idea") or "").strip()
    if core:
        blocks.append({"type": "hero", "title": "立项简报", "subtitle": core})

    append_scalar_kv(
        blocks,
        body,
        ("genre_positioning", "target_audience", "dream_index_forecast"),
        "项目定位",
    )

    selling = body.get("three_differentiated_selling_points")
    if isinstance(selling, list) and selling:
        blocks.append(list_block("三大差异化卖点", [str(x).strip() for x in selling[:12] if str(x).strip()]))

    return view(artifact_key, "project-brief.v1", blocks, summary=core)


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


def present_world_setting(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "world-setting.v1", blocks)

    sections: List[dict] = []
    era = body.get("era_background")
    if isinstance(era, str) and era.strip():
        sections.append({"title": "时代背景", "kind": "paragraph", "text": era.strip()})

    power = body.get("power_structure")
    if isinstance(power, list) and power:
        if all(isinstance(x, str) for x in power):
            sections.append({"title": "权力结构", "kind": "list", "items": [str(x) for x in power[:20]]})
        else:
            items = format_list_items(power, limit=20)
            if items:
                sections.append({"title": "权力结构", "kind": "list", "items": items})

    rules = body.get("core_rules")
    if isinstance(rules, list) and rules:
        sections.append({"title": "核心规则", "kind": "list", "items": [str(x) for x in rules[:12]]})

    special = body.get("special_rules")
    if isinstance(special, str) and special.strip():
        sections.append({"title": "特殊规则", "kind": "paragraph", "text": special.strip()})

    constraints = body.get("taboo_constraints")
    if isinstance(constraints, list) and constraints:
        sections.append({"title": "禁忌约束", "kind": "list", "items": [str(x) for x in constraints[:12]]})

    core_space = body.get("core_space")
    if isinstance(core_space, str) and core_space.strip():
        sections.append({"title": "核心场景", "kind": "paragraph", "text": core_space.strip()})

    if sections:
        blocks.append(world_sections_block(sections))

    return view(artifact_key, "world-setting.v1", blocks)


def present_character_bible(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "character-bible.v1", blocks)

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


def present_series_outline(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    summary = ""
    if not isinstance(body, dict):
        return view(artifact_key, "series-outline.v1", blocks)

    rhythm = body.get("rhythm_control")
    rhythm_checks: List[dict] = []
    reverse_cards: List[dict] = []
    if isinstance(rhythm, dict):
        crisis = rhythm.get("crisis_depth_check")
        if isinstance(crisis, str) and crisis.strip():
            rhythm_checks.append({"label": label("crisis_depth_check"), "text": crisis.strip()})
        platform = rhythm.get("emotion_platform_check")
        if isinstance(platform, str) and platform.strip():
            rhythm_checks.append({"label": label("emotion_platform_check"), "text": platform.strip()})
        reverse_points = rhythm.get("a_level_reverse_points") or []
        if isinstance(reverse_points, list):
            reverse_cards = a_level_reverse_cards(reverse_points)

    total_episodes = body.get("total_episodes")
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

    outlines = body.get("episode_outlines")
    stage_narrative = body.get("six_stage_narrative")
    if isinstance(outlines, list) and isinstance(stage_narrative, dict):
        grouped = build_stage_grouped_outlines(stage_narrative, outlines)
        if grouped:
            blocks.append(stage_outlines_block("分集大纲", grouped))

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


SCHEMA_PRESENTERS = {
    "market-analysis.v1": present_market_analysis,
    "formula-analysis.v1": present_formula_analysis,
    "project-brief.v1": present_project_brief,
    "project-review.v1": present_project_review,
    "lapian-report.v1": present_lapian_report,
    "world-setting.v1": present_world_setting,
    "character-bible.v1": present_character_bible,
    "dream-check.v1": present_dream_check,
    "emotion-blueprint.v1": present_emotion_blueprint,
    "series-outline.v1": present_series_outline,
    "hook-plan.v1": present_hook_plan,
    "conflict-plan.v1": present_conflict_plan,
    "reversal-plan.v1": present_reversal_plan,
    "emotion-curve.v1": present_emotion_curve,
    "psychology-guide.v1": present_psychology_guide,
    "episode-scripts.v1": present_episode_scripts,
    "visual-prompts.v1": present_visual_prompts,
    "adaptation-plan.v1": present_adaptation_plan,
    "review-report.v1": present_review_report,
    "reader-review.v1": present_reader_review,
    "emotion-audit.v1": present_emotion_audit,
    "quality-report.v1": present_quality_report,
    "word-count-report.v1": present_word_count_report,
    "style-check.v1": present_style_check,
    "visual-pack.v1": present_visual_pack,
    "storyboard.v1": present_storyboard,
    "post-assets.v1": present_post_assets,
    "marketing-kit.v1": present_marketing_kit,
    "compliance-report.v1": present_compliance_report,
    "delivery-pack.v1": present_delivery_pack,
    "evolution-proposal.v1": present_evolution_proposal,
}

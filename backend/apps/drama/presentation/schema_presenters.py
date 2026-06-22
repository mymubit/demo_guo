# -*- coding: utf-8 -*-
"""各 schema_version 专用产物展示器。"""
from __future__ import annotations

from typing import Any, List

from apps.drama.presentation.base import (
    adaptation_breakdown_cards,
    append_cards,
    append_dict_kv,
    append_list,
    append_paragraph,
    append_scalar_kv,
    cards_block,
    checks_block,
    compliance_passed,
    dict_to_kv_rows,
    emotion_externalization_cards,
    episode_outline_cards,
    format_detail_list,
    format_deviation_node,
    format_emotion_marker,
    format_emotion_node_line,
    format_list_items,
    format_scalar,
    kv_block,
    label,
    list_block,
    metrics_block,
    nested_check_rows,
    normalize_payload,
    paragraph_block,
    phase_narrative_cards,
    qdn_model_metrics,
    relationship_network_cards,
    reversal_cards,
    rows_from_dict,
    score_board_block,
    script_content_to_beats,
    script_episodes_block,
    storyboard_to_cards,
    verdict_block,
    view,
    visual_prompt_episode_blocks,
)

def present_market_analysis(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "market-analysis.v1", blocks)

    heat = body.get("theme_heat_rating") or {}
    if not isinstance(heat, dict):
        heat = {}
    match_degree = body.get("爆款特征_matching_degree")
    if match_degree is None:
        match_degree = body.get("hit_feature_matching_degree")

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
        tags = heat.get("core_hot_labels") or []
        if isinstance(tags, list) and tags:
            blocks.append(list_block("核心热词", [str(x) for x in tags]))

    platform = body.get("platform_traffic_preference") or {}
    if isinstance(platform, dict) and platform:
        rows = rows_from_dict(
            platform,
            ("target_platform", "audience_portrait", "explicit_platform_benefit"),
        )
        if rows:
            blocks.append(kv_block("平台流量偏好", rows))
        tags = platform.get("traffic_weight_tags") or []
        if isinstance(tags, list) and tags:
            blocks.append(list_block("流量权重标签", [str(x) for x in tags]))

    append_cards(blocks, body, "competitive_product_analysis", "竞品对标")
    topic = body.get("topic_suggestion") or {}
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

    explosive = body.get("explosive_index_calculation") or {}
    if isinstance(explosive, dict):
        metrics = []
        if explosive.get("final_explosive_score") is not None:
            metrics.append({"label": "爆款指数", "value": format_scalar(explosive["final_explosive_score"])})
        if explosive.get("explosive_level"):
            metrics.append({"label": "爆款等级", "value": str(explosive["explosive_level"])})
        dim = explosive.get("dimension_scores") or {}
        if isinstance(dim, dict):
            for key, val in dim.items():
                metrics.append({"label": label(key), "value": format_scalar(val)})
        if metrics:
            blocks.append(metrics_block("爆款指数", metrics))

    dream = body.get("dream_index_evaluation") or {}
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

    core = str(body.get("core_idea") or body.get("coreIdea") or "").strip()
    if core:
        blocks.append({"type": "hero", "title": "立项简报", "subtitle": core})

    append_scalar_kv(
        blocks,
        body,
        ("genre_positioning", "target_audience", "dream_index_forecast"),
        "项目定位",
    )

    selling = (
        body.get("three_unique_selling_points")
        or body.get("differentiated_selling_points")
        or body.get("sellingPoints")
        or []
    )
    if isinstance(selling, list) and selling:
        blocks.append(list_block("差异化卖点", [str(x) for x in selling[:12]]))

    return view(artifact_key, "project-brief.v1", blocks, summary=core)


def present_project_review(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "project-review.v1", blocks)

    conclusion = str(body.get("review_conclusion") or body.get("verdict") or "")
    passed = str(conclusion).lower() in ("pass", "approved", "通过") or "通过" in conclusion
    metrics = []
    for key, metric_label in (
        ("total_score", "总分"),
        ("market_feasibility_score", "市场可行性"),
        ("creation_feasibility_score", "创作可行性"),
        ("compliance_risk_score", "合规风险"),
    ):
        if body.get(key) is not None:
            metrics.append({"label": metric_label, "value": format_scalar(body[key])})
    if metrics:
        blocks.append(metrics_block("立项评分", metrics))

    blocks.append(
        verdict_block(
            "复审结论",
            passed=passed,
            detail=conclusion or ("审查通过" if passed else "需进一步评估"),
        )
    )
    notes = body.get("review_notes")
    if isinstance(notes, list) and notes:
        blocks.append(list_block("复审说明", [str(x) for x in notes[:10]]))
    elif isinstance(notes, str) and notes.strip():
        blocks.append(paragraph_block("复审说明", notes.strip()))
    return view(artifact_key, "project-review.v1", blocks, summary=conclusion)


def present_lapian_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "lapian-report.v1", blocks)

    append_paragraph(blocks, body, "new_mode", "新模式识别")

    for key in ("emotion_curve", "dialogue_design", "reusable_template"):
        items = body.get(key)
        if isinstance(items, list) and items and all(isinstance(x, str) for x in items):
            blocks.append(list_block(label(key), [str(x) for x in items[:12]]))

    for key in ("rhythm_control", "camera_language"):
        section = body.get(key)
        if isinstance(section, dict):
            rows = dict_to_kv_rows(section)
            if rows:
                blocks.append(kv_block(label(key), rows))

    analysis = body.get("character_analysis") or {}
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

    structures = body.get("structure_analysis") or []
    if isinstance(structures, list):
        cards = []
        for item in structures[:10]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            segments = item.get("segment_breakdown") or []
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

    append_scalar_kv(blocks, body, ("era_background",), "时代背景")

    power = body.get("power_structure")
    if isinstance(power, dict):
        rows = dict_to_kv_rows(power)
        if rows:
            blocks.append(kv_block("权力结构", rows))
    elif power:
        blocks.append(kv_block("权力结构", [{"key": "结构", "value": format_scalar(power)}]))

    rules = body.get("core_rules") or body.get("core_world_rules") or []
    if isinstance(rules, list) and rules:
        blocks.append(list_block("核心规则", [str(x) for x in rules[:12]]))

    special = body.get("special_rules")
    if isinstance(special, list):
        blocks.append(list_block("特殊规则", [str(x) for x in special[:12]]))
    elif isinstance(special, str) and special.strip():
        blocks.append(paragraph_block("特殊规则", special.strip()))

    constraints = body.get("taboo_constraints") or []
    if isinstance(constraints, list) and constraints:
        blocks.append(list_block("禁忌约束", [str(x) for x in constraints[:12]]))

    spaces = body.get("core_spaces") or []
    if isinstance(spaces, list) and spaces:
        if isinstance(spaces[0], str):
            blocks.append(list_block("核心场景", [str(x) for x in spaces[:12]]))
        else:
            cards = []
            for space in spaces[:12]:
                if not isinstance(space, dict):
                    continue
                cards.append(
                    {
                        "title": str(space.get("space_name") or "场景"),
                        "subtitle": "",
                        "body": str(space.get("vertical_show_feature") or "")[:500],
                    }
                )
            if cards:
                blocks.append(cards_block("核心场景", cards))

    return view(artifact_key, "world-setting.v1", blocks)


def present_character_bible(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "character-bible.v1", blocks)

    cards = []
    for group_key in ("main_characters", "characters", "core_supporting_characters"):
        chars = body.get(group_key) or []
        if not isinstance(chars, list):
            continue
        for char in chars[:12]:
            if not isinstance(char, dict):
                continue
            name = str(char.get("name") or "未命名")
            identity = str(char.get("role_position") or char.get("identity") or "")
            want = char.get("surface_want") or char.get("want") or ""
            need = char.get("deep_need") or char.get("need") or ""
            cards.append(
                {
                    "title": name,
                    "subtitle": identity,
                    "tags": [str(char.get("timbre_tag") or char.get("timbre_ta") or "")]
                    if char.get("timbre_tag") or char.get("timbre_ta")
                    else [],
                    "body": " · ".join(
                        filter(
                            None,
                            [
                                f"欲望：{want}" if want else "",
                                f"需求：{need}" if need else "",
                                f"缺陷：{char['flaw']}" if char.get("flaw") else "",
                                f"弧光：{char['character_arc']}" if char.get("character_arc") else "",
                            ],
                        )
                    )[:500],
                }
            )
    if cards:
        blocks.append(cards_block("人物档案", cards))

    network = body.get("relationship_network")
    if isinstance(network, str) and network.strip():
        blocks.append(paragraph_block("关系网络", network.strip()))
    elif isinstance(network, list):
        rel_cards = relationship_network_cards(network)
        if rel_cards:
            blocks.append(cards_block("关系网络", rel_cards))
        elif network:
            blocks.append(list_block("关系网络", [str(x) for x in network[:20]]))

    return view(artifact_key, "character-bible.v1", blocks)


def present_dream_check(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "dream-check.v1", blocks)

    result = str(body.get("check_result") or body.get("result") or "")
    passed = str(result).lower() in ("pass", "passed", "通过") or "通过" in result
    blocks.append(verdict_block("梦境指标校验", passed=passed, detail=result or "—"))

    scores = body.get("dimension_scores") or {}
    if isinstance(scores, dict) and scores:
        metrics = [{"label": label(k), "value": format_scalar(v)} for k, v in scores.items()]
        blocks.append(metrics_block("维度得分", metrics))

    feedback = body.get("detail_feedback") or {}
    if isinstance(feedback, dict):
        for key, val in feedback.items():
            if isinstance(val, str) and val.strip():
                blocks.append(paragraph_block(label(str(key)), val.strip()))
    elif isinstance(feedback, str) and feedback.strip():
        blocks.append(paragraph_block("详细反馈", feedback.strip()))

    append_paragraph(blocks, body, "suggestion", "优化建议")
    return view(artifact_key, "dream-check.v1", blocks, summary=result)


def present_emotion_blueprint(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "emotion-blueprint.v1", blocks)

    qdn = body.get("qdn_emotion_model") or {}
    metrics = qdn_model_metrics(qdn if isinstance(qdn, dict) else {})
    if metrics:
        blocks.append(metrics_block("QDN 情绪模型", metrics))
    if isinstance(qdn, dict):
        for key, val in qdn.items():
            if isinstance(val, dict) and val.get("description"):
                blocks.append(paragraph_block(str(val.get("dimension_name") or label(str(key))), str(val["description"])))

    targets = body.get("episode_emotion_targets") or []
    if isinstance(targets, list):
        cards = []
        for item in targets[:10]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            cards.append(
                {
                    "title": f"第{ep_id}集 · {item.get('episode_name', '')}".strip(" ·"),
                    "subtitle": f"情绪节点 {item.get('total_emotion_nodes', '—')}",
                    "body": "",
                }
            )
        if cards:
            blocks.append(cards_block("分集情绪目标", cards))

    ext_cards = emotion_externalization_cards(body.get("emotion_externalization_dictionary") or {})
    if ext_cards:
        blocks.append(cards_block("情绪外化词典", ext_cards))

    return view(artifact_key, "emotion-blueprint.v1", blocks)


def present_series_outline(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "series-outline.v1", blocks)

    rhythm = body.get("rhythm_control") or body.get("rhythm_control_verification") or {}
    if isinstance(rhythm, dict):
        for beat_key in ("plot_beat", "emotion_beat"):
            beats = rhythm.get(beat_key) or []
            if isinstance(beats, list) and beats:
                blocks.append(list_block(label(beat_key), [str(x) for x in beats[:10]]))
        for note_key in ("a_level_reversal_check", "emotion_platform_check", "double_track_rhythm_note"):
            note = rhythm.get(note_key)
            if isinstance(note, str) and note.strip():
                blocks.append(paragraph_block(label(note_key), note.strip()))
        compliance = rhythm.get("compliance_check")
        if isinstance(compliance, dict):
            rows = dict_to_kv_rows(compliance)
            if rows:
                blocks.append(kv_block("节奏合规校验", rows))

    six_phase = (
        body.get("six_phase_narrative_structure")
        or body.get("six_stage_narrative")
        or {}
    )
    phase_cards = phase_narrative_cards(six_phase if isinstance(six_phase, dict) else {})
    if phase_cards:
        blocks.append(cards_block("六段叙事", phase_cards))

    outlines = body.get("episode_outlines") or body.get("episodes") or []
    if isinstance(outlines, list):
        cards = episode_outline_cards(outlines)
        if cards:
            blocks.append(cards_block("分集大纲", cards))

    return view(artifact_key, "series-outline.v1", blocks)


def present_hook_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "hook-plan.v1", blocks)

    s_hook = body.get("s_class_hook") or {}
    if isinstance(s_hook, dict):
        content = str(s_hook.get("hook_content") or s_hook.get("content") or "")
        if content:
            blocks.append({"type": "hero", "title": "S 级钩子", "subtitle": content[:240]})
        calc = s_hook.get("hook_calculation")
        if calc:
            blocks.append(paragraph_block("S 级钩子公式", str(calc)))

    append_cards(blocks, body, "a_class_hooks", "A 级钩子")

    systems = body.get("episode_hook_systems") or []
    if isinstance(systems, list):
        cards = []
        for item in systems[:15]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or item.get("episodeNumber") or ""
            golden = item.get("golden_30s") or {}
            subtitle = ""
            if isinstance(golden, dict):
                subtitle = str(golden.get("0_3s_visual_impact") or golden.get("visual_impact") or "")[:120]
            b_hook = item.get("b_class_hook") or {}
            body_text = ""
            if isinstance(b_hook, dict):
                body_text = str(b_hook.get("hook_content") or "")
            cards.append(
                {
                    "title": f"第{ep_id}集钩子体系" if ep_id else "分集钩子",
                    "subtitle": subtitle,
                    "body": body_text[:400],
                }
            )
        if cards:
            blocks.append(cards_block("分集钩子体系", cards))

    return view(artifact_key, "hook-plan.v1", blocks)


def present_conflict_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "conflict-plan.v1", blocks)

    core = body.get("core_conflict_system") or {}
    if isinstance(core, dict):
        rows = []
        for key, val in core.items():
            if format_scalar(val) != "—":
                rows.append({"key": label(str(key)), "value": format_scalar(val)})
        if rows:
            blocks.append(kv_block("核心冲突体系", rows))

    scenes = body.get("key_confrontation_scenes") or []
    if isinstance(scenes, list) and scenes and isinstance(scenes[0], dict):
        cards = []
        for item in scenes[:10]:
            cards.append(
                {
                    "title": str(item.get("scene_name") or f"场景 {item.get('scene_id', '')}"),
                    "subtitle": str(item.get("conflict_type") or ""),
                    "body": str(item.get("conflict_upgrade_path") or "")[:500],
                }
            )
        if cards:
            blocks.append(cards_block("关键对峙场景", cards))
    return view(artifact_key, "conflict-plan.v1", blocks)


def present_reversal_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "reversal-plan.v1", blocks)

    for key in (
        "truth_reversals",
        "identity_reversals",
        "situation_reversals",
        "motivation_reversals",
        "relationship_reversals",
    ):
        items = body.get(key) or []
        if isinstance(items, list) and items:
            cards = reversal_cards([x for x in items if isinstance(x, dict)])
            if cards:
                blocks.append(cards_block(label(key), cards))
    return view(artifact_key, "reversal-plan.v1", blocks)


def present_emotion_curve(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "emotion-curve.v1", blocks)

    curve = body.get("full_series_emotion_curve") or {}
    if isinstance(curve, dict) and curve:
        if curve.get("total_episodes") is not None:
            blocks.append(
                metrics_block(
                    "全剧情绪曲线",
                    [{"label": "总集数", "value": format_scalar(curve["total_episodes"])}],
                )
            )
        for check_key in ("hook_density_check", "crisis_period_et_check", "final_episode_peak_check"):
            check = curve.get(check_key)
            if isinstance(check, dict) and check.get("note"):
                blocks.append(paragraph_block(label(check_key), str(check["note"])))

    markers = body.get("episode_level_emotion_markers") or []
    if isinstance(markers, list):
        cards = []
        for item in markers[:10]:
            if not isinstance(item, dict):
                continue
            ep_id = item.get("episode_id") or ""
            body_parts = []
            for nested_key in ("emotion_peak", "emotion_trough", "plot_turning_point"):
                nested = item.get(nested_key)
                if isinstance(nested, dict):
                    for sub_k, sub_v in nested.items():
                        body_parts.append(f"{label(sub_k)}：{sub_v}")
            cards.append({"title": f"第{ep_id}集", "subtitle": "", "body": "\n".join(body_parts)[:500]})
        if cards:
            blocks.append(cards_block("分集情绪标记", cards))

    zone = body.get("emotion_platform_zone_check") or {}
    if isinstance(zone, dict) and zone.get("note"):
        blocks.append(paragraph_block("情绪平台区校验", str(zone["note"])))

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
                    "body": str(item.get("information_difference_trigger") or item.get("unknown_info") or "")[:500],
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
    episodes_raw = []
    if isinstance(body, dict):
        episodes_raw = body.get("episodes") or []
    elif isinstance(body, list):
        episodes_raw = body

    episodes = []
    for item in episodes_raw[:20]:
        if not isinstance(item, dict):
            continue
        ep_no = item.get("episodeNumber") or item.get("episode_number") or item.get("episode_id")
        beats = []
        script_content = item.get("scriptContent") or item.get("script_content") or []
        if isinstance(script_content, list) and script_content:
            beats = script_content_to_beats(script_content)
        else:
            for script in (item.get("scripts") or item.get("scenes") or [])[:40]:
                if not isinstance(script, dict):
                    continue
                beats.append(
                    {
                        "sceneHeader": str(script.get("sceneHeader") or script.get("scene_header") or ""),
                        "action": str(script.get("action") or script.get("content") or ""),
                        "dialogue": str(script.get("dialogue") or ""),
                    }
                )

        checkpoint = item.get("memoryCheckpoint") or item.get("memory_checkpoint") or {}
        checkpoint_text = ""
        if isinstance(checkpoint, dict):
            parts = []
            for ck in ("characterStates", "activeClues", "foreshadowStatus"):
                val = checkpoint.get(ck)
                if isinstance(val, list):
                    parts.extend(str(x) for x in val)
                elif val:
                    parts.append(str(val))
            checkpoint_text = "；".join(parts)

        episodes.append(
            {
                "episodeNumber": ep_no,
                "title": str(item.get("title") or item.get("episode_name") or f"第{ep_no}集"),
                "memoryCheckPoint": checkpoint_text or str(item.get("memoryCheckPoint") or ""),
                "beats": beats,
            }
        )

    blocks = [script_episodes_block("分集剧本", episodes)] if episodes else []
    summary = f"共 {len(episodes)} 集剧本" if episodes else ""
    return view(artifact_key, "episode-scripts.v1", blocks, summary=summary)


def present_visual_prompts(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "visual-prompts.v1", blocks)

    value = body.get("value") or body.get("prompts") or []
    if isinstance(value, list) and value and isinstance(value[0], dict):
        blocks.extend(visual_prompt_episode_blocks(value))
    elif isinstance(value, str) and value.strip():
        blocks.append(paragraph_block("视觉提示词", value.strip()))
    elif isinstance(value, list):
        blocks.append(list_block("视觉提示词", [str(x) for x in value[:30]]))

    return view(artifact_key, "visual-prompts.v1", blocks)


def present_adaptation_plan(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "adaptation-plan.v1", blocks)

    info = body.get("project_basic_info") or {}
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

    rhythm = body.get("rhythm_control") or {}
    if isinstance(rhythm, dict):
        rows = dict_to_kv_rows(rhythm)
        if rows:
            blocks.append(kv_block("节奏控制", rows))

    breakdown = body.get("episode_breakdown") or []
    if isinstance(breakdown, list):
        cards = adaptation_breakdown_cards([x for x in breakdown if isinstance(x, dict)])
        if cards:
            blocks.append(cards_block("分集改编拆解", cards))

    return view(artifact_key, "adaptation-plan.v1", blocks)


def present_review_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "review-report.v1", [])

    passed = bool(body.get("passed"))
    issues = []
    for item in body.get("issues") or []:
        if isinstance(item, str):
            issues.append(item)
        elif isinstance(item, dict):
            text = item.get("description") or item.get("message") or item.get("detail") or ""
            issue_type = item.get("type") or item.get("category") or item.get("sceneId") or ""
            issues.append(f"[{issue_type}] {text}".strip() if issue_type else str(text))

    detail = "审查通过"
    if not passed:
        detail = "审查未通过，需修改"
    if body.get("pacingPassed") is False:
        detail += "（节奏未通过）"

    blocks = [verdict_block("审稿结论", passed=passed, detail=detail, issues=issues[:20])]
    return view(artifact_key, "review-report.v1", blocks)


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

    repairs = body.get("repair_suggestions") or []
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

    plateau = body.get("continuous_plateau_zone") or []
    if isinstance(plateau, list) and plateau:
        blocks.append(list_block("连续平台区", format_list_items(plateau, limit=10)))

    deviations = body.get("over_deviation_episodes") or []
    if isinstance(deviations, list):
        cards = []
        for item in deviations[:10]:
            if not isinstance(item, dict):
                continue
            nodes = item.get("deviation_nodes") or []
            body_lines = [format_deviation_node(node) for node in nodes if isinstance(node, dict)]
            cards.append(
                {
                    "title": f"第{item.get('episodeNumber', '—')}集偏离",
                    "subtitle": f"共 {len(body_lines)} 个偏离节点" if body_lines else "",
                    "body": "\n\n".join(body_lines)[:600],
                }
            )
        if cards:
            blocks.append(cards_block("偏离集数", cards))

    extractions = body.get("episode_emotion_extraction") or []
    if isinstance(extractions, list):
        cards = []
        for item in extractions[:10]:
            if not isinstance(item, dict):
                continue
            ep_no = item.get("episodeNumber") or ""
            peak_raw = item.get("emotion_peak_ev") or {}
            valley_raw = item.get("emotion_valley_et") or {}
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
            tps = item.get("emotion_tp") or []
            if isinstance(tps, list) and tps:
                body_parts.append("转折点：")
                body_parts.extend(format_list_items(tps, limit=5))
            nodes = item.get("actual_emotion_nodes") or []
            if isinstance(nodes, list) and nodes:
                body_parts.append("情绪节点：")
                body_parts.extend(format_emotion_node_line(n) for n in nodes if isinstance(n, dict))
            cards.append(
                {
                    "title": f"第{ep_no}集情绪",
                    "subtitle": subtitle[:120],
                    "body": "\n".join(body_parts)[:600],
                }
            )
        if cards:
            blocks.append(cards_block("分集情绪提取", cards))

    return view(artifact_key, "emotion-audit.v1", blocks)


def present_quality_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "quality-report.v1", [])

    scores = body.get("scores") or body.get("dimensions") or {}
    dimensions = []
    if isinstance(scores, dict):
        dimensions = [{"name": label(str(k)), "score": v} for k, v in scores.items()]
    elif isinstance(scores, list):
        for row in scores:
            if isinstance(row, dict):
                dimensions.append(
                    {
                        "name": str(row.get("name") or row.get("dimension") or ""),
                        "score": row.get("score") or row.get("value"),
                    }
                )

    suspend = body.get("suspend_status") or {}
    summary = str(body.get("core_evaluation") or body.get("summary") or body.get("verdict") or "")
    if isinstance(suspend, dict) and suspend.get("trigger_suspend"):
        summary = f"【暂缓】{suspend.get('suspend_reason', '')} {summary}".strip()

    break_check = body.get("break_check") or {}
    if isinstance(break_check, dict) and break_check:
        parts = []
        if "format_pass" in break_check:
            parts.append(f"格式{'通过' if break_check['format_pass'] else '未通过'}")
        if "dream_safety_pass" in break_check:
            parts.append(f"梦境安全{'通过' if break_check['dream_safety_pass'] else '未通过'}")
        if parts:
            summary = f"{' · '.join(parts)}。{summary}".strip()

    blocks = [
        score_board_block(
            "质量评分",
            grade=str(body.get("final_rating") or body.get("rating") or body.get("grade") or ""),
            total=body.get("total_score") or body.get("overall_score") or body.get("overallScore"),
            summary=summary,
            dimensions=dimensions,
        )
    ]
    return view(artifact_key, "quality-report.v1", blocks, summary=summary[:240])


def present_word_count_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "word-count-report.v1", blocks)

    overview = body.get("global_overview") or {}
    if isinstance(overview, dict):
        rows = []
        for key, val in overview.items():
            if format_scalar(val) != "—":
                rows.append({"key": label(str(key)), "value": format_scalar(val)})
        if rows:
            blocks.append(kv_block("全局概览", rows))

    episodes = body.get("episode_detail_list") or []
    if isinstance(episodes, list):
        cards = []
        for item in episodes[:10]:
            if not isinstance(item, dict):
                continue
            ep_no = item.get("episode_number") or ""
            compliance = item.get("compliance_check") or {}
            subtitle = ""
            if isinstance(compliance, dict) and compliance.get("status"):
                subtitle = str(compliance["status"])
            cards.append(
                {
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
        if cards:
            blocks.append(cards_block("分集字数明细", cards))

    return view(artifact_key, "word-count-report.v1", blocks)


def present_style_check(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "style-check.v1", blocks)

    verdict = str(body.get("final_verification") or body.get("verdict") or "")
    passed = "通过" in verdict or "对齐" in verdict or str(verdict).lower() in ("pass", "passed")
    blocks.append(verdict_block("风格校验", passed=passed, detail=verdict or "—"))
    append_scalar_kv(blocks, body, ("drama_type",), "剧种类型")

    drift = body.get("style_drift_detection_result") or {}
    if isinstance(drift, dict):
        rows = nested_check_rows(drift)
        if rows:
            blocks.append(kv_block("风格漂移检测", rows))

    repairs = body.get("drift_repair_record") or []
    if isinstance(repairs, list) and repairs:
        blocks.append(list_block("漂移修复记录", [str(x) for x in repairs[:10]]))

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

    items = body.get("storyboard_list") or body.get("shots") or []
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
            blocks.append(list_block("调整明细", [str(x) for x in details[:10]]))

    for key, title in (("dubbing_emotion_script", "配音情绪脚本"), ("vertical_screen_subtitles", "竖屏字幕")):
        items = body.get(key) or []
        if not isinstance(items, list):
            continue
        cards = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue
            ep_no = item.get("episode_number") or ""
            sub_items = item.get("emotion_timeline") or item.get("subtitle_list") or []
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

    for key in ("titles", "streaming_titles"):
        append_list(blocks, body, key)

    synopses = body.get("synopses") or {}
    if isinstance(synopses, dict):
        rows = dict_to_kv_rows(
            synopses,
            key_labels={"mini_50": "50字简介", "standard_100": "100字简介", "long_200": "200字简介"},
        )
        if rows:
            blocks.append(kv_block("剧情简介", rows))

    payment = body.get("payment_copy") or {}
    if isinstance(payment, dict):
        rows = dict_to_kv_rows(payment, key_labels={"s_level_card": "S级付费文案", "a_level_card": "A级付费文案"})
        if rows:
            blocks.append(kv_block("付费文案", rows))

    strategy = body.get("platform_diff_strategy") or {}
    if isinstance(strategy, dict):
        platform_labels = {"douyin": "抖音", "wechat": "微信", "kuaishou": "快手"}
        rows = []
        for plat_key, plat_val in strategy.items():
            if isinstance(plat_val, str) and plat_val.strip():
                rows.append({"key": platform_labels.get(plat_key, str(plat_key)), "value": plat_val[:300]})
        if rows:
            blocks.append(kv_block("平台差异化策略", rows))

    return view(artifact_key, "marketing-kit.v1", blocks)


def present_compliance_report(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    if not isinstance(body, dict):
        return view(artifact_key, "compliance-report.v1", [])

    verdict = str(
        body.get("overall_compliance_decision")
        or body.get("final_verdict")
        or body.get("overall_result")
        or body.get("verdict")
        or ""
    )
    checks = []
    for level, result_key, detail_key in (
        ("P0", "p0_check_result", "p0_risk_details"),
        ("P1", "p1_check_result", "p1_risk_details"),
        ("P2", "p2_check_result", "p2_optimization_suggestions"),
    ):
        result = body.get(result_key)
        if result is not None and result != "":
            checks.append(
                {
                    "level": level,
                    "status": format_scalar(result),
                    "detail": format_detail_list(body.get(detail_key)),
                }
            )

    for legacy_key in ("p0_risk_check", "p1_risk_check", "p2_risk_check"):
        block = body.get(legacy_key)
        if isinstance(block, dict):
            checks.append(
                {
                    "level": legacy_key.replace("_risk_check", "").upper(),
                    "status": format_scalar(block.get("level") or block.get("result")),
                    "detail": str(block.get("details") or block.get("detail") or ""),
                }
            )

    nine = body.get("nine_dimension_risk_scan") or body.get("nine_dimension_risk_check") or {}
    if isinstance(nine, dict) and nine:
        if nine.get("details"):
            checks.append({"level": "九维扫描", "status": "—", "detail": str(nine["details"])[:400]})
        else:
            status_parts = []
            all_pass = True
            for dim_key, dim_val in nine.items():
                if dim_key in ("details", "values"):
                    continue
                if isinstance(dim_val, str):
                    status_parts.append(f"{label(dim_key)}:{dim_val}")
                    if dim_val.lower() != "pass":
                        all_pass = False
            values = nine.get("values")
            if isinstance(values, list):
                status_parts.insert(0, "价值观：" + "、".join(str(v) for v in values))
            checks.append(
                {
                    "level": "九维扫描",
                    "status": "通过" if all_pass else "需关注",
                    "detail": " · ".join(status_parts[:12]),
                }
            )

    remark = str(body.get("remark") or "")
    blocks = [
        checks_block(
            "合规审查",
            passed=compliance_passed(verdict),
            verdict=verdict or "—",
            items=checks,
        )
    ]
    if remark:
        blocks.append(paragraph_block("备注", remark))

    return view(artifact_key, "compliance-report.v1", blocks, summary=verdict or remark[:240])


def present_delivery_pack(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "delivery-pack.v1", blocks)

    if body.get("quality_score") is not None:
        blocks.append(
            metrics_block("交付质量", [{"label": "质量分", "value": format_scalar(body["quality_score"])}])
        )

    append_paragraph(blocks, body, "evaluation_summary", "评估摘要")
    append_list(blocks, body, "delivery_file_list", "交付文件清单")

    quality_ok = body.get("quality_check_result")
    if isinstance(quality_ok, bool):
        blocks.append(
            kv_block(
                "质量检查结果",
                [{"key": "状态", "value": "通过" if quality_ok else "未通过"}],
            )
        )

    compliance_ok = body.get("compliance_check_result")
    if compliance_ok not in (None, ""):
        blocks.append(kv_block("合规检查结果", [{"key": "状态", "value": format_scalar(compliance_ok)}]))

    word_count = body.get("word_count_check_result") or {}
    if isinstance(word_count, dict):
        rows = dict_to_kv_rows(word_count)
        if rows:
            blocks.append(kv_block("字数检查结果", rows))

    return view(artifact_key, "delivery-pack.v1", blocks)


def present_evolution_proposal(artifact_key: str, payload: Any) -> dict:
    body = normalize_payload(payload)
    blocks: List[dict] = []
    if not isinstance(body, dict):
        return view(artifact_key, "evolution-proposal.v1", blocks)

    track1 = body.get("轨道一_技能进化提案") or body.get("skill_evolution_proposal") or {}
    if isinstance(track1, dict):
        append_paragraph(blocks, track1, "共性缺陷模式判定", "共性缺陷模式")
        skills = track1.get("SKILL更新提案") or track1.get("skill_updates") or []
        if isinstance(skills, list):
            cards = []
            for item in skills[:10]:
                if not isinstance(item, dict):
                    continue
                cards.append(
                    {
                        "title": str(item.get("target_skill_file") or item.get("skill") or "技能更新"),
                        "subtitle": f"优先级：{item.get('priority', '—')}",
                        "body": str(item.get("update_content") or item.get("content") or "")[:500],
                    }
                )
            if cards:
                blocks.append(cards_block("技能进化提案", cards))

    inspirations = body.get("轨道二_灵感归档条目") or body.get("inspiration_archive") or []
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
                or item.get("applicable_scene")
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

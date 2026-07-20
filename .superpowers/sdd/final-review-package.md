# Final review package — prompt-schema-field-ssot
MERGE_BASE: c557f6e8ef6ff6593673965882c3bf7811fd5e97
HEAD: 389bcf0ac8524773907c51aacd7c16ca8ae3779e

## Deferred findings from task reviews
- Task 2 minors: enum hardcode in test; shrink_strings untested
- Task 3 Important: prompt_builder commit swept pre-existing progressive-disclosure WIP; adjacent commits 835206c/287b37f incidental
- Task 4 minor: story-bible SKILL larger than minimal checklist edit

## Commits
389bcf0 docs: declare schema as sole field SSOT; keep normalize as fallback only
b593297 feat(ui): replace brand button with action and shell variants
e8f7ca1 fix: ensure review owners can observe job LLM I/O
6b2d121 fix: make story-bible primary fewshot a schema-valid full example
14b9fc3 feat(ui): introduce dual-accent design tokens
c3c6e00 fix: load quality weights from YAML and stop thin suggestion placeholders
9e9c14b docs: align role SKILL output checklists with schema field keys
2a9e78f fix: reject thin compliance reports and keep judge rule budget
5e83c69 feat: inject nested schema field table and skeleton into role prompts
287b37f fix: make quality normalize test suite pass schema validation
835206c test: lock judge rule injection and sparse evidence regressions
e94892c feat: build schema-valid output skeletons for prompt contracts
571fa72 feat: extract nested required paths from artifact JSON Schema

## Stat (full range)
 .superpowers/sdd/task-3-report.md                  |   31 +
 backend/apps/core/schema_validator.py              |    2 +-
 backend/apps/drama/services/artifact_normalize.py  | 1400 ++++++++++++++++++++
 backend/apps/drama/services/generation_service.py  |  545 +++++++-
 backend/apps/drama/services/prompt_builder.py      |  222 +++-
 .../apps/drama/services/schema_prompt_contract.py  |  302 +++++
 .../apps/drama/tests/test_artifact_normalize.py    |  601 +++++++++
 .../apps/drama/tests/test_job_llm_logs_access.py   |  135 ++
 .../drama/tests/test_judge_prompt_injection.py     |   91 ++
 .../drama/tests/test_prompt_schema_injection.py    |   93 ++
 .../drama/tests/test_quality_report_substance.py   |   53 +
 .../drama/tests/test_schema_prompt_contract.py     |  193 +++
 drama-skills/knowledge/output-schemas.md           |    5 +-
 .../roles/drama-compliance-guard/role.yaml         |    4 +
 drama-skills/roles/drama-episode-designer/SKILL.md |   28 +-
 drama-skills/roles/drama-script-scorer/role.yaml   |   11 +
 drama-skills/roles/drama-story-bible/SKILL.md      |   94 +-
 .../roles/drama-story-bible/fewshots.v1.yaml       |  177 +++
 frontend/src/components/ui/Button.tsx              |   14 +-
 frontend/src/components/ui/button.test.tsx         |   17 +
 .../components/workbench/JobLlmCallLogsPanel.tsx   |  171 +++
 .../src/components/workbench/QualityLoopPanel.tsx  |    7 +-
 frontend/src/pages/ExternalReviewRecordsPage.tsx   |  408 ++++++
 frontend/src/styles/index.css                      |   35 +-
 frontend/src/styles/tokens.test.ts                 |   20 +
 frontend/tailwind.config.js                        |   53 +-
 26 files changed, 4587 insertions(+), 125 deletions(-)

## Diff (plan-scoped files)
```diff
diff --git a/backend/apps/drama/services/artifact_normalize.py b/backend/apps/drama/services/artifact_normalize.py
new file mode 100644
index 0000000..ea213bf
--- /dev/null
+++ b/backend/apps/drama/services/artifact_normalize.py
@@ -0,0 +1,1400 @@
+# -*- coding: utf-8 -*-
+"""灏?LLM 鏉炬暎杈撳嚭瀵归綈鍒颁骇鐗?schema锛堢粨鏋勫瓧娈电敱 settings/鍚堟垚鍣ㄨˉ鍏級銆?+
+鍏煎鍏滃簳灞傦紝闈炲瓧娈靛悕 SSOT銆傚瓧娈靛绾︿互 JSON Schema 涓?schema_prompt_contract 涓哄噯锛?+鏈ā鍧椾粎澶勭悊鍒悕鏄犲皠涓庣己鐪佽ˉ鍏紝绂佹鍦ㄦ鏂板绗簩浠藉瓧娈佃〃銆?+"""
+from __future__ import annotations
+
+from typing import Any
+
+from apps.drama.services.matrix_synthesis import synthesize_rule_params
+from apps.drama.services.skills_loader import get_skills_loader
+
+_PROJECT_BRIEF_KEYS = frozenset(
+    {
+        "title",
+        "genre_matrix",
+        "theme_code",
+        "matrix_key",
+        "rule_params",
+        "preset_theme_code",
+        "episode_count",
+        "episode_duration",
+        "core_idea",
+        "target_audience",
+        "core_conflict",
+        "hook_concept",
+        "commercial_hook",
+        "reference_works",
+        "compliance_risk",
+        "market_opportunity",
+        "blockbuster_factors",
+        "competitor_references",
+        "differentiation_strategy",
+        "first_episode_hook",
+        "paywall_direction",
+    }
+)
+
+_RISK_RANK = {"low": 0, "medium": 1, "high": 2}
+
+
+def normalize_artifact(
+    artifact_key: str,
+    payload: dict[str, Any],
+    settings: dict[str, Any],
+) -> dict[str, Any]:
+    """鎸変骇鐗╃被鍨嬪仛濂戠害瀵归綈锛涙湭鐭ョ被鍨嬪師鏍疯繑鍥炪€?""
+    if artifact_key == "project_brief":
+        return normalize_project_brief(payload, settings)
+    if artifact_key == "story_bible":
+        return normalize_story_bible(payload, settings)
+    if artifact_key == "narrative_plan":
+        return normalize_narrative_plan(payload, settings)
+    if artifact_key == "quality_report":
+        return normalize_quality_report(payload, settings)
+    if artifact_key == "compliance_report":
+        return normalize_compliance_report(payload, settings)
+    return payload
+
+
+def normalize_narrative_plan(
+    raw: dict[str, Any],
+    settings: dict[str, Any] | None = None,
+) -> dict[str, Any]:
+    """瀵归綈 narrative_plan锛氳ˉ鍏ㄥ垎闆嗗繀濉瓧娈典笌鍒悕锛岃鎺?schema 澶栭敭銆?""
+    settings = settings or {}
+    designs_raw = raw.get("episode_narrative_designs")
+    if not isinstance(designs_raw, list):
+        # 鍏煎妯″瀷鐩存帴杩斿洖鏁扮粍
+        designs_raw = raw.get("episodes") if isinstance(raw.get("episodes"), list) else []
+
+    designs: list[dict[str, Any]] = []
+    for idx, item in enumerate(designs_raw):
+        if not isinstance(item, dict):
+            continue
+        designs.append(_normalize_episode_design(item, idx=idx, settings=settings))
+
+    if not designs:
+        designs.append(
+            _normalize_episode_design(
+                {
+                    "episode": 1,
+                    "title": "绗?闆?,
+                    "core_event": "寰呰ˉ鍏呮湰闆嗘牳蹇冧簨浠?,
+                },
+                idx=0,
+                settings=settings,
+            )
+        )
+
+    return {"episode_narrative_designs": designs}
+
+
+def _normalize_episode_design(
+    item: dict[str, Any],
+    *,
+    idx: int,
+    settings: dict[str, Any],
+) -> dict[str, Any]:
+    episode_no = item.get("episode")
+    if not isinstance(episode_no, int) or episode_no < 1:
+        try:
+            episode_no = int(episode_no)
+        except (TypeError, ValueError):
+            episode_no = idx + 1
+        if episode_no < 1:
+            episode_no = idx + 1
+
+    core_event = (
+        _as_nonempty_str(item.get("core_event"))
+        or _as_nonempty_str(item.get("event"))
+        or _as_nonempty_str(item.get("summary"))
+        or "寰呰ˉ鍏呮湰闆嗘牳蹇冧簨浠?
+    )
+    title = (
+        _as_nonempty_str(item.get("title"))
+        or _as_nonempty_str(item.get("episode_title"))
+        or f"绗瑊episode_no}闆?
+    )
+    opening_hook = (
+        _as_nonempty_str(item.get("opening_hook"))
+        or _as_nonempty_str(item.get("open_hook"))
+        or _as_nonempty_str(item.get("opening"))
+        or _as_nonempty_str(item.get("cold_open"))
+        or _as_nonempty_str(item.get("start_hook"))
+        or _as_nonempty_str(item.get("hook_open"))
+        or f"寮€鍦哄垏鍏ワ細{core_event}"
+    )
+    ending_hook = (
+        _as_nonempty_str(item.get("ending_hook"))
+        or _as_nonempty_str(item.get("end_hook"))
+        or _as_nonempty_str(item.get("ending"))
+        or _as_nonempty_str(item.get("cliffhanger"))
+        or _as_nonempty_str(item.get("hook_end"))
+        or _as_nonempty_str(item.get("closing_hook"))
+        or _pick_string_hook(item.get("hook"))
+        or f"闆嗘湯鎮康锛歿core_event}"
+    )
+
+    intensity = item.get("emotion_intensity")
+    try:
+        intensity_int = int(intensity)
+    except (TypeError, ValueError):
+        intensity_int = 6
+    intensity_int = max(1, min(10, intensity_int))
+
+    hook_grade = str(item.get("hook_grade") or "B").strip().upper()
+    if hook_grade not in {"S", "A", "B", "C"}:
+        hook_grade = "B"
+
+    foreshadowing = _normalize_foreshadowing(item.get("foreshadowing"))
+    emotion_nodes = _normalize_emotion_nodes(item.get("emotion_nodes"), core_event)
+
+    return {
+        "episode": episode_no,
+        "title": title,
+        "core_event": core_event,
+        "goal_conflict": (
+            _as_nonempty_str(item.get("goal_conflict"))
+            or _as_nonempty_str(item.get("conflict"))
+            or "寰呰ˉ鍏呯洰鏍囦笌鍐茬獊"
+        ),
+        "emotion_intensity": intensity_int,
+        "opening_hook": opening_hook,
+        "ending_hook": ending_hook,
+        "satisfaction_points": _as_str_list(
+            item.get("satisfaction_points"),
+            fallback=["寰呰ˉ鍏呯埥鐐?],
+        ),
+        "reversal": (
+            _as_nonempty_str(item.get("reversal"))
+            or _as_nonempty_str(item.get("twist"))
+            or "寰呰ˉ鍏呭弽杞?
+        ),
+        "paywall_hook": (
+            _as_nonempty_str(item.get("paywall_hook"))
+            or _as_nonempty_str(item.get("paywall"))
+            or ending_hook
+        ),
+        "rhythm_tag": (
+            _as_nonempty_str(item.get("rhythm_tag"))
+            or _as_nonempty_str(item.get("rhythm"))
+            or "standard"
+        ),
+        "foreshadowing": foreshadowing,
+        "hook_grade": hook_grade,
+        "characters": _as_str_list(
+            item.get("characters"),
+            fallback=[_as_nonempty_str(settings.get("title")) or "涓昏"],
+        ),
+        "emotion_nodes": emotion_nodes,
+    }
+
+
+def _pick_string_hook(value: Any) -> str | None:
+    if isinstance(value, str):
+        return _as_nonempty_str(value)
+    if isinstance(value, dict):
+        return (
+            _as_nonempty_str(value.get("ending"))
+            or _as_nonempty_str(value.get("end"))
+            or _as_nonempty_str(value.get("text"))
+            or _as_nonempty_str(value.get("content"))
+        )
+    return None
+
+
+def _normalize_foreshadowing(value: Any) -> dict[str, list[str]]:
+    if isinstance(value, dict):
+        setup = _as_str_list(value.get("setup"), fallback=[])
+        payoff = _as_str_list(value.get("payoff"), fallback=[])
+        return {"setup": setup, "payoff": payoff}
+    if isinstance(value, list):
+        return {"setup": _as_str_list(value, fallback=[]), "payoff": []}
+    text = _as_nonempty_str(value)
+    if text:
+        return {"setup": [text], "payoff": []}
+    return {"setup": [], "payoff": []}
+
+
+def _normalize_emotion_nodes(value: Any, core_event: str) -> dict[str, Any]:
+    src = value if isinstance(value, dict) else {}
+    ev = src.get("EV") if isinstance(src.get("EV"), dict) else {"value": 5}
+    et = src.get("ET") if isinstance(src.get("ET"), dict) else {"value": 5}
+    tp = src.get("TP") if isinstance(src.get("TP"), dict) else {"content": core_event}
+    if not tp:
+        tp = {"content": core_event}
+    return {"EV": ev, "ET": et, "TP": tp}
+
+
+def normalize_story_bible(
+    raw: dict[str, Any],
+    settings: dict[str, Any],
+) -> dict[str, Any]:
+    """瀵归綈 story_bible锛氳ˉ鍏?synopsis.short/full锛岃鎺?schema 澶栧瓧娈点€?""
+    title = (
+        _as_nonempty_str(raw.get("drama_title"))
+        or _as_nonempty_str(raw.get("title"))
+        or _as_nonempty_str(settings.get("title"))
+        or "鏈懡鍚嶇煭鍓?
+    )
+    logline = (
+        _as_nonempty_str(raw.get("logline"))
+        or _as_nonempty_str(settings.get("core_idea"))
+        or "寰呰ˉ鍏呬竴鍙ヨ瘽鏁呬簨"
+    )
+
+    out: dict[str, Any] = {
+        "drama_title": title,
+        "logline": logline,
+        "synopsis": _normalize_synopsis(raw, logline),
+        "adapt_source": _normalize_adapt_source(raw, settings),
+        "world_rules": _normalize_world_rules(raw.get("world_rules")),
+        "characters": _normalize_characters(raw.get("characters")),
+        "relationship_map": _as_object_list(raw.get("relationship_map")),
+        "series_structure": _normalize_series_structure(raw.get("series_structure")),
+    }
+    return out
+
+
+def _normalize_synopsis(raw: dict[str, Any], logline: str) -> dict[str, str]:
+    syn = raw.get("synopsis")
+    if isinstance(syn, str):
+        text = syn.strip() or logline
+        return {"short": _clip_text(text, 300), "full": text}
+    if isinstance(syn, dict):
+        short = (
+            _as_nonempty_str(syn.get("short"))
+            or _as_nonempty_str(syn.get("summary"))
+            or _as_nonempty_str(syn.get("brief"))
+            or _as_nonempty_str(syn.get("one_liner"))
+        )
+        full = (
+            _as_nonempty_str(syn.get("full"))
+            or _as_nonempty_str(syn.get("long"))
+            or _as_nonempty_str(syn.get("complete"))
+            or _as_nonempty_str(syn.get("text"))
+        )
+        if not short and full:
+            short = _clip_text(full, 300)
+        if not full and short:
+            full = short
+        if not short:
+            short = logline
+        if not full:
+            full = logline
+        return {"short": short, "full": full}
+    return {"short": logline, "full": logline}
+
+
+def _normalize_adapt_source(
+    raw: dict[str, Any],
+    settings: dict[str, Any],
+) -> dict[str, Any]:
+    src = raw.get("adapt_source") if isinstance(raw.get("adapt_source"), dict) else {}
+    entry = str(settings.get("entry_type") or "original_track")
+    default_mode = "adapt" if entry == "story_adapt" else "original"
+    mode = src.get("mode") if src.get("mode") in ("original", "adapt") else default_mode
+    out: dict[str, Any] = {"mode": mode}
+    for key in ("retained", "enhanced", "rewritten"):
+        value = src.get(key)
+        if isinstance(value, list):
+            out[key] = [str(item) for item in value if item is not None]
+    check = _as_nonempty_str(src.get("originality_check"))
+    if check:
+        out["originality_check"] = check
+    return out
+
+
+def _normalize_world_rules(value: Any) -> dict[str, Any]:
+    src = value if isinstance(value, dict) else {}
+    root_rules = _normalize_root_rules(src.get("root_rules"))
+    return {
+        "setting_summary": (
+            _as_nonempty_str(src.get("setting_summary")) or "寰呰ˉ鍏呮椂绌鸿儗鏅?
+        ),
+        "root_rules": root_rules or ["寰呰ˉ鍏呬笘鐣屾牴瑙勫垯"],
+        "power_structure": _normalize_power_structure(src.get("power_structure")),
+    }
+
+
+def _normalize_root_rules(value: Any) -> list[str]:
+    """root_rules schema 涓?string[]锛涘吋瀹?LLM 杈撳嚭鐨勮鍒欏璞°€?""
+    if isinstance(value, list):
+        result: list[str] = []
+        for item in value:
+            text = _format_root_rule_item(item)
+            if text:
+                result.append(text)
+        return result
+    text = _as_nonempty_str(value)
+    return [text] if text else []
+
+
+def _format_root_rule_item(item: Any) -> str | None:
+    if isinstance(item, dict):
+        rule = _as_nonempty_str(item.get("rule")) or _as_nonempty_str(item.get("name"))
+        if not rule:
+            return None
+        parts = [rule]
+        trigger = _as_nonempty_str(item.get("trigger"))
+        cost = _as_nonempty_str(item.get("violation_cost"))
+        applicable = _as_nonempty_str(item.get("applicable_to"))
+        visible = _as_nonempty_str(item.get("visible_manifestation"))
+        if trigger:
+            parts.append(f"瑙﹀彂锛歿trigger}")
+        if applicable:
+            parts.append(f"閫傜敤锛歿applicable}")
+        if cost:
+            parts.append(f"浠ｄ环锛歿cost}")
+        if visible:
+            parts.append(f"澶栨樉锛歿visible}")
+        return "锝?.join(parts)
+    return _as_nonempty_str(item)
+
+
+def _normalize_power_structure(value: Any) -> str:
+    """power_structure schema 涓?string锛涘吋瀹?description + key_actors 瀵硅薄銆?""
+    if isinstance(value, dict):
+        chunks: list[str] = []
+        desc = _as_nonempty_str(value.get("description")) or _as_nonempty_str(
+            value.get("summary")
+        )
+        if desc:
+            chunks.append(desc)
+        actors = value.get("key_actors")
+        if isinstance(actors, list) and actors:
+            actor_lines: list[str] = []
+            for actor in actors:
+                if not isinstance(actor, dict):
+                    text = _as_nonempty_str(actor)
+                    if text:
+                        actor_lines.append(text)
+                    continue
+                name = _as_nonempty_str(actor.get("name")) or "鏈懡鍚?
+                position = _as_nonempty_str(actor.get("position"))
+                resources = _as_nonempty_str(actor.get("resources"))
+                motivation = _as_nonempty_str(actor.get("motivation"))
+                detail = name
+                extras = [
+                    part
+                    for part in (position, resources and f"璧勬簮锛歿resources}", motivation and f"鍔ㄦ満锛歿motivation}")
+                    if part
+                ]
+                if extras:
+                    detail = f"{name}锛坽'锛?.join(extras)}锛?
+                actor_lines.append(detail)
+            if actor_lines:
+                chunks.append("鍏抽敭浜虹墿锛? + "锛?.join(actor_lines))
+        if chunks:
+            return "\n".join(chunks)
+        return "寰呰ˉ鍏呮潈鍔涚粨鏋?
+    return _as_nonempty_str(value) or "寰呰ˉ鍏呮潈鍔涚粨鏋?
+
+
+_ROLE_TYPE_ALIASES = {
+    "protagonist": "protagonist",
+    "hero": "protagonist",
+    "main": "protagonist",
+    "lead": "protagonist",
+    "涓昏": "protagonist",
+    "antagonist": "antagonist",
+    "villain": "antagonist",
+    "鍙嶆淳": "antagonist",
+    "supporting": "supporting",
+    "support": "supporting",
+    "閰嶈": "supporting",
+}
+
+
+def _normalize_characters(value: Any) -> list[dict[str, Any]]:
+    if not isinstance(value, list) or not value:
+        return [
+            {
+                "name": "涓昏",
+                "role_type": "protagonist",
+                "surface_desire": "寰呰ˉ鍏?,
+                "deep_need": "寰呰ˉ鍏?,
+                "ghost": "寰呰ˉ鍏?,
+                "lie": "寰呰ˉ鍏?,
+                "flaw": "寰呰ˉ鍏?,
+                "arc": {
+                    "start": "寰呰ˉ鍏?,
+                    "turning_point_1": "寰呰ˉ鍏?,
+                    "turning_point_2": "寰呰ˉ鍏?,
+                    "end": "寰呰ˉ鍏?,
+                },
+                "voice_tag": "寰呰ˉ鍏?,
+                "visual_anchor": "寰呰ˉ鍏?,
+            }
+        ]
+    result: list[dict[str, Any]] = []
+    for item in value:
+        if not isinstance(item, dict):
+            continue
+        role_raw = str(item.get("role_type") or "supporting").strip().lower()
+        role_type = _ROLE_TYPE_ALIASES.get(role_raw, "supporting")
+        arc_src = item.get("arc") if isinstance(item.get("arc"), dict) else {}
+        char: dict[str, Any] = {
+            "name": _as_nonempty_str(item.get("name")) or "鏈懡鍚嶈鑹?,
+            "role_type": role_type,
+            "surface_desire": (
+                _as_nonempty_str(item.get("surface_desire"))
+                or _as_nonempty_str(item.get("want"))
+                or _as_nonempty_str(item.get("desire"))
+                or "寰呰ˉ鍏?
+            ),
+            "deep_need": (
+                _as_nonempty_str(item.get("deep_need"))
+                or _as_nonempty_str(item.get("need"))
+                or "寰呰ˉ鍏?
+            ),
+            "ghost": (
+                _as_nonempty_str(item.get("ghost"))
+                or _as_nonempty_str(item.get("wound"))
+                or "寰呰ˉ鍏?
+            ),
+            "lie": _as_nonempty_str(item.get("lie")) or "寰呰ˉ鍏?,
+            "flaw": _as_nonempty_str(item.get("flaw")) or "寰呰ˉ鍏?,
+            "arc": {
+                "start": (
+                    _as_nonempty_str(arc_src.get("start"))
+                    or _as_nonempty_str(arc_src.get("initial"))
+                    or _as_nonempty_str(arc_src.get("beginning"))
+                    or "寰呰ˉ鍏?
+                ),
+                "turning_point_1": (
+                    _as_nonempty_str(arc_src.get("turning_point_1"))
+                    or _as_nonempty_str(arc_src.get("midpoint"))
+                    or _as_nonempty_str(arc_src.get("mid1"))
+                    or "寰呰ˉ鍏?
+                ),
+                "turning_point_2": (
+                    _as_nonempty_str(arc_src.get("turning_point_2"))
+                    or _as_nonempty_str(arc_src.get("low_point"))
+                    or _as_nonempty_str(arc_src.get("mid2"))
+                    or "寰呰ˉ鍏?
+                ),
+                "end": (
+                    _as_nonempty_str(arc_src.get("end"))
+                    or _as_nonempty_str(arc_src.get("final"))
+                    or _as_nonempty_str(arc_src.get("ending"))
+                    or "寰呰ˉ鍏?
+                ),
+            },
+            "voice_tag": _as_nonempty_str(item.get("voice_tag")) or "寰呰ˉ鍏?,
+            "visual_anchor": (
+                _as_nonempty_str(item.get("visual_anchor")) or "寰呰ˉ鍏?
+            ),
+        }
+        ident = (
+            _as_nonempty_str(item.get("audience_identification"))
+            or _as_nonempty_str(item.get("background"))
+        )
+        if ident:
+            char["audience_identification"] = ident
+        result.append(char)
+    return result or _normalize_characters([])
+
+
+def _normalize_series_structure(value: Any) -> dict[str, Any]:
+    src = value if isinstance(value, dict) else {}
+    stages = src.get("six_stage_structure")
+    if not isinstance(stages, list):
+        stages = []
+    # 涓嶈冻 6 娈垫椂鐢ㄥ崰浣嶈ˉ榻愶紝閬垮厤 schema minItems 澶辫触
+    while len(stages) < 6:
+        idx = len(stages) + 1
+        stages.append({"stage": idx, "name": f"闃舵{idx}", "summary": "寰呰ˉ鍏?})
+    stages = stages[:6]
+    normalized_stages: list[dict[str, Any]] = []
+    for item in stages:
+        if isinstance(item, dict):
+            normalized_stages.append(item)
+        else:
+            normalized_stages.append({"summary": str(item)})
+
+    return {
+        "main_storyline": (
+            _as_nonempty_str(src.get("main_storyline")) or "寰呰ˉ鍏呬富绾?
+        ),
+        "six_stage_structure": normalized_stages,
+        "conflict_escalation_chain": _normalize_conflict_chain(
+            src.get("conflict_escalation_chain")
+        ),
+        "major_reversal_positions": _as_object_list(
+            src.get("major_reversal_positions")
+        ),
+        "paywall_distribution": _as_object_list(src.get("paywall_distribution")),
+        "foreshadowing_table": _as_object_list(src.get("foreshadowing_table")),
+        "series_emotion_curve": _normalize_emotion_curve(
+            src.get("series_emotion_curve")
+        ),
+    }
+
+
+def _normalize_conflict_chain(value: Any) -> list[str]:
+    """conflict_escalation_chain schema 涓?string[]锛涘吋瀹归樁娈靛璞′笌宸插瓧绗︿覆鍖栫殑 dict銆?""
+    if isinstance(value, list):
+        result: list[str] = []
+        for item in value:
+            text = _format_conflict_item(item)
+            if text:
+                result.append(text)
+        if result:
+            return result
+    if isinstance(value, dict):
+        text = _format_conflict_item(value)
+        return [text] if text else ["寰呰ˉ鍏呭啿绐佸崌绾ч摼"]
+    return _as_str_list(value, fallback=["寰呰ˉ鍏呭啿绐佸崌绾ч摼"])
+
+
+def _format_conflict_item(item: Any) -> str | None:
+    parsed = item
+    if isinstance(item, str):
+        text = item.strip()
+        if not text:
+            return None
+        # 鍏煎鍘嗗彶钀藉簱锛歴tr(dict) / JSON 瀛楃涓?+        coerced = _coerce_mapping(text)
+        if coerced is None:
+            return text
+        parsed = coerced
+    if not isinstance(parsed, dict):
+        return _as_nonempty_str(parsed)
+
+    stage = parsed.get("stage")
+    conflict_type = _as_nonempty_str(parsed.get("conflict_type")) or _as_nonempty_str(
+        parsed.get("type")
+    )
+    description = _as_nonempty_str(parsed.get("description")) or _as_nonempty_str(
+        parsed.get("summary")
+    )
+    head = f"绗瑊stage}骞? if stage is not None and str(stage).strip() else None
+    label = " 路 ".join(part for part in (head, conflict_type) if part)
+    if label and description:
+        return f"{label}锛歿description}"
+    if description:
+        return description
+    if label:
+        return label
+    return None
+
+
+def _coerce_mapping(text: str) -> dict[str, Any] | None:
+    """鎶?JSON / Python dict 瀛楃涓插敖閲忚繕鍘熶负 dict銆?""
+    import ast
+    import json
+
+    cleaned = text.strip()
+    if not (cleaned.startswith("{") and cleaned.endswith("}")):
+        return None
+    try:
+        loaded = json.loads(cleaned)
+        return loaded if isinstance(loaded, dict) else None
+    except (TypeError, ValueError, json.JSONDecodeError):
+        pass
+    try:
+        loaded = ast.literal_eval(cleaned)
+        return loaded if isinstance(loaded, dict) else None
+    except (SyntaxError, ValueError):
+        return None
+
+
+def _normalize_emotion_curve(value: Any) -> list[dict[str, Any]]:
+    """series_emotion_curve schema 涓?object[]锛涘吋瀹?{description,key_points}銆?""
+    if isinstance(value, list):
+        return [item for item in value if isinstance(item, dict)]
+    if isinstance(value, dict):
+        points = value.get("key_points")
+        if isinstance(points, list):
+            result = [item for item in points if isinstance(item, dict)]
+            if result:
+                desc = _as_nonempty_str(value.get("description"))
+                if desc and not any(
+                    _as_nonempty_str(item.get("description")) == desc for item in result
+                ):
+                    # 淇濈暀鏇茬嚎鎬昏堪锛屾寕鍒伴鐐癸紝閬垮厤淇℃伅涓㈠け
+                    first = dict(result[0])
+                    if not _as_nonempty_str(first.get("curve_summary")):
+                        first["curve_summary"] = desc
+                    result[0] = first
+                return result
+        # 鏁存瀵硅薄褰撲綔鍗曠偣淇濈暀鍙瀛楁
+        if any(
+            key in value
+            for key in ("episode", "emotion", "event", "description", "summary")
+        ):
+            return [value]
+    return []
+
+
+def _as_str_list(value: Any, fallback: list[str] | None = None) -> list[str]:
+    if isinstance(value, list):
+        items: list[str] = []
+        for item in value:
+            if isinstance(item, dict):
+                text = (
+                    _format_conflict_item(item)
+                    or _as_nonempty_str(item.get("description"))
+                    or _as_nonempty_str(item.get("summary"))
+                    or _as_nonempty_str(item.get("name"))
+                )
+                if text:
+                    items.append(text)
+                continue
+            if isinstance(item, str):
+                coerced = _coerce_mapping(item)
+                if coerced is not None:
+                    text = _format_conflict_item(coerced)
+                    if text:
+                        items.append(text)
+                        continue
+            text = _as_nonempty_str(item)
+            if text:
+                items.append(text)
+        if items:
+            return items
+    if isinstance(value, str) and value.strip():
+        return [value.strip()]
+    return list(fallback or [])
+
+
+def _as_object_list(value: Any) -> list[dict[str, Any]]:
+    if not isinstance(value, list):
+        return []
+    return [item for item in value if isinstance(item, dict)]
+
+
+def _clip_text(text: str, max_len: int) -> str:
+    cleaned = text.strip()
+    if len(cleaned) <= max_len:
+        return cleaned
+    return f"{cleaned[: max_len - 1]}鈥?
+
+
+def normalize_project_brief(
+    raw: dict[str, Any],
+    settings: dict[str, Any],
+) -> dict[str, Any]:
+    """琛ュ叏鐭╅樀缁撴瀯瀛楁锛屽苟瑁佹帀 schema 涓嶅厑璁哥殑棰濆閿€?""
+    settings_matrix = dict(settings.get("genre_matrix") or {})
+    raw_matrix = raw.get("genre_matrix") if isinstance(raw.get("genre_matrix"), dict) else {}
+
+    genre_matrix: dict[str, Any] = {
+        "emotion": raw_matrix.get("emotion") or settings_matrix.get("emotion"),
+        "identity": raw_matrix.get("identity") or settings_matrix.get("identity"),
+        "conflict": raw_matrix.get("conflict") or settings_matrix.get("conflict"),
+        "world": raw_matrix.get("world") or settings_matrix.get("world"),
+        "audience_channel": (
+            raw_matrix.get("audience_channel")
+            or raw.get("audience_channel")
+            or settings.get("audience_channel")
+            or "general"
+        ),
+    }
+    structure = (
+        raw_matrix.get("protagonist_structure")
+        or raw.get("protagonist_structure")
+        or settings.get("protagonist_structure")
+    )
+    if structure:
+        genre_matrix["protagonist_structure"] = structure
+    tags: list[Any]
+    if "flavor_tags" in raw_matrix:
+        tags = list(raw_matrix.get("flavor_tags") or [])
+    elif "flavor_tags" in raw:
+        tags = list(raw.get("flavor_tags") or [])
+    else:
+        tags = list(settings.get("flavor_tags") or [])
+    if isinstance(tags, str):
+        tags = [tags]
+    if tags:
+        genre_matrix["flavor_tags"] = list(tags)[:5]
+    elif "flavor_tags" in raw_matrix or "flavor_tags" in raw:
+        genre_matrix["flavor_tags"] = []
+
+    synthesized = synthesize_rule_params(genre_matrix)
+    # rule_params 鐢遍鏉愮煩闃靛悎鎴愶紱妯″瀷甯歌緭鍑?high/瀵硅薄缁撴瀯绛夐潪娉曞€硷紝涓€寰嬩笉閲囦俊
+    rule_params = {
+        "reversal_density": synthesized["reversal_density"],
+        "emotion_curve": synthesized["emotion_curve"],
+        "act_ratio": synthesized["act_ratio"],
+        "hook_types": synthesized["hook_types"],
+    }
+
+    derived = settings.get("derived") if isinstance(settings.get("derived"), dict) else {}
+    matrix_key = (
+        raw.get("matrix_key")
+        or derived.get("matrix_key")
+        or synthesized.get("matrix_key")
+    )
+
+    core_idea = (
+        _as_nonempty_str(raw.get("core_idea"))
+        or _as_nonempty_str(settings.get("core_idea"))
+        or _as_nonempty_str(raw.get("synopsis"))
+        or _as_nonempty_str(raw.get("one_line_theme"))
+        or "寰呰ˉ鍏呮牳蹇冨垱鎰?
+    )
+
+    out: dict[str, Any] = {
+        "title": (
+            _as_nonempty_str(raw.get("title"))
+            or _as_nonempty_str(settings.get("title"))
+            or "鏈懡鍚嶇煭鍓?
+        ),
+        "genre_matrix": genre_matrix,
+        "theme_code": "matrix",
+        "matrix_key": matrix_key,
+        "rule_params": rule_params,
+        "preset_theme_code": settings.get("preset_theme_code"),
+        "episode_count": int(
+            raw.get("episode_count") or settings.get("episode_count") or 1
+        ),
+        "episode_duration": raw.get("episode_duration"),
+        "core_idea": core_idea,
+        "target_audience": (
+            _as_nonempty_str(raw.get("target_audience")) or "寰呰ˉ鍏呯洰鏍囧彈浼?
+        ),
+        "core_conflict": (
+            _as_nonempty_str(raw.get("core_conflict")) or "寰呰ˉ鍏呮牳蹇冨啿绐?
+        ),
+        "hook_concept": (
+            _as_nonempty_str(raw.get("hook_concept"))
+            or _as_nonempty_str(raw.get("one_line_theme"))
+            or "寰呰ˉ鍏呴挬瀛愭蹇?
+        ),
+        "compliance_risk": _resolve_compliance_risk(raw),
+    }
+
+    commercial = _as_nonempty_str(raw.get("commercial_hook")) or _as_nonempty_str(
+        raw.get("one_line_theme")
+    )
+    if commercial:
+        out["commercial_hook"] = commercial
+
+    refs = raw.get("reference_works")
+    if isinstance(refs, list):
+        out["reference_works"] = [str(item) for item in refs if item is not None]
+
+    market = _as_nonempty_str(raw.get("market_opportunity"))
+    if market:
+        out["market_opportunity"] = market
+
+    factors = _normalize_blockbuster_factors(raw.get("blockbuster_factors"))
+    if factors is not None:
+        out["blockbuster_factors"] = factors
+
+    competitors = raw.get("competitor_references")
+    if isinstance(competitors, list):
+        out["competitor_references"] = [
+            item for item in competitors if isinstance(item, dict)
+        ]
+
+    for key in (
+        "differentiation_strategy",
+        "first_episode_hook",
+        "paywall_direction",
+    ):
+        value = _as_nonempty_str(raw.get(key))
+        if value:
+            out[key] = value
+
+    return {key: value for key, value in out.items() if key in _PROJECT_BRIEF_KEYS}
+
+
+def _as_nonempty_str(value: Any) -> str | None:
+    if value is None:
+        return None
+    text = str(value).strip()
+    return text or None
+
+
+def _normalize_blockbuster_factors(value: Any) -> list[str] | None:
+    if not isinstance(value, list):
+        return None
+    result: list[str] = []
+    for item in value:
+        if isinstance(item, str) and item.strip():
+            result.append(item.strip())
+        elif isinstance(item, dict):
+            label = (
+                _as_nonempty_str(item.get("factor"))
+                or _as_nonempty_str(item.get("description"))
+                or _as_nonempty_str(item.get("name"))
+            )
+            if label:
+                result.append(label)
+    return result
+
+
+def _resolve_compliance_risk(raw: dict[str, Any]) -> str:
+    direct = raw.get("compliance_risk")
+    if direct in _RISK_RANK:
+        return str(direct)
+    best = "low"
+    for item in raw.get("sensitivity_pre_check") or []:
+        if not isinstance(item, dict):
+            continue
+        level = item.get("level")
+        if level in _RISK_RANK and _RISK_RANK[level] > _RISK_RANK[best]:
+            best = str(level)
+    return best
+
+
+_QUALITY_DIMENSION_KEYS = (
+    "format",
+    "narrative",
+    "conflict",
+    "character",
+    "emotion",
+    "logic",
+    "satisfaction",
+    "hooks",
+    "paywall",
+    "genre_fit",
+)
+
+_QUALITY_DIMENSION_NAME_ALIASES: dict[str, str] = {
+    "鏍煎紡瑙勮寖": "format",
+    "鏍煎紡": "format",
+    "format": "format",
+    "鍙欎簨鏁堢巼": "narrative",
+    "鍙欎簨": "narrative",
+    "narrative": "narrative",
+    "鍐茬獊澶勭悊": "conflict",
+    "鍐茬獊": "conflict",
+    "conflict": "conflict",
+    "瑙掕壊涓€鑷存€?: "character",
+    "瑙掕壊": "character",
+    "character": "character",
+    "鎯呮劅娣卞害": "emotion",
+    "鎯呮劅": "emotion",
+    "emotion": "emotion",
+    "閫昏緫涓€鑷存€?: "logic",
+    "閫昏緫": "logic",
+    "logic": "logic",
+    "鐖界偣瀵嗗害": "satisfaction",
+    "鐖界偣": "satisfaction",
+    "satisfaction": "satisfaction",
+    "閽╁瓙寮哄害": "hooks",
+    "閽╁瓙": "hooks",
+    "hooks": "hooks",
+    "浠樿垂鐐逛紭鍖?: "paywall",
+    "浠樿垂鐐?: "paywall",
+    "paywall": "paywall",
+    "璧涢亾鍖归厤": "genre_fit",
+    "璧涢亾": "genre_fit",
+    "genre_fit": "genre_fit",
+}
+
+
+def normalize_quality_report(
+    raw: dict[str, Any],
+    settings: dict[str, Any] | None = None,
+) -> dict[str, Any]:
+    """瀵归綈 quality_report锛歞imensions 鏁扮粍鈫掑璞★紝瀛楁鍒悕涓庣己鐪佽ˉ榻愩€?""
+    settings = settings or {}
+    title = (
+        _as_nonempty_str(raw.get("drama_title"))
+        or _as_nonempty_str(raw.get("title"))
+        or _as_nonempty_str(settings.get("title"))
+        or "鏈懡鍚嶇煭鍓?
+    )
+    overall = _as_number(raw.get("overall_score"), default=0.0)
+    scoring_preset = _resolve_scoring_preset(raw, settings)
+    dimension_weights = _load_quality_dimension_weights(scoring_preset)
+    dimensions = _normalize_quality_dimensions(
+        raw.get("dimensions"), overall, dimension_weights
+    )
+    overall = _rescale_overall_if_ten_point(overall, dimensions)
+    needs_revision = raw.get("needs_revision")
+    if not isinstance(needs_revision, bool):
+        needs_revision = overall < 75
+    can_continue = raw.get("can_continue_next_batch")
+    if not isinstance(can_continue, bool):
+        can_continue = not needs_revision
+    verdict = _normalize_quality_verdict(raw.get("verdict"), overall, needs_revision)
+    verdict, needs_revision, can_continue = _reconcile_quality_verdict(
+        verdict, overall, needs_revision, can_continue
+    )
+    grade = _as_nonempty_str(raw.get("grade"))
+    if grade not in {"S", "A", "B", "C", "D"}:
+        grade = _grade_from_score(overall)
+
+    resolved = _as_nonempty_str(raw.get("resolved_script_key")) or "external_script"
+    if resolved not in {"polished_script", "episode_scripts", "external_script"}:
+        resolved = "external_script"
+
+    continuity = raw.get("continuity_summary")
+    if not isinstance(continuity, dict):
+        continuity = {"result": "pass", "issues": []}
+    else:
+        result = _as_nonempty_str(continuity.get("result")) or "pass"
+        if result not in {"pass", "warning", "fail"}:
+            lower = result.lower()
+            if lower in {"pass", "passed", "ok"}:
+                result = "pass"
+            elif lower in {"warn", "warning"}:
+                result = "warning"
+            else:
+                result = "fail"
+        continuity = {
+            "result": result,
+            "issues": continuity.get("issues")
+            if isinstance(continuity.get("issues"), list)
+            else [],
+        }
+
+    out: dict[str, Any] = {
+        "drama_title": title,
+        "scored_artifact": "latest_script",
+        "resolved_script_key": resolved,
+        "scoring_preset": scoring_preset,
+        "pass_threshold": _as_number(raw.get("pass_threshold"), default=75.0),
+        "overall_score": overall,
+        "grade": grade,
+        "can_continue_next_batch": can_continue,
+        "needs_revision": needs_revision,
+        "dimensions": dimensions,
+        "defects": raw.get("defects") if isinstance(raw.get("defects"), list) else [],
+        "continuity_summary": continuity,
+        "revision_priorities": (
+            raw.get("revision_priorities")
+            if isinstance(raw.get("revision_priorities"), list)
+            else []
+        ),
+        "verdict": verdict,
+    }
+    if raw.get("config_revision") is not None:
+        out["config_revision"] = str(raw.get("config_revision"))
+    if "evolution_proposal" in raw:
+        out["evolution_proposal"] = raw.get("evolution_proposal")
+    return out
+
+
+def _normalize_quality_verdict(value: Any, overall: float, needs_revision: bool) -> str:
+    allowed = {"閫氳繃", "鏉′欢閫氳繃", "闇€瑕佷慨鏀?, "閲嶅ぇ杩斿伐"}
+    text = _as_nonempty_str(value)
+    if text in allowed:
+        return text
+    aliases = {
+        "pass": "閫氳繃",
+        "passed": "閫氳繃",
+        "ok": "閫氳繃",
+        "鏉′欢閫氳繃": "鏉′欢閫氳繃",
+        "闇€瑕佷慨鏀?: "闇€瑕佷慨鏀?,
+        "寤鸿淇": "闇€瑕佷慨鏀?,
+        "淇": "闇€瑕佷慨鏀?,
+        "閲嶅ぇ杩斿伐": "閲嶅ぇ杩斿伐",
+        "fail": "閲嶅ぇ杩斿伐",
+        "failed": "閲嶅ぇ杩斿伐",
+    }
+    if text:
+        mapped = aliases.get(text) or aliases.get(text.lower())
+        if mapped in allowed:
+            return mapped
+    if overall < 40:
+        return "閲嶅ぇ杩斿伐"
+    if needs_revision or overall < 75:
+        return "闇€瑕佷慨鏀?
+    if overall < 80:
+        return "鏉′欢閫氳繃"
+    return "閫氳繃"
+
+
+def normalize_compliance_report(
+    raw: dict[str, Any],
+    settings: dict[str, Any] | None = None,
+) -> dict[str, Any]:
+    """瀵归綈 compliance_report锛氭灇涓句笌缂虹渷瀛楁琛ラ綈銆?""
+    settings = settings or {}
+    title = (
+        _as_nonempty_str(raw.get("drama_title"))
+        or _as_nonempty_str(raw.get("title"))
+        or _as_nonempty_str(settings.get("title"))
+        or "鏈懡鍚嶇煭鍓?
+    )
+    check_mode = _as_nonempty_str(raw.get("check_mode")) or "standard"
+    if check_mode not in {"standard", "values-risk", "full"}:
+        check_mode = "standard"
+    platform = _as_nonempty_str(raw.get("target_platform")) or "generic"
+    if platform not in {"generic", "douyin", "kuaishou", "wechat_miniprogram"}:
+        platform = "generic"
+    resolved = _as_nonempty_str(raw.get("resolved_script_key")) or "external_script"
+    if resolved not in {"polished_script", "episode_scripts", "external_script"}:
+        resolved = "external_script"
+
+    overall = _as_nonempty_str(raw.get("overall_result"))
+    if overall not in {"閫氳繃", "椋庨櫓", "涓嶉€氳繃"}:
+        # 鍏煎鑻辨枃/鍚屼箟璇?+        lower = (overall or "").lower()
+        if lower in {"pass", "passed", "ok", "safe"}:
+            overall = "閫氳繃"
+        elif lower in {"risk", "warning", "warn"}:
+            overall = "椋庨櫓"
+        elif lower in {"fail", "failed", "block", "blocked"}:
+            overall = "涓嶉€氳繃"
+        else:
+            blocking = raw.get("blocking_issues")
+            overall = "涓嶉€氳繃" if isinstance(blocking, list) and blocking else "閫氳繃"
+
+    risk_items = _normalize_compliance_risk_items(raw.get("risk_items"))
+    blocking = _normalize_blocking_issues(raw.get("blocking_issues"))
+
+    return {
+        "drama_title": title,
+        "check_mode": check_mode,
+        "target_platform": platform,
+        "platform_policy_version": raw.get("platform_policy_version"),
+        "platform_policy_verified_at": raw.get("platform_policy_verified_at"),
+        "checked_artifact": "latest_script",
+        "resolved_script_key": resolved,
+        "overall_result": overall,
+        "blocking_issues": blocking,
+        "risk_items": risk_items,
+    }
+
+
+def _resolve_scoring_preset(
+    raw: dict[str, Any],
+    settings: dict[str, Any],
+) -> str:
+    preset = _as_nonempty_str(raw.get("scoring_preset"))
+    if not preset:
+        prefs = settings.get("creation_preferences") or {}
+        preset = _as_nonempty_str(prefs.get("scoring_preset")) or "standard"
+    if preset not in {"standard", "strict", "relaxed", "rhythm_first"}:
+        return "standard"
+    return preset
+
+
+def _load_quality_dimension_weights(scoring_preset: str) -> dict[str, float]:
+    """浠?quality-scoring.yaml + scoring-presets.yaml 璇诲彇鍗佺淮鏉冮噸 SSOT銆?""
+    loader = get_skills_loader()
+    scoring = loader.load_seed_yaml("foundation/constraints/quality-scoring.yaml")
+    presets = loader.load_seed_yaml("foundation/constraints/scoring-presets.yaml")
+    preset_map = presets.get("presets") if isinstance(presets.get("presets"), dict) else {}
+    if scoring_preset not in preset_map:
+        scoring_preset = "standard"
+    preset = preset_map.get(scoring_preset) or {}
+    preset_weights = preset.get("weights") if isinstance(preset.get("weights"), dict) else {}
+
+    weights: dict[str, float] = {}
+    for dim in scoring.get("dimensions") or []:
+        if not isinstance(dim, dict):
+            continue
+        key = str(dim.get("key") or "")
+        if key not in _QUALITY_DIMENSION_KEYS:
+            continue
+        raw_weight = preset_weights.get(key, dim.get("weight"))
+        weights[key] = _as_number(raw_weight, default=0.0)
+
+    for key in _QUALITY_DIMENSION_KEYS:
+        weights.setdefault(key, 0.0)
+    return weights
+
+
+def _normalize_quality_dimensions(
+    value: Any,
+    overall: float,
+    dimension_weights: dict[str, float],
+) -> dict[str, Any]:
+    mapped: dict[str, Any] = {}
+    if isinstance(value, dict):
+        for key, item in value.items():
+            dim_key = _QUALITY_DIMENSION_NAME_ALIASES.get(str(key).strip(), str(key).strip())
+            if dim_key in _QUALITY_DIMENSION_KEYS:
+                mapped[dim_key] = _normalize_score_dimension(
+                    item, dim_key, overall, dimension_weights
+                )
+    elif isinstance(value, list):
+        for item in value:
+            if not isinstance(item, dict):
+                continue
+            name = (
+                _as_nonempty_str(item.get("key"))
+                or _as_nonempty_str(item.get("name"))
+                or _as_nonempty_str(item.get("dimension"))
+                or ""
+            )
+            dim_key = _QUALITY_DIMENSION_NAME_ALIASES.get(name, name)
+            if dim_key in _QUALITY_DIMENSION_KEYS:
+                mapped[dim_key] = _normalize_score_dimension(
+                    item, dim_key, overall, dimension_weights
+                )
+
+    for key in _QUALITY_DIMENSION_KEYS:
+        if key not in mapped:
+            mapped[key] = {
+                "score": overall,
+                "weight": dimension_weights[key],
+                "evidence": [],
+                "deductions": [],
+            }
+    return mapped
+
+
+def _normalize_score_dimension(
+    value: Any,
+    key: str,
+    overall: float,
+    dimension_weights: dict[str, float],
+) -> dict[str, Any]:
+    default_weight = dimension_weights.get(key, 0.0)
+    if isinstance(value, (int, float)) and not isinstance(value, bool):
+        return {
+            "score": float(value),
+            "weight": default_weight,
+            "evidence": [],
+            "deductions": [],
+        }
+    if not isinstance(value, dict):
+        return {
+            "score": overall,
+            "weight": default_weight,
+            "evidence": [],
+            "deductions": [],
+        }
+
+    evidence = _coerce_text_list(value.get("evidence"))
+    for alt_key in ("comment", "analysis", "summary", "reason", "notes"):
+        if evidence:
+            break
+        evidence = _coerce_text_list(value.get(alt_key))
+
+    deductions = _coerce_text_list(value.get("deductions"))
+    if not deductions:
+        deductions = _coerce_text_list(
+            value.get("deduction_reasons") or value.get("reasons")
+        )
+
+    weight = _as_number(value.get("weight"), default=default_weight)
+    if weight < 0 or weight > 1:
+        weight = default_weight
+
+    return {
+        "score": _as_number(value.get("score"), default=overall),
+        "weight": weight,
+        "evidence": evidence,
+        "deductions": deductions,
+    }
+
+
+def _coerce_text_list(value: Any) -> list[str]:
+    if isinstance(value, str):
+        text = value.strip()
+        return [text] if text else []
+    if not isinstance(value, list):
+        return []
+    result: list[str] = []
+    for item in value:
+        if item is None:
+            continue
+        if isinstance(item, str):
+            text = item.strip()
+            if text:
+                result.append(text)
+            continue
+        if isinstance(item, dict):
+            text = (
+                _as_nonempty_str(item.get("text"))
+                or _as_nonempty_str(item.get("quote"))
+                or _as_nonempty_str(item.get("description"))
+                or _as_nonempty_str(item.get("content"))
+                or ""
+            )
+            if text:
+                result.append(text)
+            continue
+        text = str(item).strip()
+        if text:
+            result.append(text)
+    return result
+
+
+def _rescale_overall_if_ten_point(
+    overall: float,
+    dimensions: dict[str, Any],
+) -> float:
+    """绾犳妯″瀷璇敤 1-10 鍒嗗埗锛氭€诲垎鎴栧悇缁村亸灏忓垯鏀惧ぇ鍒扮櫨鍒嗗埗銆?""
+    scores = [
+        float(dim.get("score"))
+        for dim in dimensions.values()
+        if isinstance(dim, dict) and isinstance(dim.get("score"), (int, float))
+    ]
+    if not scores:
+        return overall
+
+    def _scale_dims() -> None:
+        for dim in dimensions.values():
+            if isinstance(dim, dict) and isinstance(dim.get("score"), (int, float)):
+                raw = float(dim["score"])
+                if raw <= 10:
+                    dim["score"] = round(raw * 10, 1)
+
+    # 鎬诲垎涓庡悇缁撮兘鏄崄鍒嗗埗
+    if overall <= 10 and max(scores) <= 10:
+        _scale_dims()
+        return round(overall * 10, 1)
+    # 鎬诲垎宸叉槸鐧惧垎鍒讹紝浣嗗悇缁翠粛鍍忓崄鍒嗗埗锛堝 overall=78銆佺淮鍒?8/7/9锛?+    if overall > 10 and max(scores) <= 10 and len(scores) >= 5:
+        _scale_dims()
+        return overall
+    return overall
+
+
+def _reconcile_quality_verdict(
+    verdict: str,
+    overall: float,
+    needs_revision: bool,
+    can_continue: bool,
+) -> tuple[str, bool, bool]:
+    """閬垮厤銆岄珮鍒?+ 閲嶅ぇ杩斿伐 + 鍙斁琛屻€嶈繖绫讳簰鐩哥煕鐩剧殑灞曠ず銆?""
+    if verdict in {"閲嶅ぇ杩斿伐", "闇€瑕佷慨鏀?}:
+        if overall >= 80 and not needs_revision:
+            return ("閫氳繃", False, True)
+        return (verdict, True, False)
+    if needs_revision:
+        if verdict == "閫氳繃":
+            verdict = "闇€瑕佷慨鏀?
+        return (verdict, True, False)
+    if overall >= 80:
+        return ("閫氳繃", False, True)
+    if overall >= 75:
+        return (verdict if verdict in {"閫氳繃", "鏉′欢閫氳繃"} else "鏉′欢閫氳繃", False, True)
+    return (verdict, needs_revision, can_continue)
+
+
+def quality_report_evidence_too_sparse(payload: dict[str, Any]) -> bool:
+    """浠讳竴缁村害缂哄皯鏈夋晥 evidence 鈫?瑙嗕负绌哄３璇勫垎锛堢姝㈠彧鍚愬垎鏁帮級銆?""
+    dims = payload.get("dimensions")
+    if not isinstance(dims, dict) or not dims:
+        return True
+    for dim in dims.values():
+        if not isinstance(dim, dict):
+            return True
+        evidence = dim.get("evidence")
+        if not isinstance(evidence, list) or not evidence:
+            return True
+        if not any(isinstance(x, str) and len(x.strip()) >= 8 for x in evidence):
+            return True
+    return False
+
+
+def compliance_report_too_thin(payload: dict[str, Any]) -> bool:
+    result = str(payload.get("overall_result") or "")
+    blocking = payload.get("blocking_issues")
+    risks = payload.get("risk_items")
+    if not isinstance(blocking, list):
+        blocking = []
+    if not isinstance(risks, list):
+        risks = []
+    if result == "涓嶉€氳繃" and not blocking:
+        return True
+    for item in blocking:
+        if not isinstance(item, dict):
+            return True
+        title = str(item.get("title") or "").strip()
+        detail = str(item.get("description") or item.get("detail") or "").strip()
+        if len(title) < 2 or len(detail) < 8:
+            return True
+    for item in risks:
+        if not isinstance(item, dict):
+            return True
+        if len(str(item.get("description") or "").strip()) < 8:
+            return True
+        if len(str(item.get("suggestion") or "").strip()) < 8:
+            return True
+    return False
+
+
+def _normalize_blocking_issues(value: Any) -> list[dict[str, Any]]:
+    if not isinstance(value, list):
+        return []
+    result: list[dict[str, Any]] = []
+    for item in value:
+        if isinstance(item, str):
+            text = item.strip()
+            if text:
+                result.append({"title": text[:40], "description": text})
+            continue
+        if not isinstance(item, dict):
+            continue
+        row = dict(item)
+        title = (
+            _as_nonempty_str(row.get("title"))
+            or _as_nonempty_str(row.get("name"))
+            or _as_nonempty_str(row.get("issue"))
+            or _as_nonempty_str(row.get("rule_key"))
+            or _as_nonempty_str(row.get("category"))
+            or ""
+        )
+        detail = (
+            _as_nonempty_str(row.get("description"))
+            or _as_nonempty_str(row.get("detail"))
+            or _as_nonempty_str(row.get("summary"))
+            or ""
+        )
+        if not title:
+            title = (detail[:32] + "鈥?) if len(detail) > 32 else (detail or "鍚堣闂")
+        row["title"] = title
+        if detail and not _as_nonempty_str(row.get("description")):
+            row["description"] = detail
+        result.append(row)
+    return result
+
+
+def _normalize_compliance_risk_items(value: Any) -> list[dict[str, str]]:
+    if not isinstance(value, list):
+        return []
+    result: list[dict[str, str]] = []
+    for item in value:
+        if not isinstance(item, dict):
+            continue
+        risk_type = str(item.get("type") or "p2").lower()
+        if risk_type not in {"p0", "p1", "p2"}:
+            risk_type = "p2"
+        description = (
+            _as_nonempty_str(item.get("description"))
+            or _as_nonempty_str(item.get("issue"))
+            or _as_nonempty_str(item.get("title"))
+            or "鏈鏄庨闄?
+        )
+        suggestion = (
+            _as_nonempty_str(item.get("suggestion"))
+            or _as_nonempty_str(item.get("fix"))
+            or ""
+        )
+        result.append(
+            {
+                "type": risk_type,
+                "description": description,
+                "suggestion": suggestion,
+            }
+        )
+    return result
+
+
+def _as_number(value: Any, *, default: float) -> float:
+    try:
+        if value is None or value == "":
+            return default
+        return float(value)
+    except (TypeError, ValueError):
+        return default
+
+
+def _grade_from_score(score: float) -> str:
+    if score >= 90:
+        return "S"
+    if score >= 80:
+        return "A"
+    if score >= 75:
+        return "B"
+    if score >= 60:
+        return "C"
+    return "D"
diff --git a/backend/apps/drama/services/prompt_builder.py b/backend/apps/drama/services/prompt_builder.py
index f596c7c..ac21f44 100644
--- a/backend/apps/drama/services/prompt_builder.py
+++ b/backend/apps/drama/services/prompt_builder.py
@@ -1,14 +1,28 @@
 # -*- coding: utf-8 -*-
-"""鎸夎鑹插绾︾粍瑁?LLM 鎻愮ず璇嶏紝涓嶆硠闇叉棤鍏宠鑹?prompt銆?""
+"""鎸夎鑹插绾︾粍瑁?LLM 鎻愮ず璇嶏紝涓嶆硠闇叉棤鍏宠鑹?prompt銆?+
+娓愯繘鎶湶锛?+- L0 瑙掕壊杈圭晫 + SKILL 绱㈠紩浣?+- L1 鎸夐渶 modules锛坋nable_when锛?+- L2 rules锛坢ax_chars锛?+- L3 杈撳嚭濂戠害 + 鍙嶄緥 + 杞婚噺鐭ヨ瘑
+"""
 from __future__ import annotations
 
 import json
 from typing import Any
 
+from apps.drama.services.schema_prompt_contract import (
+    extract_required_paths,
+    load_artifact_fixture,
+    render_contract_block,
+)
 from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader
 
+_KNOWLEDGE_MAX_CHARS = 1200
+
 
 class PromptBuilder:
     """鍩轰簬 Skills SSOT 鏋勫缓 system/user prompt銆?""
 
     def __init__(self, loader: SkillsBundleLoader | None = None) -> None:
@@ -27,47 +41,94 @@ class PromptBuilder:
     ) -> tuple[str, str]:
         contract = self.loader.get_role_contract(role)
         entry = self.loader.get_role_entry(role)
         max_chars = int((contract.get("rule_policy") or {}).get("max_chars", 3200))
 
+        knowledge_budget = (
+            1800
+            if role in {"drama.script-scorer", "drama.compliance-guard"}
+            else _KNOWLEDGE_MAX_CHARS
+        )
         skill_text = self.loader.load_skill(role)
-        modules_text = self.loader.load_modules_for_role(role)
+        modules_text = self.loader.load_modules_for_role(role, settings)
         rules_text = self.loader.collect_rules(role, settings, max_chars=max_chars)
+        anti_text = self.loader.load_anti_examples(role)
+        knowledge_text = self.loader.load_knowledge_for_role(
+            role, settings, max_chars=knowledge_budget
+        )
+        fewshot_text = self.loader.load_fewshots(role)
         runtime = self.loader.project_runtime_projection(role, settings, workflow_state)
         artifact_key = self.loader.get_output_artifact_by_role(role)
         schema_version = self.loader.artifact_schema_version(artifact_key)
+        artifact_schema = _safe_load_artifact_schema(self.loader, artifact_key)
+        artifact_fixture = (
+            load_artifact_fixture(self.loader, artifact_key)
+            if artifact_schema is not None
+            else None
+        )
+        contract_block = (
+            render_contract_block(
+                artifact_key,
+                artifact_schema,
+                fixture=artifact_fixture,
+                max_chars=3500,
+            )
+            if artifact_schema is not None
+            else ""
+        )
+        schema_required_paths = (
+            extract_required_paths(artifact_schema) if artifact_schema is not None else []
+        )
+        scoring_inline = (
+            _inline_quality_scoring(self.loader, settings)
+            if role == "drama.script-scorer"
+            else ""
+        )
 
         system_parts = [
             f"浣犳槸 {entry.get('name_zh', role)}锛坅gent_id={role}锛夈€?,
             contract.get("role", ""),
             "",
             "## 鑱岃矗涓庢妧鑳?,
             skill_text,
         ]
         if modules_text:
             system_parts.extend(["", "## 妯″潡姝ラ", modules_text])
+        if scoring_inline:
+            system_parts.extend(["", scoring_inline])
         if rules_text:
             system_parts.extend(["", "## 瑙勫垯涓庣害鏉?, rules_text])
+        if knowledge_text:
+            system_parts.extend(["", "## 鍙傝€冪煡璇嗭紙鑺傞€夛級", knowledge_text])
+        if fewshot_text:
+            system_parts.extend(["", "## Few-shot 绀轰緥", fewshot_text])
+        if anti_text:
+            system_parts.extend(["", "## 杈撳嚭鍙嶄緥锛堢姝㈠鐜帮級", anti_text])
         system_parts.extend(
             [
                 "",
                 "## 杈撳嚭濂戠害",
                 f"- artifact_key: {artifact_key}",
                 f"- schema_version: {schema_version}",
-                "浠呰緭鍑虹鍚?schema 鐨?JSON 瀵硅薄锛屼笉瑕佽緭鍑鸿В閲婃枃瀛椼€?,
+                "浠呰緭鍑虹鍚?schema 鐨?JSON 瀵硅薄锛屼笉瑕佽緭鍑鸿В閲婃枃瀛楋紝涓嶈鍖呰９ markdown 浠ｇ爜鍥存爮銆?,
+                *_output_schema_hints(artifact_key, self.loader),
             ]
         )
+        if contract_block:
+            system_parts.extend(["", contract_block])
         system_prompt = "\n".join(part for part in system_parts if part is not None)
 
         user_body: dict[str, Any] = {
             "runtime_projection": runtime,
             "project_settings": _settings_subset(settings),
             "input": input_payload or {},
             "required_artifacts": _required_artifacts(contract, artifacts),
             "output": {
                 "artifact_key": artifact_key,
                 "schema_version": schema_version,
+                "schema_required": _schema_required_fields(artifact_key, self.loader),
+                "schema_required_paths": schema_required_paths,
             },
         }
         if latest_script is not None:
             user_body["latest_script"] = latest_script
         if scoring_mode:
@@ -84,27 +145,178 @@ def _settings_subset(settings: dict[str, Any]) -> dict[str, Any]:
         "core_idea",
         "synopsis",
         "external_story",
         "adapt_notes",
         "genre_matrix",
+        "audience_channel",
+        "protagonist_structure",
+        "flavor_tags",
         "episode_count",
         "target_platform",
         "creation_preferences",
         "production_context",
         "derived",
     )
     return {key: settings[key] for key in keys if key in settings}
 
 
+def _schema_required_fields(artifact_key: str, loader: SkillsBundleLoader) -> list[str]:
+    try:
+        schema = loader.load_artifact_schema(artifact_key)
+    except Exception:
+        return []
+    required = schema.get("required") or []
+    return [str(item) for item in required]
+
+
+def _safe_load_artifact_schema(
+    loader: SkillsBundleLoader, artifact_key: str
+) -> dict[str, Any] | None:
+    try:
+        return loader.load_artifact_schema(artifact_key)
+    except Exception:
+        return None
+
+
+def _output_schema_hints(artifact_key: str, loader: SkillsBundleLoader) -> list[str]:
+    """浠呬繚鐣?schema 澶栫殑琛屼负绾︽潫锛涘繀濉瓧娈电敱濂戠害鍧楃粺涓€鎻愪緵锛岄伩鍏嶉噸澶嶃€?""
+    hints: list[str] = []
+    if artifact_key == "project_brief":
+        hints.extend(
+            [
+                "- genre_matrix 蹇呴』鍖呭惈 emotion/identity/conflict/world/audience_channel锛?
+                "protagonist_structure銆乫lavor_tags 鏀惧湪 genre_matrix 鍐呫€?,
+                "- 涓嶈杈撳嚭 rule_params锛堢敱绯荤粺鎸夐鏉愮煩闃靛悎鎴愶級锛沚lockbuster_factors 蹇呴』鏄瓧绗︿覆鏁扮粍锛?
+                "compliance_risk 鍙兘鏄?low|medium|high銆?,
+                "- 涓嶈杈撳嚭 artifact_key銆乻chema_version銆乻ensitivity_pre_check 绛?schema 澶栧瓧娈点€?,
+            ]
+        )
+    if artifact_key == "story_bible":
+        hints.extend(
+            [
+                "- synopsis 蹇呴』鏄璞★紝涓斿悓鏃跺寘鍚?short锛堢煭姊楁锛変笌 full锛堝畬鏁存姒傦級锛?
+                "涓嶈鎶?synopsis 鍐欐垚瀛楃涓层€?,
+                "- adapt_source.mode 鍙兘鏄?original 鎴?adapt锛?
+                "characters[].role_type 鍙兘鏄?protagonist|antagonist|supporting銆?,
+                "- series_structure.six_stage_structure 蹇呴』鎭板ソ 6 椤癸紱"
+                "涓嶈杈撳嚭 schema 澶栧瓧娈点€?,
+            ]
+        )
+    if artifact_key == "quality_report":
+        hints.extend(
+            [
+                "- dimensions 蹇呴』鏄璞★紝閿负 format/narrative/conflict/character/"
+                "emotion/logic/satisfaction/hooks/paywall/genre_fit銆?,
+                "- 姣忎釜缁村害蹇呴』鍚?score銆亀eight銆乪vidence銆乨eductions锛?
+                "evidence 蹇呴』涓洪潪绌哄瓧绗︿覆鏁扮粍锛屾瘡鏉′笉灏戜簬 8 瀛楋紝椤诲紩鐢ㄥ叿浣撻泦鏁?鍦烘櫙/鍙拌瘝锛?
+                "绂佹绌烘暟缁勩€佺姝㈠彧杈撳嚭鍒嗘暟銆?,
+                "- deductions 鍙负绌烘暟缁勶紱鍏堝啓 evidence锛屽啀鎵?0-100 鍒嗐€?,
+                "- needs_revision=false 鏃?verdict 涓嶅緱涓恒€岄噸澶ц繑宸ャ€嶃€?,
+            ]
+        )
+    if artifact_key == "compliance_report":
+        hints.extend(
+            [
+                "- blocking_issues 涓?risk_items 椤诲啓鏄庡叿浣撹繚瑙勭偣銆佹秹鍙婇泦鏁?鍦烘櫙涓庝慨鏀瑰缓璁紝"
+                "绂佹浠呰緭鍑虹被鍒悕鎴栨ā鏉垮寲绌鸿瘽銆?,
+                "- risk_items[].type 鍙兘鏄?p0|p1|p2銆?,
+            ]
+        )
+    return hints
+
+
+def _inline_quality_scoring(
+    loader: SkillsBundleLoader,
+    settings: dict[str, Any],
+) -> str:
+    """鎶?quality-scoring.yaml + 褰撳墠 preset 鏉冮噸鍐呰仈杩涜瘎鍒嗗畼 prompt銆?""
+    try:
+        scoring = loader.load_seed_yaml("foundation/constraints/quality-scoring.yaml")
+        presets = loader.load_seed_yaml("foundation/constraints/scoring-presets.yaml")
+    except FileNotFoundError:
+        return ""
+
+    prefs = settings.get("creation_preferences") or {}
+    preset_id = str(prefs.get("scoring_preset") or "standard")
+    preset_map = presets.get("presets") if isinstance(presets.get("presets"), dict) else {}
+    if preset_id not in preset_map:
+        preset_id = "standard"
+    preset = preset_map.get(preset_id) or {}
+    weights = preset.get("weights") if isinstance(preset.get("weights"), dict) else {}
+    pass_threshold = preset.get("pass_threshold", scoring.get("revision_threshold", 75))
+
+    lines = [
+        "## 璇勫垎缁嗗垯锛堝唴鑱旓級",
+        f"- scoring_preset={preset_id}",
+        f"- pass_threshold={pass_threshold}",
+        f"- revision_threshold={scoring.get('revision_threshold')}",
+        f"- evolution_threshold={scoring.get('evolution_threshold')}",
+        f"- grade_thresholds={json.dumps(scoring.get('grade_thresholds') or {}, ensure_ascii=False)}",
+        "- 鍗佺淮瀹氫箟涓庢潈閲嶏紙鍏堣瘉鎹悗鎵撳垎锛涙瘡缁村繀椤昏緭鍑?evidence[] 涓?deductions[]锛夛細",
+    ]
+    for dim in scoring.get("dimensions") or []:
+        if not isinstance(dim, dict):
+            continue
+        key = str(dim.get("key") or "")
+        if not key:
+            continue
+        weight = weights.get(key, dim.get("weight"))
+        name = dim.get("name") or key
+        desc = str(dim.get("desc") or "").strip()
+        lines.append(f"  - {key}锛坽name}锛墂eight={weight}: {desc}")
+    return "\n".join(lines)
+
+
 def _required_artifacts(
     contract: dict[str, Any],
     artifacts: dict[str, Any],
 ) -> dict[str, Any]:
     input_contract = contract.get("input_contract") or {}
     required = list(input_contract.get("required_artifacts") or [])
+    optional = list(input_contract.get("optional_artifacts") or [])
+    keys = list(dict.fromkeys([*required, *optional]))
     result: dict[str, Any] = {}
-    for key in required:
+    for key in keys:
         if key == "latest_script":
             continue
         if key in artifacts:
-            result[key] = artifacts[key]
+            result[key] = _compact_artifact_payload(key, artifacts[key])
     return result
+
+
+def _compact_artifact_payload(artifact_key: str, payload: Any) -> Any:
+    """鍘嬬缉涓婃父浜х墿锛岄檷浣庤摑鍥剧瓑闀胯皟鐢ㄧ殑鎻愮ず璇嶄綋绉笌棣栧寘绛夊緟銆?""
+    if not isinstance(payload, dict):
+        return payload
+    if artifact_key != "project_brief":
+        return payload
+
+    keep_keys = (
+        "title",
+        "core_idea",
+        "genre_matrix",
+        "target_audience",
+        "core_conflict",
+        "hook_concept",
+        "commercial_hook",
+        "episode_count",
+        "compliance_risk",
+        "first_episode_hook",
+        "paywall_direction",
+        "market_opportunity",
+        "differentiation_strategy",
+        "blockbuster_factors",
+    )
+    compact: dict[str, Any] = {}
+    for key in keep_keys:
+        if key not in payload:
+            continue
+        value = payload[key]
+        if isinstance(value, str) and len(value) > 400:
+            compact[key] = f"{value[:400]}鈥?
+        elif key == "blockbuster_factors" and isinstance(value, list):
+            compact[key] = value[:5]
+        elif key == "competitor_references" and isinstance(value, list):
+            compact[key] = value[:2]
+        else:
+            compact[key] = value
+    return compact
diff --git a/backend/apps/drama/services/schema_prompt_contract.py b/backend/apps/drama/services/schema_prompt_contract.py
new file mode 100644
index 0000000..0b9303e
--- /dev/null
+++ b/backend/apps/drama/services/schema_prompt_contract.py
@@ -0,0 +1,302 @@
+from __future__ import annotations
+
+import json
+from copy import deepcopy
+from typing import Any, TYPE_CHECKING
+
+if TYPE_CHECKING:
+    from apps.drama.services.skills_loader import SkillsBundleLoader
+
+
+def load_artifact_fixture(
+    loader: "SkillsBundleLoader", artifact_key: str
+) -> dict[str, Any] | None:
+    """浠?build/fixtures/artifacts/valid-artifacts.json 璇诲彇浜х墿绀轰緥銆?+
+    鐢熶骇浠ｇ爜閫氳繃 loader 璇诲彇鎶€鑳戒粨锛岄伩鍏嶇洿鎺?import apps.drama.tests.helpers銆?+    """
+    try:
+        data = loader.load_json("build/fixtures/artifacts/valid-artifacts.json")
+    except (FileNotFoundError, json.JSONDecodeError):
+        return None
+    if not isinstance(data, dict):
+        return None
+    item = data.get(artifact_key)
+    return item if isinstance(item, dict) else None
+
+
+def extract_required_paths(
+    schema: dict[str, Any],
+    *,
+    max_paths: int = 80,
+) -> list[str]:
+    """閫掑綊鎶藉彇 JSON Schema required 璺緞锛堝惈鏁扮粍 items锛夈€?""
+    paths: list[str] = []
+    _walk_object(schema, prefix="", out=paths, max_paths=max_paths)
+    # 鍘婚噸涓斾繚鎸佺ǔ瀹氶『搴?+    seen: set[str] = set()
+    ordered: list[str] = []
+    for path in paths:
+        if path not in seen:
+            seen.add(path)
+            ordered.append(path)
+    return ordered[:max_paths]
+
+
+def _walk_object(
+    schema: dict[str, Any],
+    *,
+    prefix: str,
+    out: list[str],
+    max_paths: int,
+) -> None:
+    if len(out) >= max_paths:
+        return
+    if not isinstance(schema, dict):
+        return
+    required = schema.get("required") or []
+    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
+    for key in required:
+        key_s = str(key)
+        path = f"{prefix}.{key_s}" if prefix else key_s
+        out.append(path)
+        if len(out) >= max_paths:
+            return
+        child = props.get(key_s)
+        if isinstance(child, dict):
+            _walk_node(child, prefix=path, out=out, max_paths=max_paths)
+
+
+def _walk_node(
+    schema: dict[str, Any],
+    *,
+    prefix: str,
+    out: list[str],
+    max_paths: int,
+) -> None:
+    if len(out) >= max_paths:
+        return
+    schema_type = schema.get("type")
+    if schema_type == "object" or "properties" in schema or "required" in schema:
+        _walk_object(schema, prefix=prefix, out=out, max_paths=max_paths)
+        return
+    if schema_type == "array" or "items" in schema:
+        items = schema.get("items")
+        if isinstance(items, dict):
+            _walk_node(items, prefix=f"{prefix}[]", out=out, max_paths=max_paths)
+
+
+def build_output_skeleton(
+    schema: dict[str, Any],
+    *,
+    fixture: dict[str, Any] | None = None,
+    max_chars: int = 3500,
+) -> dict[str, Any]:
+    """鏍规嵁 schema 鐢熸垚鏈€灏忓悎娉曡緭鍑洪鏋讹細浼樺厛鐢?fixture 瑁佸壀锛屽惁鍒欐寜 type 濉崰浣嶃€?""
+    if fixture is not None:
+        skeleton = _prune_to_schema(deepcopy(fixture), schema)
+    else:
+        skeleton = _synthesize_from_schema(schema)
+    blob = json.dumps(skeleton, ensure_ascii=False)
+    if len(blob) > max_chars:
+        skeleton = _shrink_strings(skeleton, max_chars=max_chars)
+    return skeleton
+
+
+def render_contract_block(
+    artifact_key: str,
+    schema: dict[str, Any],
+    *,
+    fixture: dict[str, Any] | None = None,
+    max_chars: int = 3500,
+) -> str:
+    """杩斿洖鍙嫾杩?system prompt 鐨?Markdown 濂戠害鍧椼€?""
+    paths = extract_required_paths(schema)
+    skeleton = build_output_skeleton(schema, fixture=fixture, max_chars=max_chars)
+    example = json.dumps(skeleton, ensure_ascii=False, indent=2)
+    lines = [
+        f"- artifact_key: {artifact_key}",
+        "- 涓嬪垪瀛楁鍚嶅繀椤诲師鏍蜂娇鐢紙绂佹 want/need/open_hook 绛夊埆鍚嶉敭锛夛細",
+        "- 蹇呭～璺緞:",
+        *[f"  - {path}" for path in paths],
+        "- 鏈€灏忓悎娉曠ず渚嬶紙閿悕鍐欐锛屽彲鏀规枃妗堜笉鍙敼閿悕锛夛細",
+        "```json",
+        example,
+        "```",
+        "- 浠呰緭鍑轰竴涓?JSON 瀵硅薄锛涗笉瑕?markdown 鍥存爮锛涗笉瑕?schema 澶栧瓧娈点€?,
+    ]
+    return "\n".join(lines)
+
+
+def _schema_kind(schema: dict[str, Any]) -> str:
+    """鍒ゆ柇 schema 涓荤被鍨嬶細object / array / 鍩虹绫诲瀷銆?""
+    if not isinstance(schema, dict):
+        return "any"
+    schema_type = schema.get("type")
+    if isinstance(schema_type, list):
+        for t in schema_type:
+            if t != "null":
+                return t
+        return "any"
+    if schema_type in ("object", "array"):
+        return schema_type
+    if "properties" in schema or "required" in schema:
+        return "object"
+    if "items" in schema:
+        return "array"
+    if schema_type in ("string", "integer", "number", "boolean"):
+        return schema_type
+    if "enum" in schema:
+        return "enum"
+    return "any"
+
+
+def _prune_to_schema(value: Any, schema: dict[str, Any]) -> Any:
+    kind = _schema_kind(schema)
+    if kind == "object":
+        return _prune_object(value, schema)
+    if kind == "array":
+        return _prune_array(value, schema)
+    return _prune_primitive(value, schema)
+
+
+def _prune_object(value: Any, schema: dict[str, Any]) -> dict[str, Any]:
+    if not isinstance(value, dict):
+        return _synthesize_from_schema(schema)
+    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
+    required = schema.get("required") or []
+    additional_props_false = schema.get("additionalProperties") is False
+    result: dict[str, Any] = {}
+    for key, child_schema in props.items():
+        if key in value:
+            result[key] = _prune_to_schema(value[key], child_schema)
+    for key in required:
+        if key not in result:
+            child = props.get(key, {})
+            result[key] = _synthesize_from_schema(child if isinstance(child, dict) else {})
+    if not additional_props_false:
+        for key, val in value.items():
+            if key not in result:
+                result[key] = val
+    return result
+
+
+def _prune_array(value: Any, schema: dict[str, Any]) -> list[Any]:
+    if not isinstance(value, list):
+        return _synthesize_from_schema(schema)
+    items_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
+    pruned = [_prune_to_schema(item, items_schema) for item in value]
+    min_items = schema.get("minItems")
+    max_items = schema.get("maxItems")
+    if isinstance(min_items, int) and len(pruned) < min_items:
+        while len(pruned) < min_items:
+            pruned.append(_synthesize_from_schema(items_schema))
+    if isinstance(max_items, int) and len(pruned) > max_items:
+        pruned = pruned[:max_items]
+    return pruned
+
+
+def _prune_primitive(value: Any, schema: dict[str, Any]) -> Any:
+    enum = schema.get("enum")
+    if isinstance(enum, list) and enum:
+        if value in enum:
+            return value
+        return enum[0]
+    schema_type = schema.get("type")
+    if schema_type == "string":
+        return value if isinstance(value, str) else _synthesize_primitive(schema)
+    if schema_type == "integer":
+        return value if isinstance(value, int) and not isinstance(value, bool) else 1
+    if schema_type == "number":
+        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 1
+    if schema_type == "boolean":
+        return value if isinstance(value, bool) else True
+    return value
+
+
+def _synthesize_from_schema(schema: dict[str, Any]) -> Any:
+    kind = _schema_kind(schema)
+    if kind == "object":
+        return _synthesize_object(schema)
+    if kind == "array":
+        return _synthesize_array(schema)
+    return _synthesize_primitive(schema)
+
+
+def _synthesize_object(schema: dict[str, Any]) -> dict[str, Any]:
+    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
+    required = schema.get("required") or []
+    result: dict[str, Any] = {}
+    for key in required:
+        child = props.get(key, {})
+        result[key] = _synthesize_from_schema(child if isinstance(child, dict) else {})
+    return result
+
+
+def _synthesize_array(schema: dict[str, Any]) -> list[Any]:
+    items_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
+    min_items = schema.get("minItems")
+    max_items = schema.get("maxItems")
+    count = max(min_items if isinstance(min_items, int) else 1, 1)
+    if isinstance(max_items, int) and count > max_items:
+        count = max_items
+    return [_synthesize_from_schema(items_schema) for _ in range(count)]
+
+
+def _synthesize_primitive(schema: dict[str, Any]) -> Any:
+    enum = schema.get("enum")
+    if isinstance(enum, list) and enum:
+        return enum[0]
+    schema_type = schema.get("type")
+    if schema_type == "string":
+        return "绀轰緥"
+    if schema_type == "integer":
+        return 1
+    if schema_type == "number":
+        return 1
+    if schema_type == "boolean":
+        return True
+    if isinstance(schema_type, list):
+        for t in schema_type:
+            if t == "string":
+                return "绀轰緥"
+            if t in ("integer", "number"):
+                return 1
+            if t == "boolean":
+                return True
+    return "绀轰緥"
+
+
+def _shrink_strings(value: Any, *, max_chars: int) -> Any:
+    """鎸夋瘮渚嬬缉鏀惧瓧绗︿覆鍊硷紝浣?JSON blob 涓嶈秴杩?max_chars锛堜繚鐣欑粨鏋勪笌閿悕锛夈€?""
+    blob = json.dumps(value, ensure_ascii=False)
+    if len(blob) <= max_chars:
+        return value
+    strings: list[tuple[Any, Any, str]] = []
+    _collect_strings(value, strings)
+    total_len = sum(len(s) for _, _, s in strings)
+    if total_len == 0:
+        return value
+    structural = len(blob) - total_len
+    target_total = max(max_chars - structural, 0)
+    scale = target_total / total_len
+    for parent, key, s in strings:
+        new_len = int(len(s) * scale)
+        if new_len < len(s):
+            parent[key] = s[:new_len]
+    return value
+
+
+def _collect_strings(value: Any, out: list[tuple[Any, Any, str]]) -> None:
+    if isinstance(value, dict):
+        for k, v in value.items():
+            if isinstance(v, str):
+                out.append((value, k, v))
+            else:
+                _collect_strings(v, out)
+    elif isinstance(value, list):
+        for i, v in enumerate(value):
+            if isinstance(v, str):
+                out.append((value, i, v))
+            else:
+                _collect_strings(v, out)
diff --git a/backend/apps/drama/tests/test_prompt_schema_injection.py b/backend/apps/drama/tests/test_prompt_schema_injection.py
new file mode 100644
index 0000000..a58d06f
--- /dev/null
+++ b/backend/apps/drama/tests/test_prompt_schema_injection.py
@@ -0,0 +1,93 @@
+# -*- coding: utf-8 -*-
+"""PromptBuilder 娉ㄥ叆瀹屾暣濂戠害鍧楋細宓屽蹇呭～璺緞 + 绀轰緥 JSON銆?""
+from __future__ import annotations
+
+from pathlib import Path
+
+from django.test import SimpleTestCase, override_settings
+
+from apps.drama.services.prompt_builder import PromptBuilder
+from apps.drama.services.skills_loader import SkillsBundleLoader
+from apps.drama.tests.helpers import SKILLS_ROOT
+
+
+class SkillKeyAlignmentTests(SimpleTestCase):
+    def test_episode_designer_skill_mentions_opening_hook_key(self) -> None:
+        text = (
+            Path(SKILLS_ROOT) / "roles/drama-episode-designer/SKILL.md"
+        ).read_text(encoding="utf-8")
+        self.assertIn("`opening_hook`", text)
+        self.assertIn("`ending_hook`", text)
+        self.assertIn("`paywall_hook`", text)
+
+    def test_story_bible_skill_mentions_surface_desire_key(self) -> None:
+        text = (
+            Path(SKILLS_ROOT) / "roles/drama-story-bible/SKILL.md"
+        ).read_text(encoding="utf-8")
+        self.assertIn("`surface_desire`", text)
+        self.assertIn("`deep_need`", text)
+        self.assertIn("`arc.start`", text)
+
+_SETTINGS = {
+    "title": "鐜夌煶瀹棻",
+    "entry_type": "original_track",
+    "episode_count": 40,
+    "genre_matrix": {
+        "emotion": "ambition",
+        "identity": "hidden-elite",
+        "conflict": "power",
+        "world": "ancient",
+    },
+}
+
+
+@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
+class PromptSchemaInjectionTests(SimpleTestCase):
+    def setUp(self) -> None:
+        self.builder = PromptBuilder(loader=SkillsBundleLoader(root=SKILLS_ROOT))
+
+    def test_episode_designer_prompt_locks_opening_hook_key(self) -> None:
+        system, _user = self.builder.build(
+            "drama.episode-designer",
+            settings=_SETTINGS,
+            workflow_state={"current_phase": "episode_design"},
+            artifacts={},
+        )
+        self.assertIn("opening_hook", system)
+        self.assertIn("episode_narrative_designs[].opening_hook", system)
+        self.assertIn('"opening_hook"', system)  # 绀轰緥閲岀殑 JSON 閿?+        # 鏃х殑浠呴《灞傛彁绀哄彲娑堝け鎴栧苟瀛橈紝浣嗗繀椤绘湁宓屽璺緞
+        self.assertNotIn("蹇呭～瀛楁: episode_narrative_designs\n", system)
+
+    def test_story_bible_prompt_locks_surface_desire_and_arc_start(self) -> None:
+        system, _user = self.builder.build(
+            "drama.story-bible",
+            settings=_SETTINGS,
+            workflow_state={"current_phase": "blueprint"},
+            artifacts={},
+        )
+        self.assertIn("surface_desire", system)
+        self.assertIn("characters[].arc.start", system)
+        self.assertIn('"surface_desire"', system)
+
+    def test_user_prompt_carries_full_schema_required_paths(self) -> None:
+        _system, user = self.builder.build(
+            "drama.episode-designer",
+            settings=_SETTINGS,
+            workflow_state={"current_phase": "episode_design"},
+            artifacts={},
+        )
+        self.assertIn("schema_required_paths", user)
+        self.assertIn("episode_narrative_designs[].opening_hook", user)
+
+    def test_project_brief_keeps_behavior_constraints_without_top_required(self) -> None:
+        system, _user = self.builder.build(
+            "drama.topic-director",
+            settings=_SETTINGS,
+            workflow_state={"current_phase": "blueprint"},
+            artifacts={},
+        )
+        # 琛屼负绾︽潫淇濈暀
+        self.assertIn("schema 澶栧瓧娈?, system)
+        # 鏃х殑浠呴《灞傚繀濉瓧娈垫彁绀哄簲娑堝け
+        self.assertNotIn("蹇呭～瀛楁: title", system)
diff --git a/backend/apps/drama/tests/test_schema_prompt_contract.py b/backend/apps/drama/tests/test_schema_prompt_contract.py
new file mode 100644
index 0000000..944c14b
--- /dev/null
+++ b/backend/apps/drama/tests/test_schema_prompt_contract.py
@@ -0,0 +1,193 @@
+from django.test import SimpleTestCase, override_settings
+
+from apps.core.schema_validator import SchemaValidator
+from apps.drama.services.schema_prompt_contract import build_output_skeleton, extract_required_paths
+from apps.drama.services.skills_loader import SkillsBundleLoader
+from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT
+
+
+class ExtractRequiredPathsTests(SimpleTestCase):
+    def test_narrative_plan_includes_nested_opening_hook(self) -> None:
+        schema = {
+            "type": "object",
+            "required": ["episode_narrative_designs"],
+            "properties": {
+                "episode_narrative_designs": {
+                    "type": "array",
+                    "items": {
+                        "type": "object",
+                        "required": ["episode", "opening_hook", "ending_hook"],
+                        "properties": {
+                            "episode": {"type": "integer"},
+                            "opening_hook": {"type": "string"},
+                            "ending_hook": {"type": "string"},
+                        },
+                    },
+                }
+            },
+        }
+        paths = extract_required_paths(schema)
+        self.assertIn("episode_narrative_designs", paths)
+        self.assertIn("episode_narrative_designs[].opening_hook", paths)
+        self.assertIn("episode_narrative_designs[].ending_hook", paths)
+
+    def test_story_bible_includes_character_arc_start(self) -> None:
+        schema = {
+            "type": "object",
+            "required": ["characters"],
+            "properties": {
+                "characters": {
+                    "type": "array",
+                    "items": {
+                        "type": "object",
+                        "required": ["name", "surface_desire", "arc"],
+                        "properties": {
+                            "name": {"type": "string"},
+                            "surface_desire": {"type": "string"},
+                            "arc": {
+                                "type": "object",
+                                "required": ["start", "end"],
+                                "properties": {
+                                    "start": {"type": "string"},
+                                    "end": {"type": "string"},
+                                },
+                            },
+                        },
+                    },
+                }
+            },
+        }
+        paths = extract_required_paths(schema)
+        self.assertIn("characters[].surface_desire", paths)
+        self.assertIn("characters[].arc.start", paths)
+
+
+@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
+class StoryBibleFewshotSchemaTests(SimpleTestCase):
+    """Task 5: 棣栦釜 fewshot 蹇呴』鏄畬鏁?schema 鍚堟硶鐨?story_bible銆?""
+
+    def test_first_fewshot_output_validates(self) -> None:
+        import yaml
+        from pathlib import Path
+
+        path = Path(SKILLS_ROOT) / "roles/drama-story-bible/fewshots.v1.yaml"
+        data = yaml.safe_load(path.read_text(encoding="utf-8"))
+        output = data["fewshots"][0]["output"]
+        SchemaValidator().validate_file(
+            output, "schemas/artifacts/story_bible/1.schema.json"
+        )
+
+    def test_first_fewshot_output_has_no_alias_keys(self) -> None:
+        import yaml
+        from pathlib import Path
+
+        path = Path(SKILLS_ROOT) / "roles/drama-story-bible/fewshots.v1.yaml"
+        data = yaml.safe_load(path.read_text(encoding="utf-8"))
+        output = data["fewshots"][0]["output"]
+        # want/initial 绛夊埆鍚嶉敭绂佹鍑虹幇鍦?fewshot output
+        self.assertNotIn("want", output)
+        self.assertNotIn("initial", output)
+        for char in output.get("characters", []):
+            self.assertNotIn("want", char)
+            self.assertNotIn("initial", char)
+
+
+@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
+class BuildOutputSkeletonTests(SimpleTestCase):
+    def test_narrative_plan_skeleton_validates(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("narrative_plan")
+        skeleton = build_output_skeleton(
+            schema, fixture=FIXTURES["narrative_plan"]
+        )
+        self.assertIn("opening_hook", skeleton["episode_narrative_designs"][0])
+        SchemaValidator().validate_file(
+            skeleton, "schemas/artifacts/narrative_plan/1.schema.json"
+        )
+
+    def test_story_bible_skeleton_uses_surface_desire_not_want(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("story_bible")
+        skeleton = build_output_skeleton(schema, fixture=FIXTURES["story_bible"])
+        char = skeleton["characters"][0]
+        self.assertIn("surface_desire", char)
+        self.assertNotIn("want", char)
+        self.assertIn("start", char["arc"])
+        SchemaValidator().validate_file(
+            skeleton, "schemas/artifacts/story_bible/1.schema.json"
+        )
+
+    def test_six_stage_structure_exactly_six(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("story_bible")
+        skeleton = build_output_skeleton(schema, fixture=FIXTURES["story_bible"])
+        stages = skeleton["series_structure"]["six_stage_structure"]
+        self.assertEqual(len(stages), 6)
+
+    def test_synthesize_without_fixture_validates_story_bible(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("story_bible")
+        skeleton = build_output_skeleton(schema)
+        self.assertIn("surface_desire", skeleton["characters"][0])
+        self.assertEqual(len(skeleton["series_structure"]["six_stage_structure"]), 6)
+        SchemaValidator().validate_file(
+            skeleton, "schemas/artifacts/story_bible/1.schema.json"
+        )
+
+    def test_hook_grade_only_from_enum(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("narrative_plan")
+        skeleton = build_output_skeleton(schema, fixture=FIXTURES["narrative_plan"])
+        self.assertIn(skeleton["episode_narrative_designs"][0]["hook_grade"], {"S", "A", "B", "C"})
+
+    def test_prune_strips_unknown_keys_when_additional_properties_false(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("story_bible")
+        bloated_fixture = {
+            **FIXTURES["story_bible"],
+            "want": "should_be_removed",
+        }
+        skeleton = build_output_skeleton(schema, fixture=bloated_fixture)
+        self.assertNotIn("want", skeleton)
+
+    def test_prune_synthesizes_missing_required_field(self) -> None:
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("narrative_plan")
+        incomplete = {
+            "episode_narrative_designs": [
+                {
+                    "episode": 1,
+                    "title": "褰掓潵",
+                    "core_event": "涓昏鎷掔粷绛惧瓧",
+                    "goal_conflict": "淇濅綇鑲℃潈脳瀹舵棌閫艰揩",
+                    "emotion_intensity": 8,
+                    # opening_hook 缂哄け锛岄渶鐢?_synthesize_from_schema 琛ラ綈
+                    "ending_hook": "璇佹嵁鍑虹幇",
+                    "satisfaction_points": ["褰撲紬鎷掔粷"],
+                    "reversal": "涓昏鎺屾彙褰曢煶",
+                    "paywall_hook": "褰曢煶鍐呭鏈叕寮€",
+                    "rhythm_tag": "tight-heavy",
+                    "foreshadowing": {"setup": ["鎬€琛?], "payoff": []},
+                    "hook_grade": "B",
+                    "characters": ["鏋楀"],
+                    "emotion_nodes": {"EV": {"value": 8}, "ET": {"value": 3}, "TP": {"content": "鎷掔粷绛惧瓧"}},
+                }
+            ]
+        }
+        skeleton = build_output_skeleton(schema, fixture=incomplete)
+        self.assertIn("opening_hook", skeleton["episode_narrative_designs"][0])
+        SchemaValidator().validate_file(
+            skeleton, "schemas/artifacts/narrative_plan/1.schema.json"
+        )
+
+    def test_render_contract_block_returns_markdown(self) -> None:
+        from apps.drama.services.schema_prompt_contract import render_contract_block
+
+        loader = SkillsBundleLoader()
+        schema = loader.load_artifact_schema("narrative_plan")
+        block = render_contract_block(
+            "narrative_plan", schema, fixture=FIXTURES["narrative_plan"]
+        )
+        self.assertIn("artifact_key: narrative_plan", block)
+        self.assertIn("episode_narrative_designs[].opening_hook", block)
+        self.assertIn("```json", block)
diff --git a/drama-skills/knowledge/output-schemas.md b/drama-skills/knowledge/output-schemas.md
index 9d0a28a..143f84c 100644
--- a/drama-skills/knowledge/output-schemas.md
+++ b/drama-skills/knowledge/output-schemas.md
@@ -1,9 +1,10 @@
 # 杈撳嚭濂戠害 Schema锛圤utput Schemas锛? 
-> **鏈哄櫒 SSOT**锛歚contracts/artifacts.yaml` + `schemas/artifacts/<artifact_key>/1.schema.json`锛涙湰鏂囦欢鏄汉绫诲彲璇昏鏄庛€?-> 瑙掕壊涓庝骇鐗╃储寮曚互 `registry.yaml` 涓?`contracts/artifacts.yaml` 涓哄噯銆?+> **鏈哄櫒 SSOT**锛歚schemas/artifacts/<artifact_key>/1.schema.json`銆?+> **Prompt 瀛楁琛?*锛氳繍琛屾椂鐢?`schema_prompt_contract` 浠?schema 鐢熸垚锛岀姝㈠湪 prompt_builder 鎵嬪啓绗簩浠藉繀濉竻鍗曘€?+> 鏈?Markdown 浠呬緵浜鸿锛涜嫢涓?schema 鍐茬獊锛屼互 schema 涓哄噯銆? 
 ## schema 绱㈠紩
 
 | artifact_key | schema_version | 涓枃鏍囩 | 瑙掕壊 | 鏍煎紡 |
 |--------------|----------------|----------|------|------|
diff --git a/drama-skills/roles/drama-episode-designer/SKILL.md b/drama-skills/roles/drama-episode-designer/SKILL.md
index 62a1b7c..7de4402 100644
--- a/drama-skills/roles/drama-episode-designer/SKILL.md
+++ b/drama-skills/roles/drama-episode-designer/SKILL.md
@@ -45,24 +45,26 @@ references:
 3. 鎸夐挬瀛愪綋绯绘ā鍧楄璁￠泦棣?闆嗘湯閽╁瓙骞舵爣娉ㄧ瓑绾э紙`modules/hook-system.md`锛? 4. 鎸夊啿绐佸崌绾т笌鍙嶈浆浼忕瑪闂幆妯″潡瀹夋帓鍐茬獊鍗囩骇銆佸弽杞€佸煁璁句笌鍥炴墸
 5. 鐢ㄤ粯璐瑰崱鐐规ā鍧楄惤瀹炴壙璇恒€佸崱鐐瑰拰鍏戠幇浣嶇疆
 6. 閫愰泦杈撳嚭 episode card锛岃窇鍚勬ā鍧楄嚜妫€娓呭崟
 
-## 鏍囧噯杈撳嚭瑕佹眰
+## 鏍囧噯杈撳嚭瑕佹眰锛堥敭鍚嶅繀椤讳笌 schema 涓€鑷达級
 
-- 姣忛泦鏍囬
-- 姣忛泦鏍稿績浜嬩欢
-- 姣忛泦鍑哄満浜虹墿
-- 姣忛泦 Goal 脳 Conflict
-- 姣忛泦鎯呯华寮哄害
-- 姣忛泦鐖界偣
-- 闆嗛閽╁瓙
-- 闆嗘湯閽╁瓙
-- 鍗曢泦鍙嶈浆
-- 浼忕瑪鍩嬭 / 鍥炴墸
-- 浠樿垂鍗＄偣
-- 鍙岃建鑺傚鏍囨敞
+- `title`锛氭瘡闆嗘爣棰?+- `core_event`锛氭瘡闆嗘牳蹇冧簨浠?+- `characters`锛氬嚭鍦轰汉鐗╁悕鏁扮粍
+- `goal_conflict`锛欸oal 脳 Conflict
+- `emotion_intensity`锛氭儏缁己搴?1鈥?0
+- `satisfaction_points`锛氱埥鐐瑰瓧绗︿覆鏁扮粍
+- `opening_hook`锛氶泦棣栭挬瀛愶紙绂佹鍐欐垚 open_hook / opening锛?+- `ending_hook`锛氶泦鏈挬瀛愶紙绂佹鍐欐垚 cliffhanger 椤跺眰閿級
+- `reversal`锛氬崟闆嗗弽杞?+- `foreshadowing.setup` / `foreshadowing.payoff`
+- `paywall_hook`锛氫粯璐瑰崱鐐?+- `rhythm_tag`锛氬弻杞ㄨ妭濂忔爣娉?+- `hook_grade`锛歋|A|B|C
+- `emotion_nodes.EV` / `ET` / `TP`
 
 ## 瑙﹀彂鏂瑰紡
 
 ```
 @drama-episode-designer episode_range=1-10
diff --git a/drama-skills/roles/drama-story-bible/SKILL.md b/drama-skills/roles/drama-story-bible/SKILL.md
index 775d739..e4710c2 100644
--- a/drama-skills/roles/drama-story-bible/SKILL.md
+++ b/drama-skills/roles/drama-story-bible/SKILL.md
@@ -1,9 +1,11 @@
 ---
 name: drama-story-bible
-version: 5.0.0
-description: 鍓ф湰钃濆浘瀹橈細鍚堝苟浜虹墿鍏崇郴涓庡叏鍓ф灦鏋勮兘鍔涳紝杈撳嚭鍓ф湰姊楁+浜虹墿+涓栫晫瑙?鍏ㄥ墽缁撴瀯涓€浣撶殑 story_bible銆傛敮鎸佸師鍒涙ā寮忥紙鎺ラ€夐绠€鎶ワ級涓庢敼缂栨ā寮忥紙鎻愬彇骞惰ˉ鍏ㄧ敤鎴锋彁渚涚殑鏁呬簨锛夈€?+version: 5.1.0
+description: >
+  浣曟椂鐢細鍩轰簬 project_brief 灞曞紑鍘熷垱钃濆浘锛屾垨鍩轰簬 external_story 鍋氭敼缂栬摑鍥撅紝杈撳嚭 story_bible銆?+  浣曟椂涓嶇敤锛氫粛鍦ㄩ€夐闃舵涓旀病鏈夊畾璋冭緭鍏ユ椂涓嶈鎶㈣窇锛涗笉瑕佸睍寮€閫愰泦姝ｆ枃鎴栧垎闆嗗崱锛堜氦缁欏垎闆嗚璁″畼/姝ｆ枃瀹橈級銆? tags:
 - 鍓ф湰姊楁
 - 浜虹墿灏忎紶
 - 鍏崇郴缃? - 杞婚噺涓栫晫瑙?@@ -23,74 +25,86 @@ output_schema:
 - name: story_bible
   type: object
   description: 鏁呬簨钃濆浘锛堟姒?+ 浜虹墿 + 涓栫晫瑙勫垯 + 鍏ㄥ墽缁撴瀯锛? references:
 - ./role.yaml
+- ./anti-examples.yaml
 - ../../modules/character-system.md
 - ../../modules/world-rules.md
 - ../../modules/series-structure.md
 - ../../modules/series-emotion-curve.md
 - ../../modules/conflict-escalation.md
 - ../../modules/reversal-foreshadowing.md
 - ../../modules/adaptation-originality.md
 - ../../foundation/rules/character-rules.yaml
 - ../../knowledge/quality/originality-rules.md
+- ../../knowledge/quality/structured-output-guards.md
 - ../../knowledge/craft/shanyin-screenwriting-methodology.md
 - ../../knowledge/craft/shanyin-feature-format.md
 - ../../knowledge/craft/shanyin-series-format.md
 ---
 
-# 鍓ф湰钃濆浘瀹?v5.0
+# 鍓ф湰钃濆浘瀹?v5.1
 
-> 瑙掕壊閲嶇粍鍘熷垯锛氳鑹插噺灏戯紝鐭ヨ瘑涓嶄涪銆傛湰瑙掕壊鍚堝苟鍘熴€屼汉鐗╁叧绯诲畼銆嶄笌銆屽叏鍓ф灦鏋勫畼銆嶅叏閮ㄨ兘鍔涳紝
-> 瀵瑰簲鍟嗕笟鍒涗綔娴佺▼涓殑銆屽墽鏈憳瑕併€嶄竴姝ワ紝浣嗗悓鏃堕攣瀹氫汉鐗╀笌鍏ㄥ墽缁撴瀯锛岄伩鍏嶄袱鑰呰劚鑺傘€?+> Agent Skills 绱㈠紩浣擄細缁嗚妭鍦?modules锛涘弽渚嬪湪 `anti-examples.yaml`銆?+> 鍚堝苟鍘熴€屼汉鐗╁叧绯诲畼銆嶄笌銆屽叏鍓ф灦鏋勫畼銆嶈兘鍔涳紝鍙帶鍒跺叏灞€銆? 
-## 鑱岃矗
+## 鑱岃矗杈圭晫
 
-涓€娆℃€у洖绛斻€岃繖鏄竴涓粈涔堟晠浜嬨€佽皝鍦ㄦ帹鍔ㄥ畠銆佹暣閮ㄥ墽鎬庝箞璧疯浆鐖嗘敹銆嶃€傝緭鍑?`story_bible`锛坰chema v1锛夛紝鍙帶鍒跺叏灞€锛屼笉灞曞紑閫愰泦缁嗚妭銆?+涓€娆℃€у洖绛斻€岃繖鏄粈涔堟晠浜嬨€佽皝鍦ㄦ帹鍔ㄣ€佹暣閮ㄥ墽鎬庝箞璧疯浆鐖嗘敹銆嶃€傝緭鍑?`story_bible`锛屼笉鍐欓€愰泦鍓ф湰銆? 
-## 鍙屾ā寮?+## 杈撳叆/杈撳嚭濂戠害
 
-| 妯″紡 | 杈撳叆 | 琛屼负 |
-|------|------|------|
-| 鍘熷垱妯″紡 | `project_brief`锛堜笂娓革細閫夐瀹氳皟瀹橈級 | 鍩轰簬瀹氳皟绠€鎶ュ睍寮€姊楁銆佷汉鐗╀笌鍏ㄥ墽缁撴瀯 |
-| 鏀圭紪妯″紡 | `external_story`锛堢敤鎴风矘璐存晠浜?灏忚/澶х翰锛? 鍙€?`adapt_notes` | 鍏堟彁鍙栧師鏁呬簨鐨勪汉鐗┿€佸啿绐佷笌缁撴瀯锛屽啀鎸夌煭鍓ц寰嬭ˉ鍏ㄧ己澶遍儴鍒嗭紝骞舵墽琛屽師鍒涙€ч闄╄嚜妫€锛堣 `knowledge/quality/originality-rules.md`锛?|
+- 鍘熷垱妯″紡锛氬繀闇€涓婃父 `project_brief`锛涜繍琛屽弬鏁拌 `contracts/parameters.yaml`
+- 鏀圭紪妯″紡锛氬繀闇€ `external_story`锛屽彲閫?`adapt_notes`锛涢』鍋氬師鍒涙€ч闄╄嚜妫€
+- 鍏朵粬鍙傛暟锛歚episode_count`銆乣outline_mode`锛坒ull / structure_only锛?+- 杈撳嚭浜х墿锛歚story_bible`锛坰chema v1锛夛紱涓ょ妯″紡 schema 鐩稿悓
 
-杩愯鍙傛暟锛圫SOT锛歚contracts/parameters.yaml#role_parameter_refs`锛夛細`external_story`銆乣adapt_notes`銆?-`episode_count`锛堟€婚泦鏁帮紝鍐冲畾鍏樁娈垫崲绠楋級銆乣outline_mode`锛坒ull / structure_only锛夈€?+## 妯″潡绱㈠紩
 
-涓ょ妯″紡杈撳嚭瀹屽叏鐩稿悓鐨?schema锛屼笅娓稿垎闆嗚璁″畼鏃犲樊鍒秷璐广€傛敼缂栨ā寮忓繀椤绘樉寮忓垪鍑恒€屼繚鐣?/ 寮哄寲 / 鏀瑰啓銆嶄笁绫诲鐞嗚鏄庛€?+| module | 鐢ㄩ€?| 鏉′欢 |
+|--------|------|------|
+| `character-system` | 浜虹墿灏忎紶涓庡姬鍏?| 濮嬬粓 |
+| `world-rules` | 鍙鍔ㄤ笘鐣岃鍒?| 濮嬬粓 |
+| `series-structure` | 鍏樁娈靛叏鍓х粨鏋?| 濮嬬粓 |
+| `series-emotion-curve` | 鍏ㄥ墽鎯呯华鏇茬嚎 | 濮嬬粓 |
+| `conflict-escalation` | 鍐茬獊鍗囩骇閾?| 濮嬬粓 |
+| `reversal-foreshadowing` | 鍙嶈浆涓庝紡绗旀€昏〃 | 濮嬬粓 |
+| `adaptation-originality` | 鏀圭紪淇濈暀/寮哄寲/鏀瑰啓涓庡師鍒涙€?| 浠?`entry_type == story_adapt` |
 
-## 鏍囧噯杈撳嚭瑕佹眰
+## 姝ｄ緥
 
-**姊楁灞?*
+`synopsis` 蹇呴』鏄璞★細
 
-- 涓€鍙ヨ瘽鏁呬簨锛坙ogline锛?-- 300 瀛楃煭姊楁 + 鍗冨瓧瀹屾暣姊楁
-
-**浜虹墿灞?*锛堝師浜虹墿鍏崇郴瀹樿兘鍔涳級
+```json
+{
+  "drama_title": "閫嗗厜閲嶆潵",
+  "logline": "琚姏寮冪殑缁ф壙浜洪噸鐢熷悗鏀瑰啓瀹舵棌鍛借繍",
+  "synopsis": {
+    "short": "濂归噸鐢熷洖鍒拌閫愬嚭瀹堕棬閭ｅぉ锛屽喅瀹氬厛涓嬫墜涓哄己銆?,
+    "full": "瀹屾暣鍗冨瓧姊楁鈥︹€?
+  }
+}
+```
 
-- 涓昏銆佸弽娲俱€佹牳蹇冮厤瑙掑皬浼狅紙涓昏鈮?锛屽叧绯昏鑹测墹6锛?-- Want / Need / Ghost / Lie / Flaw
-- 浜虹墿鍏崇郴缃戙€佷汉鐗╁姬鍏夈€佽涓鸿竟鐣屼笌绂佸繉
-- 瑙備紬浠ｅ叆鐐广€佹儏缁棝鐐广€佽瑙夎瘑鍒偣銆丄I 閰嶉煶闊宠壊鏍囩
-- 杞婚噺涓栫晫瑙勫垯锛氬彧淇濈暀浼氬奖鍝嶄汉鐗╄鍔ㄤ笌鍓ф儏閫夋嫨鐨勮鍒?+## 浜虹墿瀛楁锛堥敭鍚嶅繀椤讳笌 schema 涓€鑷达級
 
-**缁撴瀯灞?*锛堝師鍏ㄥ墽鏋舵瀯瀹樿兘鍔涳級
+- 浜虹墿娆叉湜瀛楁锛歚surface_desire`锛堟兂瑕侊級銆乣deep_need`锛堥渶瑕侊級锛涚姝㈣緭鍑?want/need 浣滀负閿悕
+- 寮у厜瀵硅薄锛歚arc.start` / `arc.turning_point_1` / `arc.turning_point_2` / `arc.end`锛涚姝?initial/midpoint/final
 
-- 鍏ㄥ墽涓荤嚎涓庢牳蹇冨啿绐侀摼
-- 鍏樁娈电粨鏋勶紙100 闆嗗熀鍑嗭細10/20/20/20/15/15锛岄鏉愬彲瑕嗙洊锛?-- 涓荤嚎 / 鏀嚎瀹夋帓銆佷汉鐗╁姬鍏夎惤鐐?-- 鍏抽敭鍙嶈浆浣嶇疆銆佷粯璐硅妭鐐瑰垎甯?-- 浼忕瑪鎬昏〃銆佸叏鍓ф儏缁洸绾?+## 鍙嶄緥
 
-## 闀垮墽鍒嗚妭绛栫暐
+璇﹁ `anti-examples.yaml`銆傜‖绂佹锛? 
-50 闆嗕互涓婇」鐩彲鍒嗕袱鎵圭敓鎴愶細鍏堣緭鍑烘姒傚眰+浜虹墿灞?涓栫晫瑙勫垯锛岀‘璁ゅ悗鍐嶈緭鍑虹粨鏋勫眰锛坄outline_mode=structure_only`锛夛紝涓ゆ壒鍚堝苟涓哄悓涓€ `story_bible`銆?+- 鎶?`synopsis` 鍐欐垚瀛楃涓?+- `characters[].role_type` 浣跨敤闈炴灇涓惧€?+- `six_stage_structure` 涓嶆槸鎭板ソ 6 椤?+- 杈撳嚭閫愰泦瀹屾暣鍓ф湰姝ｆ枃
 
-## 瑙﹀彂鏂瑰紡
+## 鑷娓呭崟
 
-```
-@drama-story-bible 鍩轰簬绔嬮」绠€鎶ヨ緭鍑烘晠浜嬭摑鍥?-@drama-story-bible external_story=銆?..銆?鎶婅繖涓晠浜嬫敼缂栨垚30闆嗙煭鍓ц摑鍥?-@drama-story-bible outline_mode=structure_only
-```
+1. `synopsis.short` 涓?`synopsis.full` 鏄惁閮藉瓨鍦ㄤ笖闈炵┖锛?+2. `adapt_source.mode` 鏄惁涓?`original` 鎴?`adapt`锛?+3. 涓昏 鈮?銆佸叧绯昏鑹插悎鐞嗭紝涓?`role_type` 鍚堟硶锛?+4. `series_structure.six_stage_structure` 鏄惁鎭板ソ 6 娈碉紵
+5. 鏀圭紪妯″紡鏄惁鍐欐槑淇濈暀/寮哄寲/鏀瑰啓锛?+6. 鏄惁鏈睍寮€閫愰泦姝ｆ枃锛?diff --git a/drama-skills/roles/drama-story-bible/fewshots.v1.yaml b/drama-skills/roles/drama-story-bible/fewshots.v1.yaml
new file mode 100644
index 0000000..5225aaa
--- /dev/null
+++ b/drama-skills/roles/drama-story-bible/fewshots.v1.yaml
@@ -0,0 +1,177 @@
+version: 1.0.0
+source: eval/cases offline fixtures
+note: |
+  浜哄伐瀹￠槄鍚庡啀琚?PromptBuilder 寮曠敤锛涚姝㈡棤瀹¤嚜鍔ㄨ鐩?SKILL.md銆?+  浠?case_id=SB001 涓?schema 瀹屾暣鍚堟硶绀轰緥锛堝榻?story_bible/1.schema.json锛夛紱
+  鍏朵綑 case 涓洪鏍肩ず鎰忥紝瀛楁涓嶅叏锛屽嬁浣滀负 schema 鑼冩湰銆?+fewshots:
+- case_id: SB001
+  input:
+    title: 钃濆浘鏍蜂緥1
+    entry_type: original_track
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥1
+    logline: 濂瑰甫鐫€鐪熺浉閲嶅洖琚姏寮冨綋澶?+    synopsis:
+      short: 琚鏃忔姏寮冪殑缁ф壙浜洪噸鐢熷悗澶哄洖浜虹敓
+      full: 琚鏃忔姏寮冪殑缁ф壙浜洪噸鐢熷悗澶哄洖浜虹敓锛屽€熺敱鎻愬墠鐭ユ檽鐨勮儗鍙涢€愬眬缈荤洏锛屾渶缁堜互鑷垜浠峰€煎彇浠ｄ粬浜鸿鍙€?+    adapt_source:
+      mode: original
+      retained: []
+      enhanced: []
+      rewritten: []
+      originality_check: 鍘熷垱
+    world_rules:
+      setting_summary: 鐜颁唬瀹舵棌浼佷笟
+      root_rules:
+      - 鑲℃潈鍐冲畾璇濊鏉?+      power_structure: 钁ｄ簨浼氭帶鍒惰祫婧?+    characters:
+    - name: 鏋楀
+      role_type: protagonist
+      surface_desire: 澶哄洖鑲℃潈
+      deep_need: 寤虹珛鑷垜浠峰€?+      ghost: 琚鏃忔姏寮?+      lie: 鍙湁琚鍙墠鏈変环鍊?+      flaw: 杩囧害璇佹槑
+      arc:
+        start: 渚濊禆璁ゅ彲
+        turning_point_1: 鐙珛鍐崇瓥
+        turning_point_2: 鏀惧純璁ㄥソ
+        end: 鑷垜纭
+      audience_identification: 鑱屽満涓庡搴竟鐣?+      voice_tag: 鐭彞鐩存帴
+      visual_anchor: 鏃ф€€琛?+    relationship_map: []
+    series_structure:
+      main_storyline: 澶哄洖浜虹敓
+      six_stage_structure:
+      - {}
+      - {}
+      - {}
+      - {}
+      - {}
+      - {}
+      conflict_escalation_chain: []
+      major_reversal_positions: []
+      paywall_distribution: []
+      foreshadowing_table: []
+      series_emotion_curve: []
+- case_id: SB002
+  input:
+    title: 钃濆浘鏍蜂緥2
+    entry_type: original_track
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥2
+    logline: 鏍蜂緥2鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
+- case_id: SB003
+  input:
+    title: 钃濆浘鏍蜂緥3
+    entry_type: original_track
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥3
+    logline: 鏍蜂緥3鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
+- case_id: SB004
+  input:
+    title: 钃濆浘鏍蜂緥4
+    entry_type: story_adapt
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥4
+    logline: 鏍蜂緥4鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
+- case_id: SB005
+  input:
+    title: 钃濆浘鏍蜂緥5
+    entry_type: original_track
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥5
+    logline: 鏍蜂緥5鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
+- case_id: SB006
+  input:
+    title: 钃濆浘鏍蜂緥6
+    entry_type: original_track
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥6
+    logline: 鏍蜂緥6鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
+- case_id: SB007
+  input:
+    title: 钃濆浘鏍蜂緥7
+    entry_type: original_track
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥7
+    logline: 鏍蜂緥7鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
+- case_id: SB008
+  input:
+    title: 钃濆浘鏍蜂緥8
+    entry_type: story_adapt
+    core_idea: null
+    genre_matrix:
+      emotion: revenge
+      identity: reborn
+      conflict: family
+      world: modern
+  output:
+    drama_title: 钃濆浘鏍蜂緥8
+    logline: 鏍蜂緥8鐨勪竴鍙ヨ瘽鏁呬簨
+    synopsis:
+      short: 鐭姒?+      full: 瀹屾暣姊楁
```

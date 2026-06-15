# -*- coding: utf-8 -*-
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.creation.display.portal_display import portal_gate_log
from apps.creation.display.structure_display import (
    build_structure_plan_view,
    build_world_validation_log,
    normalize_core_nouns,
    normalize_dream_indicators,
    normalize_key_reversal_points,
    normalize_reversal_type,
    normalize_rhythm_block,
    normalize_structure_payload,
    validate_worldview_issues,
)


class StructureDisplayTests(SimpleTestCase):
    def test_normalize_core_nouns_with_tier(self):
        raw = [
            {"term": "痕迹", "definition": "人心留下的印记", "tier": "root"},
            {"term": "裂口", "definition": "痕迹的爆发点", "tier": "mechanism"},
        ]
        nouns = normalize_core_nouns(raw)
        self.assertEqual(nouns[0]["tierLabel"], "根概念")
        self.assertEqual(nouns[1]["tier"], "mechanism")

    def test_build_world_self_check(self):
        from apps.creation.display.structure_display import build_world_self_check

        wv = {
            "settingSummary": "现代都市豪门职场，暗藏身份反转与复仇主线，能力来自家族血脉觉醒。",
            "rootRules": ["得到多少就要失去多少", "身份秘密一旦公开将引发连锁反应"],
        }
        nouns = [
            {"term": "a", "definition": "1", "tier": "root"},
            {"term": "b", "definition": "2", "tier": "mechanism"},
            {"term": "c", "definition": "3"},
        ]
        checks = build_world_self_check(wv, nouns)
        self.assertEqual(len(checks), 8)
        self.assertTrue(any(c["key"] == "nounTier" and c["passed"] for c in checks))

    def test_normalize_core_nouns_from_strings(self):
        raw = [
            "猫薄荷：一种让猫瞬间放松的神秘植物",
            "星尘契约：主角与异界生物的绑定规则",
        ]
        nouns = normalize_core_nouns(raw)
        self.assertEqual(len(nouns), 2)
        self.assertEqual(nouns[0]["term"], "猫薄荷")
        self.assertIn("神秘植物", nouns[0]["definition"])

    def test_normalize_dream_indicators_non_schema_keys(self):
        raw = {
            "fantasyAppeal": {"score": 8, "notes": "幻想元素充足"},
            "dreamPotential": {"score": 7, "description": "梦境感强"},
            "emotionalDepth": "情感层次丰富",
        }
        dream = normalize_dream_indicators(raw)
        self.assertEqual(dream["scores"]["fantasyAppeal"], 8)
        self.assertIn("幻想吸引力", dream["notes"])
        self.assertIn("情感深度", dream["notes"])

    def test_build_structure_plan_view_includes_normalized_worldview(self):
        project = SimpleNamespace(episode_count=80, theme="sweet-pet", reference_work="")
        payload = {
            "totalEpisodes": 80,
            "worldview": {
                "settingSummary": "现代都市职场，暗藏奇幻规则。",
                "timePeriod": "当代",
                "locationType": "urban",
                "rootRules": ["规则一", "规则二"],
                "coreNouns": ["猫薄荷：神秘植物"],
                "dreamIndicators": {
                    "fantasyAppeal": {"score": 8, "notes": "幻想感足"},
                },
            },
            "sixStagePlan": [
                {
                    "stageIndex": 1,
                    "stageName": "开篇",
                    "startEpisode": 1,
                    "endEpisode": 10,
                    "coreTask": "建立冲突",
                }
            ],
            "rhythmCurve": [],
            "keyReversalPoints": [],
            "coreStoryArc": {},
            "structuralConstraints": {},
        }
        normalized = normalize_structure_payload(dict(payload))
        view = build_structure_plan_view(normalized, project)
        wv = view["worldview"]
        self.assertEqual(len(wv["coreNouns"]), 1)
        self.assertEqual(wv["coreNouns"][0]["term"], "猫薄荷")
        self.assertEqual(wv["settingSummary"], "现代都市职场，暗藏奇幻规则。")
        self.assertNotIn("worldSelfCheck", wv)
        self.assertNotIn("dreamScores", wv)
        self.assertNotIn("dreamNotes", wv)
        self.assertEqual(view["worldValidationLog"], portal_gate_log(build_world_validation_log(normalized)))
        self.assertNotIn("referenceLibrary", view)
        rev = (view.get("keyReversalPoints") or [None])[0]
        if rev:
            self.assertNotIn("techniqueCode", rev)
            self.assertNotIn("patternName", rev)
        rhythm = (view.get("rhythmCurve") or [None])[0]
        if rhythm:
            self.assertNotIn("suggestedHooks", rhythm)

    def test_validate_worldview_issues_matches_sub_world_rules(self):
        issues = validate_worldview_issues({"worldview": {"settingSummary": "短", "rootRules": []}})
        self.assertTrue(any("settingSummary" in i for i in issues))
        self.assertTrue(any("rootRules" in i for i in issues))

    def test_build_world_validation_log_backfills_for_legacy_payload(self):
        payload = {
            "worldview": {
                "settingSummary": "现代都市豪门集团职场逆袭背景设定完整。",
                "rootRules": ["规则一", "规则二"],
                "dreamIndicators": {
                    "absoluteSafety": 8,
                    "efficientSatisfaction": 7,
                    "enhancedRealism": 8,
                },
            }
        }
        log = build_world_validation_log(payload)
        self.assertTrue(log["passed"])
        self.assertEqual(log["checker"], "sub-world")

    def test_finalize_dream_indicators_fills_missing_schema_scores(self):
        from apps.creation.display.structure_display import finalize_dream_indicators

        wv = {
            "dreamIndicators": {
                "fantasyAppeal": {"score": 8, "notes": "幻想感足"},
            }
        }
        out = finalize_dream_indicators(wv)
        self.assertEqual(out["absoluteSafety"], 7)
        self.assertEqual(out["efficientSatisfaction"], 8)
        self.assertGreaterEqual(out["enhancedRealism"], 6)
        self.assertGreaterEqual(out["absoluteSafety"], 6)
        self.assertGreaterEqual(out["efficientSatisfaction"], 6)

    def test_finalize_dream_indicators_empty_input(self):
        from apps.creation.display.structure_display import finalize_dream_indicators

        wv = {}
        out = finalize_dream_indicators(wv)
        self.assertEqual(out["absoluteSafety"], 7)
        self.assertEqual(out["efficientSatisfaction"], 8)
        self.assertGreaterEqual(out["enhancedRealism"], 6)

    def test_normalize_structure_payload_sets_world_validation_log(self):
        payload = {
            "worldview": {
                "settingSummary": "现代都市豪门集团职场逆袭背景设定完整。",
                "rootRules": ["规则一", "规则二"],
                "dreamIndicators": {"absoluteSafety": 8, "efficientSatisfaction": 7, "enhancedRealism": 8},
            },
        }
        out = normalize_structure_payload(dict(payload))
        self.assertIn("worldValidationLog", out)
        self.assertTrue(out["worldValidationLog"]["passed"])

    def test_normalize_structure_payload_backfills_missing_dream_scores(self):
        payload = {
            "worldview": {
                "settingSummary": "现代都市豪门集团职场逆袭背景设定完整。",
                "rootRules": ["规则一", "规则二"],
            },
        }
        out = normalize_structure_payload(dict(payload))
        di = out["worldview"]["dreamIndicators"]
        self.assertGreaterEqual(di["absoluteSafety"], 6)
        self.assertGreaterEqual(di["efficientSatisfaction"], 6)
        self.assertGreaterEqual(di["enhancedRealism"], 6)

    def test_normalize_reversal_type_maps_chinese_labels(self):
        self.assertEqual(normalize_reversal_type("情感反转"), "relationship-reversal")
        self.assertEqual(normalize_reversal_type("契约设定"), "relationship-reversal")
        self.assertEqual(normalize_reversal_type("身份暗示反转"), "identity-reveal")
        self.assertEqual(normalize_reversal_type("identity-reveal"), "identity-reveal")

    def test_normalize_key_reversal_points_in_payload(self):
        payload = {
            "keyReversalPoints": [
                {"episodeNumber": 3, "reversalType": "误会铺垫", "description": "误会"},
                {"episodeNumber": 8, "reversalType": "hidden-truth", "description": "真相"},
            ],
        }
        normalize_key_reversal_points(payload)
        self.assertEqual(payload["keyReversalPoints"][0]["reversalType"], "hidden-truth")
        self.assertEqual(payload["keyReversalPoints"][1]["reversalType"], "hidden-truth")

    def test_normalize_structure_payload_sets_node_name_and_reversal_types(self):
        payload = {
            "keyReversalPoints": [{"episodeNumber": 1, "reversalType": "态度反转"}],
            "worldview": {
                "settingSummary": "现代都市豪门集团职场逆袭背景设定完整。",
                "rootRules": ["规则一", "规则二"],
                "dreamIndicators": {"absoluteSafety": 8, "efficientSatisfaction": 7, "enhancedRealism": 8},
            },
        }
        out = normalize_structure_payload(dict(payload))
        self.assertEqual(out["nodeName"], "结构与世界观节点")
        self.assertEqual(out["keyReversalPoints"][0]["reversalType"], "relationship-reversal")

    def test_normalize_rhythm_block_from_episode_group(self):
        block = normalize_rhythm_block(
            {
                "episodeGroup": "Ep 1-10",
                "intensityLevel": 5,
                "keyEvents": ["事件"],
            }
        )
        self.assertEqual(block["episodeRange"], "1-10")
        self.assertEqual(block["episodeStart"], 1)
        self.assertEqual(block["episodeEnd"], 10)

    def test_normalize_rhythm_curve_dedupes_by_episode_range(self):
        payload = {
            "rhythmCurve": [
                {"episodeGroup": "Ep 1-10", "intensityLevel": 5},
                {"episodeRange": "1-10", "intensityLevel": 6, "notes": "更新"},
                {"episodeGroup": "Ep 11-20", "intensityLevel": 7},
            ],
        }
        from apps.creation.display.structure_display import normalize_rhythm_curve

        normalize_rhythm_curve(payload)
        self.assertEqual(len(payload["rhythmCurve"]), 2)
        self.assertEqual(payload["rhythmCurve"][0]["episodeRange"], "1-10")

    def test_normalize_structure_payload_cleans_dream_notes_punctuation(self):
        payload = {
            "worldview": {
                "settingSummary": "现代都市豪门集团职场逆袭背景设定完整。",
                "rootRules": ["规则一", "规则二"],
                "dreamIndicators": {
                    "absoluteSafety": 7,
                    "efficientSatisfaction": 8,
                    "enhancedRealism": 6,
                    "notes": "奇幻调味，不过度喧宾夺主。；主线甜度密集。；冲突强度适中。",
                },
            },
        }
        out = normalize_structure_payload(dict(payload))
        notes = out["worldview"]["dreamIndicators"]["notes"]
        self.assertNotIn("。；", notes)
        self.assertIn("；", notes)
        self.assertTrue(out["worldValidationLog"]["passed"])

    def test_build_structure_plan_view_exposes_act_structure(self):
        project = SimpleNamespace(episode_count=80, theme="urban-romance", reference_work="")
        payload = {
            "workingTitle": "测试剧名",
            "totalEpisodes": 80,
            "actStructure": {
                "actCount": 4,
                "themeCode": "urban-romance",
                "reversalPoints": [
                    {"label": "身份揭晓", "episode": 12, "description": "女主真实身份曝光"},
                    "中段危机",
                ],
            },
            "worldview": {"settingSummary": "现代都市背景设定完整可拍。"},
        }
        out = build_structure_plan_view(payload, project)
        act = out["actStructure"]
        self.assertEqual(act["actCount"], 4)
        self.assertEqual(act["themeCode"], "urban-romance")
        self.assertEqual(act["themeCodeLabel"], "都市情感")
        self.assertEqual(len(act["reversalPoints"]), 2)
        self.assertEqual(act["reversalPoints"][0]["label"], "身份揭晓")
        self.assertEqual(act["reversalPoints"][1]["label"], "中段危机")


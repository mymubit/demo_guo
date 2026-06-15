# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.orchestration.agent_payload import (
    coerce_outline_chunk,
    coerce_script_chunk,
    extract_fixer_patch,
    fixer_patch_meaningful,
    unwrap_llm_payload,
)
from apps.creation.character_enrichment import normalize_character_bible_payload


class AgentPayloadTests(SimpleTestCase):
    def test_unwrap_series_outline_wrapper(self):
        raw = {"seriesOutline": {"totalEpisodes": 10, "episodes": [{"episodeNumber": 1}]}}
        out = unwrap_llm_payload("plan-fixer", raw)
        self.assertEqual(out["totalEpisodes"], 10)
        self.assertEqual(len(out["episodes"]), 1)

    def test_coerce_outline_single_episode(self):
        raw = {"episodeNumber": 3, "oneLineSummary": "测试梗概" * 10}
        out = coerce_outline_chunk(raw)
        self.assertEqual(len(out["episodes"]), 1)
        self.assertEqual(out["episodes"][0]["episodeNumber"], 3)

    def test_coerce_script_episodes_list(self):
        raw = [{"episodeNumber": 1, "scenes": []}]
        out = coerce_script_chunk(raw)
        self.assertEqual(len(out["episodes"]), 1)

    def test_fixer_patch_meaningful_rejects_empty(self):
        self.assertFalse(fixer_patch_meaningful({}))
        self.assertFalse(fixer_patch_meaningful({"validationIssues": ["x"]}))
        self.assertTrue(fixer_patch_meaningful({"creativePlan": {"hookDiversity": {}}}))

    def test_extract_fixer_patch_nested(self):
        patch = {"seriesOutline": {"creativePlan": {"notes": "ok"}}}
        out = extract_fixer_patch("plan-fixer", patch)
        self.assertIn("creativePlan", out)


class CharacterEnrichmentTests(SimpleTestCase):
    def test_flat_characters_bucketed(self):
        sparse = {
            "characters": [
                {"name": "林晓", "roleType": "protagonist-female", "coreMotivation": "复仇"},
                {"name": "赵婆", "roleType": "antagonist-female", "coreMotivation": "夺权"},
                {"name": "阿青", "roleType": "supporting", "coreMotivation": "助攻"},
            ],
            "relationships": [
                {
                    "characterAName": "林晓",
                    "characterBName": "赵婆",
                    "relationType": "enemy",
                    "description": "婆媳对立",
                }
            ],
        }
        out = normalize_character_bible_payload(sparse, theme="family-revenge")
        self.assertEqual(len(out["protagonists"]), 1)
        self.assertEqual(len(out["antagonists"]), 1)
        self.assertGreaterEqual(len(out["relationshipMap"]), 1)
        self.assertTrue(out["protagonists"][0].get("id"))

    def test_resolve_relationship_from_description_only(self):
        sparse = {
            "characters": [
                {"name": "林小雨", "roleType": "protagonist-female"},
                {"name": "陈晓晓", "roleType": "supporting"},
                {"name": "夜白", "roleType": "protagonist-male"},
                {"name": "黑渊", "roleType": "antagonist-male"},
            ],
            "relationshipMap": [
                {
                    "relationType": "闺蜜",
                    "description": "陈晓晓是林小雨的情感顾问，帮她走出失恋阴影",
                },
                {
                    "relationType": "仇敌",
                    "description": "黑渊诅咒夜白，两人势不两立",
                },
            ],
        }
        out = normalize_character_bible_payload(sparse)
        rels = out["relationshipMap"]
        self.assertEqual(len(rels), 2)
        self.assertEqual(rels[0]["characterAName"], "陈晓晓")
        self.assertEqual(rels[0]["characterBName"], "林小雨")
        self.assertEqual(rels[1]["characterAName"], "黑渊")
        self.assertEqual(rels[1]["characterBName"], "夜白")

    def test_build_character_bible_view_maps_unknown_relation_slug(self):
        from apps.creation.display.character_display import build_character_bible_view

        payload = {
            "characters": [
                {"id": "a", "name": "甲", "roleType": "protagonist-female"},
                {"id": "b", "name": "乙", "roleType": "antagonist-male"},
            ],
            "relationshipMap": [
                {
                    "characterAId": "a",
                    "characterBId": "b",
                    "characterAName": "甲",
                    "characterBName": "乙",
                    "relationType": "romantic-lover",
                    "description": "两人曾是恋人，如今反目。",
                }
            ],
        }
        out = build_character_bible_view(payload)
        rel = out["relationships"][0]
        self.assertEqual(rel["relationTypeLabel"], "恋人")

    def test_build_character_bible_view_maps_role_and_archetype_labels(self):
        from apps.creation.display.character_display import build_character_bible_view

        payload = {
            "characters": [
                {
                    "name": "林建国",
                    "roleType": "antagonist",
                    "gender": "male",
                    "age": 55,
                    "archetypeCode": "selfish-patriarch",
                }
            ],
        }
        out = build_character_bible_view(payload)
        char = out["characters"][0]
        self.assertEqual(char["roleTypeLabel"], "男反派")
        self.assertEqual(char["archetypeLabel"], "")

    def test_build_character_bible_view_maps_speech_patterns(self):
        from apps.creation.display.character_display import build_character_bible_view

        payload = {
            "characters": [
                {
                    "name": "林小雨",
                    "roleType": "protagonist-female",
                    "speechPatterns": ["喜欢反问", "省略主语"],
                }
            ],
        }
        out = build_character_bible_view(payload)
        char = out["characters"][0]
        self.assertEqual(char["speechPatterns"], ["喜欢反问", "省略主语"])

    def test_build_character_bible_view_maps_voice_and_behavior(self):
        from apps.creation.display.character_display import build_character_bible_view

        payload = {
            "characters": [
                {
                    "name": "周柠",
                    "roleType": "protagonist-female",
                    "voiceProfile": {
                        "label": "冷感御姐音",
                        "pitch": "中",
                        "pace": "中偏慢",
                        "summary": "冷感御姐音（音高中 · 语速中偏慢 · AI配音参考）",
                    },
                    "behaviorProfile": {
                        "catchphrase": "我警告你啊",
                        "habit": "不耐烦时会跺脚",
                        "languageStyle": ["说话直接"],
                        "decisionLogic": ["优先考虑感受"],
                    },
                    "visualAnchor": {
                        "distinctiveFeatures": "高挑短发",
                        "clothingStyle": "利落西装",
                        "consistencyRules": ["保持冷感妆容"],
                    },
                }
            ],
        }
        out = build_character_bible_view(payload)
        char = out["characters"][0]
        self.assertEqual(char["voiceProfile"]["label"], "冷感御姐音")
        self.assertEqual(char["behaviorProfile"]["catchphrase"], "我警告你啊")
        self.assertEqual(char["visualAnchor"]["clothingStyle"], "利落西装")

    def test_build_character_bible_view_maps_creative_dna_and_perspectives(self):
        from apps.creation.display.character_display import build_character_bible_view

        payload = {
            "creativeDna": {
                "antiClicheElements": [{"code": "R-01", "label": "腹黑女主", "effect": "打破傻白甜"}],
                "uniqueSettings": [{"code": "U-02", "label": "深夜便利店", "example": "主要场景"}],
                "aiAuthenticityNotes": ["每个角色必须有明显缺点"],
            },
            "relationshipMap": [
                {
                    "characterAName": "林小雨",
                    "characterBName": "夜白",
                    "relationType": "romantic-lover",
                    "description": "恋人关系",
                    "perspectiveA": "依赖又试探",
                    "perspectiveB": "克制守护",
                    "coreConflict": "身份秘密",
                    "hiddenTension": "契约未解除",
                }
            ],
            "characters": [
                {"id": "lin", "name": "林小雨", "roleType": "protagonist-female"},
                {"id": "ye", "name": "夜白", "roleType": "protagonist-male"},
            ],
        }
        out = build_character_bible_view(payload)
        self.assertEqual(out["creativeDna"]["antiClicheElements"][0]["code"], "R-01")
        rel = out["relationships"][0]
        self.assertEqual(rel["perspectiveA"], "依赖又试探")
        self.assertEqual(rel["coreConflict"], "身份秘密")

    def test_dedupe_relationship_map_and_relationships(self):
        from apps.creation.display.character_display import dedupe_relationships

        rows = [
            {
                "characterAName": "陈晓晓",
                "characterBName": "林小雨",
                "relationType": "闺蜜",
                "description": "情感顾问",
            },
            {
                "characterAName": "林小雨",
                "characterBName": "陈晓晓",
                "relationType": "闺蜜",
                "description": "情感顾问",
            },
        ]
        self.assertEqual(len(dedupe_relationships(rows)), 1)

        sparse = {
            "characters": [
                {"name": "陈晓晓", "roleType": "supporting"},
                {"name": "林小雨", "roleType": "protagonist-female"},
            ],
            "relationshipMap": [
                {"characterAName": "陈晓晓", "characterBName": "林小雨", "description": "闺蜜线"},
            ],
            "relationships": [
                {"characterAName": "陈晓晓", "characterBName": "林小雨", "description": "闺蜜线"},
            ],
        }
        out = normalize_character_bible_payload(sparse)
        self.assertEqual(len(out["relationshipMap"]), 1)

    def test_infer_friend_and_lover_endpoints(self):
        from apps.creation.display.character_display import resolve_relationship_endpoints

        chars = [
            {"id": "c1", "name": "林小雨", "roleType": "protagonist-female"},
            {"id": "c2", "name": "苏晴", "roleType": "supporting"},
            {"id": "c3", "name": "夜白", "roleType": "protagonist-male"},
            {"id": "c4", "name": "暗影", "roleType": "antagonist-male"},
        ]
        friend = resolve_relationship_endpoints(
            {
                "characterAName": "苏晴",
                "relationType": "闺蜜",
                "description": "苏晴是女主林小雨的闺蜜",
            },
            chars,
        )
        self.assertEqual(friend["characterBName"], "林小雨")

        lover = resolve_relationship_endpoints(
            {
                "relationType": "宠物主人→恋人",
                "description": "女主将猫当宠物，后发现他是王子",
            },
            chars,
        )
        self.assertEqual(lover["characterAName"], "林小雨")
        self.assertEqual(lover["characterBName"], "夜白")

    def test_fuzzy_name_resolves_character_id(self):
        from apps.creation.display.character_display import resolve_relationship_endpoints

        chars = [
            {"id": "c1", "name": "林小雨", "roleType": "protagonist-female"},
            {"id": "c2", "name": "赵婆婆", "roleType": "antagonist-female"},
        ]
        row = resolve_relationship_endpoints(
            {"characterAName": "小雨", "characterBName": "赵婆", "description": "婆媳对立"},
            chars,
        )
        self.assertEqual(row["characterAId"], "c1")
        self.assertEqual(row["characterBId"], "c2")

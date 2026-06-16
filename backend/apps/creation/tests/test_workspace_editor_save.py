# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import Project
from apps.creation.workspace.workspace_editor import apply_editor_save

User = get_user_model()


class WorkspaceEditorSaveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900004402", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="编辑保存测试",
            theme="sweet-pet",
            core_idea="原始创意",
            episode_count=80,
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        save_artifact(
            self.project,
            "project_brief",
            {
                "workingTitle": "编辑保存测试",
                "theme": "sweet-pet",
                "episodeCount": 80,
                "coreHook": "原始创意",
            },
        )
        save_artifact(
            self.project,
            "structure_plan",
            {
                "workingTitle": "结构标题",
                "totalEpisodes": 80,
                "worldview": {"settingSummary": "现代都市"},
                "sixStagePlan": [{"stageIndex": 1, "stageName": "起", "coreTask": "开局"}],
            },
        )
        save_artifact(
            self.project,
            "character_bible",
            {
                "protagonists": [
                    {
                        "id": "hero-1",
                        "name": "林晚",
                        "oneLineSummary": "隐忍女主",
                        "background": "普通家庭",
                    }
                ],
                "antagonists": [],
                "supportingRoles": [],
            },
        )

    def test_brief_save_theme_display_and_episode_count(self):
        apply_editor_save(
            self.project,
            1,
            {
                "fields": [
                    {"key": "themeDisplayName", "value": "甜宠逆袭"},
                    {"key": "episodeCount", "value": "10"},
                    {"key": "coreHook", "value": "新核心钩子"},
                ]
            },
        )
        self.project.refresh_from_db()
        brief = get_artifact(self.project, "project_brief") or {}
        self.assertEqual(brief.get("themeDisplayName"), "甜宠逆袭")
        self.assertEqual(brief.get("episodeCount"), 10)
        self.assertEqual(self.project.episode_count, 10)
        self.assertEqual(brief.get("coreHook"), "新核心钩子")

    def test_structure_save_worldview(self):
        apply_editor_save(
            self.project,
            2,
            {
                "structurePlan": {
                    "worldview": {"settingSummary": "架空古代"},
                    "workingTitle": "新结构名",
                }
            },
        )
        sp = get_artifact(self.project, "structure_plan") or {}
        self.assertEqual(sp.get("workingTitle"), "新结构名")
        self.assertEqual((sp.get("worldview") or {}).get("settingSummary"), "架空古代")

    def test_character_legacy_name_patch(self):
        apply_editor_save(
            self.project,
            3,
            {
                "characters": [
                    {
                        "id": "hero-1",
                        "name": "林晚改",
                        "oneLineSummary": "逆袭女主",
                        "personality": "外柔内刚",
                    }
                ]
            },
        )
        bible = get_artifact(self.project, "character_bible") or {}
        hero = (bible.get("protagonists") or [])[0]
        self.assertEqual(hero.get("name"), "林晚改")
        self.assertEqual(hero.get("oneLineSummary"), "逆袭女主")
        self.assertEqual(hero.get("surfacePersonality"), "外柔内刚")
        self.assertIn("characterGateLog", bible)
        self.assertIn("passed", bible["characterGateLog"])

    def test_character_gate_acknowledge(self):
        from apps.creation.workspace.workspace_service import acknowledge_quality_alert

        save_artifact(
            self.project,
            "character_bible",
            {
                "protagonists": [
                    {
                        "id": "hero-1",
                        "name": "王德顺",
                        "roleType": "protagonist",
                        "age": 62,
                        "oneLineSummary": "老渔夫",
                        "coreMotivation": "守住手艺",
                        "personality": "固执",
                        "background": "20岁离开渔村",
                    }
                ],
                "antagonists": [],
                "supportingRoles": [],
                "characterGateLog": {
                    "passed": False,
                    "issues": ["角色「王德顺」年龄字段为 62 岁，但文本中出现 20 岁"],
                },
            },
        )
        result = acknowledge_quality_alert(self.project, 3, "character-gate")
        self.assertEqual(result["status"], "acknowledged")
        bible = get_artifact(self.project, "character_bible") or {}
        self.assertTrue(bible["characterGateLog"].get("userAcknowledgedAt"))


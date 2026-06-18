# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.workspace.workspace_content import (
    CONTENT_AGENT_GENERATED,
    CONTENT_SKELETON,
    CONTENT_USER_CONFIRMED,
    NODE_STATUS_COMPLETED,
    NODE_STATUS_PENDING,
    ensure_brief_seed_enriched,
    should_emit_quality_alert,
    skill_content_kind,
)
from apps.creation.models import Project

User = get_user_model()


class WorkspaceContentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900005501", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="甜宠测试",
            theme="sweet-pet",
            core_idea="一句话梗概：霸总追妻\n\n核心冲突：误会分离\n\n情绪基调：甜虐交织",
            episode_count=80,
            pipeline_mode=Project.MODE_WORKSPACE,
        )

    def test_ensure_brief_seed_enriched_backfills_internal_fields(self):
        save_artifact(
            self.project,
            "project_brief",
            {
                "theme": "sweet-pet",
                "themeDisplayName": "甜宠",
                "coreHook": self.project.core_idea,
                "episodeCount": 80,
            },
        )
        ensure_brief_seed_enriched(self.project)
        brief = get_artifact(self.project, "project_brief") or {}
        self.assertTrue(brief.get("seedEnriched"))
        self.assertIsInstance(brief.get("trendFormula"), dict)

    def test_ensure_brief_materializes_from_project_when_artifact_missing(self):
        ensure_brief_seed_enriched(self.project)
        brief = get_artifact(self.project, "project_brief") or {}
        self.assertTrue(brief.get("coreHook") or brief.get("coreIdea"))
        self.assertEqual(brief.get("theme"), "sweet-pet")
        self.assertIsInstance(brief.get("writingBrief"), dict)
        self.assertTrue((brief.get("writingBrief") or {}).get("tone") or (brief.get("writingBrief") or {}).get("notes"))

    def test_skill_content_kind_user_confirmed_for_brief(self):
        payload = {"theme": "sweet-pet", "coreHook": "测试", "seedEnriched": True}
        kind = skill_content_kind(1, payload, has_content=True, node_status=NODE_STATUS_PENDING)
        self.assertEqual(kind, CONTENT_USER_CONFIRMED)

    def test_skill_content_kind_agent_generated_after_brief_agent(self):
        payload = {"theme": "sweet-pet", "coreHook": "测试", "agentEnriched": True}
        kind = skill_content_kind(1, payload, has_content=True, node_status=NODE_STATUS_COMPLETED)
        self.assertEqual(kind, CONTENT_AGENT_GENERATED)

    def test_skill_content_kind_outline_skeleton(self):
        payload = {"skeletonReady": True, "stageBlocks": [{"label": "起"}], "episodes": []}
        kind = skill_content_kind(4, payload, has_content=True, node_status=NODE_STATUS_PENDING)
        self.assertEqual(kind, CONTENT_SKELETON)

    def test_should_not_emit_brief_incomplete(self):
        self.assertFalse(should_emit_quality_alert(1, "brief-incomplete"))

    def test_character_gate_only_after_agent_completed(self):
        self.assertFalse(
            should_emit_quality_alert(
                3,
                "character-gate",
                node_status=NODE_STATUS_PENDING,
            )
        )
        self.assertTrue(
            should_emit_quality_alert(
                3,
                "character-gate",
                node_status=NODE_STATUS_COMPLETED,
            )
        )

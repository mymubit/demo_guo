# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project, ProjectFusionArtifact
from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.models import DramaProject, DramaRoleExecution
from apps.drama.presentation.presenters import present_artifact, present_episode_scripts
from apps.drama.presentation.schema_presenters import SCHEMA_PRESENTERS
from apps.drama.presentation.service import build_execution_output_views
from apps.drama.serializers import DramaRoleExecutionSerializer

User = get_user_model()


class DramaPresentationTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = User.objects.create_user(phone="13900009902", password="test-pass-123")
        pid = "22222222-2222-2222-2222-222222222222"
        self.creation = Project.objects.create(
            id=pid,
            user=self.user,
            title="presentation-test",
            theme="overbearing-ceo",
            core_idea="测试",
            episode_count=3,
        )
        self.drama = DramaProject.objects.create(
            id=pid,
            project_id=pid,
            user=self.user,
            title="presentation-drama",
            genre_code="overbearing-ceo",
            total_episodes=3,
            track_mode="fast",
        )

    def test_project_brief_presentation_uses_blocks_not_editor_mode(self):
        payload = {
            "data": {
                "core_idea": "甜宠逆袭",
                "genre_positioning": "霸总甜宠",
                "differentiated_selling_points": ["卖点A", "卖点B"],
            }
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        self.assertEqual(view["schema_version"], "project-brief.v1")
        self.assertTrue(view["blocks"])
        self.assertNotIn("mode", view)
        self.assertEqual(view["blocks"][0]["type"], "hero")

    def test_episode_scripts_renders_beats(self):
        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scripts": [
                        {
                            "sceneHeader": "1-1 夜 内 宴会厅",
                            "action": "△动作",
                            "dialogue": "角色：台词",
                        }
                    ],
                }
            ]
        }
        view = present_episode_scripts("episode_scripts", payload)
        block = view["blocks"][0]
        self.assertEqual(block["type"], "script_episodes")
        self.assertEqual(block["episodes"][0]["beats"][0]["sceneHeader"], "1-1 夜 内 宴会厅")

    def test_market_analysis_presentation(self):
        payload = {
            "data": {
                "theme_heat_rating": {"current_popularity_score": 92, "core_hot_labels": ["甜宠"]},
                "competitive_product_analysis": [
                    {"competitor_name": "竞品A", "core_score": 86, "defect": "节奏慢"}
                ],
                "topic_suggestion": {
                    "optimization_direction": ["强化开场"],
                    "estimated_market_performance": "预计播放1200万",
                },
                "爆款特征_matching_degree": 94,
            }
        }
        view = present_artifact("market_analysis", "market-analysis.v1", payload)
        types = [b["type"] for b in view["blocks"]]
        self.assertIn("metrics", types)
        self.assertIn("cards", types)
        self.assertIn("list", types)

    def test_project_brief_unwraps_project_content(self):
        payload = {
            "project_content": {
                "core_idea": "甜宠逆袭",
                "genre_positioning": "霸总甜宠",
            }
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        self.assertTrue(view["blocks"])
        self.assertEqual(view["blocks"][0]["type"], "hero")

    def test_serializer_output_views(self):
        save_artifact(
            self.creation,
            "project_brief",
            {"data": {"core_idea": "测试剧", "genre_positioning": "甜宠"}},
        )
        exec_row = DramaRoleExecution.objects.create(
            drama_project=self.drama,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.SUCCESS,
            output_artifacts={"project_brief": {"data": {"core_idea": "测试剧"}}},
        )
        data = DramaRoleExecutionSerializer(exec_row).data
        view = data["output_views"]["project_brief"]
        self.assertIn("blocks", view)
        self.assertEqual(build_execution_output_views(exec_row)["project_brief"]["artifact_key"], "project_brief")

    def test_all_schema_presenters_registered(self):
        schemas = {
            (role.get("output_contract") or {}).get("schema_version")
            for role in DRAMA_ROLE_DEFAULTS
            if (role.get("output_contract") or {}).get("schema_version")
        }
        self.assertEqual(schemas, set(SCHEMA_PRESENTERS.keys()))

    def test_episode_scripts_script_content(self):
        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scriptContent": [
                        "1-1 日 内 宴会厅",
                        "△动作描写",
                        "角色（语气）：台词内容",
                    ],
                }
            ]
        }
        view = present_episode_scripts("episode_scripts", payload)
        beats = view["blocks"][0]["episodes"][0]["beats"]
        self.assertEqual(beats[0]["sceneHeader"], "1-1 日 内 宴会厅")
        self.assertTrue(any(b["action"].startswith("△") for b in beats))
        self.assertTrue(any("台词" in b["dialogue"] for b in beats))

    def test_compliance_report_flat_format(self):
        payload = {
            "overall_compliance_decision": "approved",
            "p0_check_result": "pass",
            "nine_dimension_risk_check": {"values": "pass", "horror": "pass"},
            "remark": "合规通过",
        }
        view = present_artifact("compliance_report", "compliance-report.v1", payload)
        self.assertEqual(view["blocks"][0]["type"], "checks")
        self.assertTrue(view["blocks"][0]["passed"])

    def test_storyboard_chinese_fields(self):
        payload = {
            "storyboard_list": [
                {
                    "镜号": 1,
                    "场景": "宴会厅",
                    "景别": "特写",
                    "画面内容(△开头)": "△甩退婚纸",
                }
            ]
        }
        view = present_artifact("storyboard", "storyboard.v1", payload)
        card = view["blocks"][0]["items"][0]
        self.assertIn("宴会厅", card["title"])

    def test_expert_project_artifacts_have_blocks(self):
        expert = DramaProject.objects.filter(title="e2e-drama-expert").first()
        if not expert:
            self.skipTest("e2e-drama-expert 项目不存在")
        artifacts = ProjectFusionArtifact.objects.filter(project_id=expert.project_id)
        self.assertGreater(artifacts.count(), 0)
        for artifact in artifacts:
            schema = None
            for role in DRAMA_ROLE_DEFAULTS:
                if role.get("default_output_artifact_key") == artifact.artifact_key:
                    schema = (role.get("output_contract") or {}).get("schema_version")
                    break
            if not schema:
                continue
            view = present_artifact(artifact.artifact_key, schema, artifact.payload)
            self.assertTrue(
                view["blocks"],
                msg=f"{artifact.artifact_key} 展示 blocks 为空",
            )
            types = {b["type"] for b in view["blocks"]}
            self.assertFalse(types == {"kv"} or not types, msg=f"{artifact.artifact_key} 仅 generic kv")

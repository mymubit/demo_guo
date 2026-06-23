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
from apps.drama.presentation.service import build_execution_output_views, build_role_output_views
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
            "project_content": {
                "core_idea": "甜宠逆袭",
                "genre_positioning": "霸总甜宠",
                "three_differentiated_selling_points": ["卖点A", "卖点B"],
            }
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        self.assertEqual(view["schema_version"], "project-brief.v1")
        self.assertTrue(view["blocks"])
        self.assertNotIn("mode", view)
        self.assertEqual(view["blocks"][0]["type"], "hero")

    def test_project_brief_three_differentiated_selling_points(self):
        payload = {
            "project_content": {
                "core_idea": "甜宠逆袭",
                "three_differentiated_selling_points": ["卖点A详细描述", "卖点B", "卖点C"],
            }
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        corpus = str(view["blocks"])
        self.assertIn("卖点A详细描述", corpus)
        list_blocks = [b for b in view["blocks"] if b["type"] == "list"]
        self.assertTrue(any("卖点" in str(b.get("title", "")) for b in list_blocks))

    def test_episode_scripts_renders_beats(self):
        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scriptContent": "1-1 夜 内 宴会厅\n△动作\n角色：台词",
                }
            ]
        }
        view = present_episode_scripts("episode_scripts", payload)
        block = view["blocks"][0]
        self.assertEqual(block["type"], "script_episodes")
        self.assertEqual(block["episodes"][0]["beats"][0]["sceneHeader"], "1-1 夜 内 宴会厅")

    def test_market_analysis_presentation(self):
        payload = {
            "爆款特征_matching_degree": 94,
            "data": {
                "theme_heat_rating": {"current_popularity_score": 92, "core_hot_labels": ["甜宠"]},
                "competitive_product_analysis": [
                    {"competitor_name": "竞品A", "core_score": 86, "defect": "节奏慢"}
                ],
                "topic_suggestion": {
                    "optimization_direction": ["强化开场"],
                    "estimated_market_performance": "预计播放1200万",
                },
            },
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
            {"project_content": {"core_idea": "测试剧", "genre_positioning": "甜宠"}},
        )
        exec_row = DramaRoleExecution.objects.create(
            drama_project=self.drama,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.SUCCESS,
            output_artifacts={"project_brief": {"project_content": {"core_idea": "测试剧"}}},
        )
        data = DramaRoleExecutionSerializer(exec_row).data
        view = data["output_views"]["project_brief"]
        self.assertIn("blocks", view)
        self.assertEqual(build_execution_output_views(exec_row)["project_brief"]["artifact_key"], "project_brief")

    def test_build_role_output_views_empty_when_snapshot_missing(self):
        views = build_role_output_views({}, agent_id="drama.character-designer")
        self.assertEqual(views, {})

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

    def test_episode_scripts_string_script_content_with_checkpoint(self):
        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scriptContent": (
                        "1-1 日 内 家政招聘办公室\n"
                        "△【中景】招聘现场\n"
                        "刘梅（满意）：你的履历我看过了。\n"
                        "阿晴：我回来了。\n"
                        "记忆检查点：苏晴潜入老宅，复仇计划启动。"
                    ),
                }
            ]
        }
        view = present_episode_scripts("episode_scripts", payload)
        episode = view["blocks"][0]["episodes"][0]
        self.assertEqual(episode["memoryCheckPoint"], "苏晴潜入老宅，复仇计划启动。")
        self.assertEqual(episode["sceneCount"], 1)
        self.assertTrue(any("刘梅" in b["dialogue"] for b in episode["beats"]))
        self.assertTrue(any("阿晴" in b["dialogue"] for b in episode["beats"]))
        self.assertEqual(view["blocks"][0]["total_episodes"], 1)

    def test_review_report_structured_issues(self):
        payload = {
            "passed": True,
            "pacingPassed": True,
            "issues": [
                {
                    "issueType": "格式问题",
                    "description": "刘梅的台词未标注情绪状态，不符合台词格式规范",
                    "sceneNumber": "2-1",
                    "episodeNumber": 2,
                },
                {
                    "issueType": "逻辑冗余",
                    "description": "张浩发送的消息内容与第3集3-5场景完全重复",
                    "sceneNumber": "7-5",
                    "episodeNumber": 7,
                },
            ],
        }
        view = present_artifact("review_report", "review-report.v1", payload)
        types = [b["type"] for b in view["blocks"]]
        self.assertEqual(types, ["review_overview", "review_issues"])
        overview = view["blocks"][0]
        self.assertTrue(overview["passed"])
        self.assertTrue(overview["pacing_passed"])
        self.assertEqual(overview["issue_count"], 2)
        issues = view["blocks"][1]["items"]
        self.assertEqual(issues[0]["issue_type"], "格式问题")
        self.assertEqual(issues[0]["episode_number"], "2")
        self.assertEqual(issues[0]["scene_number"], "2-1")
        self.assertIn("刘梅", issues[0]["description"])
        self.assertIn("待优化", view["summary"])

    def test_quality_report_structured_dimensions(self):
        payload = {
            "rating": "S",
            "total_score": 93,
            "fuse_triggered": False,
            "scores": {
                "人物塑造": 14,
                "对白质量": 14,
                "情绪曲线": 14,
                "格式规范": 12,
                "梦境指标": 5,
                "钩子效果": 10,
                "商业可行性": 5,
                "结构完整性": 19,
            },
            "details": {
                "format_issues": "共存在5处台词情绪标注缺失/不统一问题，最终得分12分",
                "hook_effect": "每集末尾都设置强钩子悬念，满分10分",
            },
        }
        view = present_artifact("quality_report", "quality-report.v1", payload)
        self.assertEqual(view["blocks"][0]["type"], "quality_report")
        block = view["blocks"][0]
        self.assertEqual(block["rating"], "S")
        self.assertEqual(block["total_score"], 93)
        self.assertFalse(block["fuse_triggered"])
        self.assertEqual(len(block["dimensions"]), 8)
        format_dim = next(d for d in block["dimensions"] if d["name"] == "格式规范")
        self.assertEqual(format_dim["score"], 12)
        self.assertEqual(format_dim["max_score"], 15)
        self.assertIn("5处", format_dim["detail"])
        self.assertIn("S 级", view["summary"])

    def test_compliance_report_fixture_shape_only(self):
        payload = {
            "p0_risk": [],
            "p1_risk": [],
            "p2_risk": [],
            "overall_conclusion": "全部剧集内容符合三级合规要求，无违规内容。",
            "nine_dimension_risk": [],
        }
        view = present_artifact("compliance_report", "compliance-report.v1", payload)
        block = view["blocks"][0]
        self.assertEqual(block["type"], "compliance_report")
        self.assertTrue(block["passed"])

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

    def test_world_setting_world_data_core_space(self):
        payload = {
            "world_data": {
                "era_background": "2026年沪城",
                "core_space": "竖屏近景适配的豪门宴会厅，怼脸拍强化情绪冲击",
            }
        }
        view = present_artifact("world_setting", "world-setting.v1", payload)
        block = next(b for b in view["blocks"] if b["type"] == "world_sections")
        titles = [s["title"] for s in block["sections"]]
        self.assertIn("核心场景", titles)
        self.assertIn("豪门宴会厅", str(block))


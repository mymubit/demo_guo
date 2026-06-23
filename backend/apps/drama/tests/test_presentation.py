# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project, ProjectFusionArtifact
from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.models import DramaRoleExecution
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
            title="presentation-drama",
            theme="overbearing-ceo",
            core_idea="测试",
            episode_count=3,
            track_mode="fast",
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        self.drama = self.creation

    def test_project_brief_presentation_uses_blocks_not_editor_mode(self):
        payload = {
            "core_idea": "甜宠逆袭",
            "genre_positioning": "霸总甜宠",
            "differentiated_selling_points": ["卖点A", "卖点B"],
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        self.assertEqual(view["schema_version"], "project-brief.v1")
        self.assertTrue(view["blocks"])
        self.assertNotIn("mode", view)
        self.assertEqual(view["blocks"][0]["type"], "hero")

    def test_project_brief_differentiated_selling_points(self):
        payload = {
            "core_idea": "甜宠逆袭",
            "differentiated_selling_points": ["卖点A详细描述", "卖点B", "卖点C"],
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        corpus = str(view["blocks"])
        self.assertIn("卖点A详细描述", corpus)
        list_blocks = [b for b in view["blocks"] if b["type"] == "steps"]
        self.assertTrue(any("卖点" in str(b.get("title", "")) for b in list_blocks))

    def test_project_brief_canonical_fields(self):
        payload = {
            "title": "遮天：我在废土世界逆命登顶",
            "genre_positioning": "野心逆袭穿越生存奇幻爽剧",
            "core_idea": "普通打工人穿越废土遮天世界逆袭登顶",
            "dream_index_forecast": "预估播放量破12亿",
            "target_audience": "18-35岁男性抖音用户",
            "differentiated_selling_points": ["卖点A", "卖点B", "卖点C"],
        }
        view = present_artifact("project_brief", "project-brief.v1", payload)
        corpus = str(view["blocks"])
        self.assertIn("遮天", corpus)
        self.assertIn("普通打工人", corpus)
        self.assertIn("18-35岁", corpus)
        self.assertIn("预估播放量", corpus)
        self.assertIn("卖点A", corpus)

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
            "theme_heat_rating": {"current_popularity_score": 92, "core_hot_labels": ["甜宠"]},
            "competitive_product_analysis": [
                {"competitor_name": "竞品A", "core_score": 86, "defect": "节奏慢"}
            ],
            "topic_suggestion": {
                "optimization_direction": ["强化开场"],
                "estimated_market_performance": "预计播放1200万",
            },
        }
        view = present_artifact("market_analysis", "market-analysis.v1", payload)
        types = [b["type"] for b in view["blocks"]]
        self.assertIn("metrics", types)
        self.assertIn("cards", types)
        self.assertIn("list", types)

    def test_serializer_output_views(self):
        save_artifact(
            self.creation,
            "project_brief",
            {"core_idea": "测试剧", "genre_positioning": "甜宠"},
        )
        exec_row = DramaRoleExecution.objects.create(
            project=self.drama,
            agent_id="drama.topic-planner",
            agent_name_zh="选题策划官",
            status=DramaRoleExecution.Status.SUCCESS,
            output_artifacts={"project_brief": {"core_idea": "测试剧", "genre_positioning": "甜宠"}},
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
        expert = Project.objects.filter(title="e2e-drama-expert", track_mode="expert").first()
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

    def test_world_setting_core_spaces(self):
        payload = {
            "era_background": "2026年沪城",
            "core_spaces": ["竖屏近景适配的豪门宴会厅，怼脸拍强化情绪冲击"],
        }
        view = present_artifact("world_setting", "world-setting.v1", payload)
        types = {b["type"] for b in view["blocks"]}
        self.assertIn("hero", types)
        self.assertIn("cards", types)
        self.assertIn("豪门宴会厅", str(view["blocks"]))

    def test_world_setting_canonical_fields(self):
        payload = {
            "core_spaces": [
                "9:16竖屏两室一厅合租出租屋",
                "通勤早餐铺与公司茶水间",
            ],
            "special_rules": ["男主实力以顺手帮忙形式体现"],
            "era_background": "2025年新一线城市合租社区",
            "power_structure": "两套互不干扰的身份认知体系",
            "core_world_rules": [
                "男主必须全程隐藏大佬身份",
                "全剧不存在狗血误会",
            ],
            "taboo_constraints": ["不能出现霸总式豪车接送"],
        }
        view = present_artifact("world_setting", "world-setting.v1", payload)
        corpus = str(view["blocks"])
        self.assertIn("合租", corpus)
        self.assertIn("顺手帮忙", corpus)
        self.assertIn("霸总", corpus)
        types = {b["type"] for b in view["blocks"]}
        self.assertIn("steps", types)

    def test_world_setting_power_dict(self):
        payload = {
            "era_background": "星碎纪元3729年遮天联邦崩坏",
            "core_spaces": ["黑岩废土求生区", "万族浮空城序列"],
            "core_world_rules": ["宿命绑定规则", "资源置换修炼规则"],
            "special_rules": [
                "穿越者豁免机制",
                "弹幕投票干涉机制",
            ],
            "power_structure": {
                "宿命观测者": "幕后boss",
                "底层求生者联盟": "被压榨基数",
            },
            "taboo_constraints": ["禁止私藏灵能晶"],
        }
        view = present_artifact("world_setting", "world-setting.v1", payload)
        corpus = str(view["blocks"])
        self.assertIn("星碎纪元", corpus)
        self.assertIn("黑岩废土", corpus)
        self.assertIn("宿命观测者", corpus)
        self.assertIn("穿越者豁免", corpus)
        self.assertIn("禁止私藏", corpus)
        types = {b["type"] for b in view["blocks"]}
        self.assertIn("hero", types)
        self.assertIn("cards", types)
        self.assertIn("steps", types)
        step_titles = [b.get("title") for b in view["blocks"] if b["type"] == "steps"]
        self.assertTrue(any("特殊规则" in str(t) for t in step_titles))

    def test_world_setting_space_title_parsed(self):
        payload = {
            "core_spaces": [
                "黑岩废土求生区：主角穿越后的初始底层据点",
            ],
        }
        view = present_artifact("world_setting", "world-setting.v1", payload)
        cards = next(b for b in view["blocks"] if b["type"] == "cards")
        self.assertEqual(cards["items"][0]["title"], "黑岩废土求生区")
        self.assertIn("主角穿越", cards["items"][0]["body"])

    def test_character_bible_roster_badge_and_role_row(self):
        payload = {
            "characters": [
                {
                    "name": "林野",
                    "character_id": "C001",
                    "role_type": "绝对主角",
                    "surface_desire": "活下去",
                }
            ],
        }
        view = present_artifact("character_bible", "character-bible.v1", payload)
        roster = next(b for b in view["blocks"] if b["type"] == "character_roster")
        char = roster["characters"][0]
        self.assertEqual(char["title"], "林野")
        self.assertEqual(char["badge"], "C001")
        self.assertEqual(char["role_label"], "绝对主角")
        keys = [row["key"] for row in char["rows"]]
        self.assertNotIn("角色类型", keys)
        self.assertIn("表层欲望", keys)

    def test_market_report_v1_presenter(self):
        payload = {
            "drama_basic_info": {
                "core_genre": "ambition-transmigration-survival-fantasy",
                "drama_name": "遮天：异世登顶100层",
                "total_episodes": 100,
                "target_platform": "Douyin",
            },
            "platform_market_analysis": {
                "target_audience_portrait": "核心受众为18-35岁男性用户",
                "Douyin_short_drama_current_trend": "玄幻穿越类短剧日均播放量突破22亿",
            },
            "risk_warning_and_suggestion": {
                "content_risk_avoidance": "需规避玄幻内容的违规表述",
                "release_strategy_suggestion": "采用日更2集的释放节奏",
            },
            "commercial_operation_forecast": {
                "derivative_expansion_path": "联动抖音游戏发行人计划",
                "expected_data_performance": "单部作品总流水预期可达3500万",
            },
            "core_project_competitiveness_analysis": {
                "IP_foundation": "遮天自带国民级玄幻IP认知基础",
                "genre_matching_degree": "精准贴合野心穿越赛道红利",
            },
        }
        view = present_artifact("market_report", "market-report.v1", payload)
        self.assertNotIn("未注册展示器", view.get("summary") or "")
        block_types = {b["type"] for b in view["blocks"]}
        self.assertIn("market_report", block_types)
        report = next(b for b in view["blocks"] if b["type"] == "market_report")
        self.assertEqual(report["drama_name"], "遮天：异世登顶100层")
        self.assertGreaterEqual(len(report["metrics"]), 2)
        self.assertGreaterEqual(len(report["sections"]), 3)
        corpus = str(view["blocks"])
        self.assertIn("遮天", corpus)
        self.assertIn("抖音", corpus)
        self.assertIn("野心穿越", corpus)

    def test_series_outline_list_stage_and_e001_episodes(self):
        payload = {
            "episode_outlines": [
                {
                    "end_hook": "警报已经亮了起来",
                    "episode_id": "E001",
                    "emotion_markers": {"EV": "穿越恐慌", "ET": "底层绝望", "TP": "系统绑定"},
                    "four_segment_structure": {
                        "opening": "林野猝死穿越",
                        "development": "石锤警告等级规则",
                        "climax": "巡查兵闯入",
                        "resolution": "制作出净辐射水",
                    },
                },
                {
                    "episode_id": "E006",
                    "four_segment_structure": {
                        "opening": "督军降临",
                        "end_hook": "要把避难所扔进兽巢",
                        "emotion_markers": {"ET": "无力感", "EV": "硬扛攻击", "TP": "捡回一条命"},
                    },
                },
            ],
            "six_stage_narrative": [
                {
                    "stage_id": "S1",
                    "stage_name": "建立世界",
                    "episode_range": "第1集-第17集",
                    "core_task": "完成穿越落地",
                }
            ],
            "rhythm_dual_track_validation": {
                "plot_rhythm_check": "每5集至少1个强冲突点",
                "emotion_rhythm_check": "第75集ET=1",
            },
        }
        view = present_artifact("series_outline", "series-outline.v1", payload)
        types = {b["type"] for b in view["blocks"]}
        self.assertIn("outline_overview", types)
        self.assertIn("stage_outlines", types)
        overview = next(b for b in view["blocks"] if b["type"] == "outline_overview")
        self.assertEqual(overview["total_episodes"], "6")
        stages = next(b for b in view["blocks"] if b["type"] == "stage_outlines")
        self.assertEqual(stages["stages"][0]["title"], "建立世界")
        ep1 = stages["stages"][0]["episodes"][0]
        self.assertEqual(ep1["episode_no"], 1)
        self.assertIn("警报", ep1["subtitle"])
        self.assertEqual(len(ep1["structure"]), 4)

    def test_narrative_plan_v1_presenter(self):
        payload = {
            "narrative_core_objective": "5集内完成穿越落地",
            "target_episode_range": "E001-E005",
            "narrative_mechanics": [
                {
                    "mechanism_type": "显性战力标签可视化",
                    "implementation_details": "头顶悬浮战力数字",
                }
            ],
            "episode_narrative_designs": [
                {
                    "episode_id": "E001",
                    "narrative_focus": "穿越落地+系统激活",
                    "narrative_beat_timing": ["0s-30s：主角穿越", "最后3s：警报亮起"],
                    "audience_emotion_design": "恐慌到爽感",
                    "key_narrative_techniques": ["硬切反差开场"],
                    "worldview_delivery_points": ["底层宿命锁死"],
                }
            ],
            "narrative_consistency_check": "符合S1阶段任务",
        }
        view = present_artifact("narrative_plan", "narrative-plan.v1", payload)
        self.assertNotIn("未注册展示器", view.get("summary") or "")
        plan = next(b for b in view["blocks"] if b["type"] == "narrative_plan")
        self.assertEqual(plan["target_range"], "第1-5集")
        self.assertEqual(plan["episodes"][0]["episode_no"], 1)
        self.assertIn("硬切", plan["episodes"][0]["techniques"][0])

    def test_narrative_plan_v1_presenter_coerces_string_beat_and_mechanics(self):
        payload = {
            "narrative_core_objective": "开篇五集",
            "target_episode_range": "E001-E005",
            "narrative_mechanics": [
                "「反差锚定」叙事机制：每集开篇展示麻木状态；紧接着切入爽点行动",
            ],
            "episode_narrative_designs": [
                {
                    "episode_id": "E001",
                    "narrative_focus": "穿越落地",
                    "narrative_beat_timing": "0-30s：穿越醒来；30s-1min：石锤警告宿命",
                    "audience_emotion_design": "恐慌到爽感",
                }
            ],
        }
        view = present_artifact("narrative_plan", "narrative-plan.v1", payload)
        plan = next(b for b in view["blocks"] if b["type"] == "narrative_plan")
        self.assertEqual(plan["mechanics"][0]["title"], "「反差锚定」叙事机制")
        self.assertIn("麻木", plan["mechanics"][0]["body"])
        self.assertEqual(len(plan["episodes"][0]["beat_timeline"]), 2)
        self.assertIn("穿越", plan["episodes"][0]["beat_timeline"][0])
        self.assertEqual(plan["episodes"][0]["beats"][0]["time"], "0-30s")
        self.assertIn("穿越", plan["episodes"][0]["beats"][0]["content"])


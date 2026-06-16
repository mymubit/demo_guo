# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.dialogue_shaper import (
    apply_dialogue_shaper,
    line_char_count,
    truncate_dialogue_line,
)
from apps.creation.orchestration.plot_structure_review import analyze_plot_structure


class DialogueShaperTests(SimpleTestCase):
    def test_truncate_long_line(self):
        long_line = (
            "你凭什么这样对我，我今天就要让你知道什么叫做真正的后悔与代价，"
            "从今以后你别想在这个城市里再翻身"
        )
        out, cut = truncate_dialogue_line(long_line, max_chars=40)
        self.assertTrue(cut)
        self.assertLessEqual(line_char_count(out), 40)

    def test_apply_dialogue_shaper_truncates_and_sets_char_count(self):
        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scenes": [
                        {
                            "sceneNumber": 1,
                            "dialogues": [
                                {
                                    "order": 1,
                                    "speaker": "c1",
                                    "line": (
                                        "你凭什么这样对我，我今天就要让你知道什么叫做真正的后悔与代价，"
                                        "从今以后你别想在这个城市里再翻身"
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        characters = {
            "protagonists": [{"id": "c1", "name": "林小雨"}],
        }
        out, log = apply_dialogue_shaper(payload, characters)
        dlg = out["episodes"][0]["scenes"][0]["dialogues"][0]
        self.assertEqual(dlg["speaker"], "林小雨")
        self.assertEqual(dlg["speakerId"], "c1")
        self.assertLessEqual(dlg["charCount"], 40)
        self.assertTrue(log.get("truncatedCount") >= 1)
        self.assertTrue((out["episodes"][0].get("scriptMarkdown") or "").strip())


class PlotStructureReviewTests(SimpleTestCase):
    def test_detects_missing_outline_reversal(self):
        structure = {
            "keyReversalPoints": [
                {"episodeNumber": 5, "reversalType": "identity-reveal", "description": "身份曝光"},
            ],
            "rhythmCurve": [{"episodeRange": "1-10", "intensityLevel": 4}],
        }
        outline = {
            "episodes": [
                {"episodeNumber": 1, "oneLineSummary": "开场", "cliffhanger": "悬念"},
                {"episodeNumber": 5, "oneLineSummary": "转折"},
            ],
        }
        out = analyze_plot_structure(structure_plan=structure, series_outline=outline)
        self.assertFalse(out["passed"])
        self.assertTrue(any("反转" in i for i in out.get("issues") or []))

    def test_passes_when_outline_aligns(self):
        structure = {
            "keyReversalPoints": [
                {"episodeNumber": 2, "reversalType": "hidden-truth", "description": "真相"},
            ],
            "rhythmCurve": [{"episodeRange": "1-10", "intensityLevel": 7}],
        }
        outline = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "cliffhanger": "她是谁？",
                    "hookTypeCode": "HOOK-SLAP-01",
                },
                {
                    "episodeNumber": 2,
                    "reversal": "真相曝光",
                    "cliffhanger": "更大的秘密",
                    "hookTypeCode": "HOOK-QUESTION-02",
                },
            ],
        }
        out = analyze_plot_structure(structure_plan=structure, series_outline=outline)
        self.assertTrue(out["passed"])


class QualityGuardTests(SimpleTestCase):
    def test_detects_rigid_phrase_and_low_score(self):
        from apps.creation.orchestration.quality_guard import run_quality_guard

        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scenes": [
                        {
                            "actions": [{"content": "△ 林晚走进房间，眼神复杂"}],
                            "dialogues": [{"speaker": "林晚", "line": "嗯"}],
                        }
                    ],
                }
            ],
        }
        out = run_quality_guard(payload, score_report={"overallScore": 50})
        self.assertFalse(out["passed"])
        self.assertTrue(any("眼神复杂" in i or "评分" in i for i in out.get("issues") or []))


class MarketingHooksTests(SimpleTestCase):
    def test_build_clip_hooks_from_outline(self):
        from apps.creation.marketing_hooks import build_clip_hooks, enrich_marketing_kit

        outline = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "hook": "巴掌响起全场安静",
                    "hookTypeCode": "HOOK-SLAP-01",
                }
            ],
        }
        hooks = build_clip_hooks(brief={"coreHook": "豪门复仇"}, outline=outline)
        self.assertGreaterEqual(len(hooks), 2)
        kit = enrich_marketing_kit({"titles": ["测试剧"]}, outline=outline)
        self.assertGreaterEqual(len(kit.get("clipHooks") or []), 2)

    def test_title_risk_flags_sensitive_word(self):
        from apps.creation.marketing_title_risk import review_title_risk

        out = review_title_risk("某某淫秽大剧")
        self.assertFalse(out["passed"])


class ConflictAdvisorTests(SimpleTestCase):
    def test_build_conflict_strategy_with_antagonist(self):
        from apps.creation.conflict_advisor import build_conflict_strategy, merge_conflict_into_creative_plan

        strategy = build_conflict_strategy(
            structure_plan={
                "keyReversalPoints": [{"episodeNumber": 10, "description": "大反转"}],
                "rhythmCurve": [{"episodeRange": "1-10", "intensityLevel": 8}],
            },
            character_bible={"antagonists": [{"name": "赵婆", "roleType": "antagonist-female"}]},
            total_episodes=30,
        )
        self.assertIn(10, strategy.get("majorConfrontationEpisodes") or [])
        self.assertGreaterEqual(len(strategy.get("conflictCycle") or []), 5)
        self.assertIn("赵婆", strategy.get("antagonistPressure") or "")

        plan = merge_conflict_into_creative_plan({"hookDiversity": {}}, total_episodes=20)
        self.assertTrue(plan.get("conflictStrategy"))


class PaymentPlannerTests(SimpleTestCase):
    def test_build_payment_checkpoints_80_episodes(self):
        from apps.creation.payment_planner import build_payment_checkpoints, merge_payment_into_creative_plan

        pts = build_payment_checkpoints(80)
        eps = [p["episode"] for p in pts]
        self.assertIn(8, eps)
        self.assertIn(30, eps)
        self.assertIn(60, eps)

        plan = merge_payment_into_creative_plan({}, total_episodes=80)
        self.assertGreaterEqual(len(plan.get("paymentCheckpoints") or []), 5)


class PsychologyAdvisorTests(SimpleTestCase):
    def test_build_psychology_for_family_revenge(self):
        from apps.creation.psychology_advisor import build_psychology_strategy, merge_psychology_into_creative_plan

        strategy = build_psychology_strategy(theme="family-revenge", total_episodes=80)
        self.assertEqual(strategy.get("dominantArchetype"), "catharsis")
        self.assertTrue(strategy.get("informationGapStrategy"))
        self.assertGreaterEqual(len(strategy.get("dreamLayers") or []), 2)

        plan = merge_psychology_into_creative_plan({}, theme="sweet-pet", total_episodes=70)
        psych = plan.get("psychologyStrategy") or {}
        self.assertEqual(psych.get("dominantArchetype"), "escape")


class IndustryBenchmarksTests(SimpleTestCase):
    def test_apply_structure_benchmark_hints(self):
        from apps.creation.industry_benchmarks import apply_structure_benchmark_hints, reversal_cadence

        cadence = reversal_cadence()
        self.assertIn("small", cadence)

        payload = apply_structure_benchmark_hints({"rhythmCurve": [{"episodeRange": "1-10", "intensityLevel": 6}]})
        constraints = payload.get("structuralConstraints") or {}
        self.assertTrue(constraints.get("industryBenchmarkHints"))
        self.assertEqual(constraints.get("smallReversalEveryEpisodes"), 3)


class ComplianceFuseTests(SimpleTestCase):
    def test_triggers_on_violent_content(self):
        from apps.creation.compliance_fuse import merge_fuse_with_cli, run_compliance_fuse_scan

        report = run_compliance_fuse_scan("主角被人斩首，鲜血喷溅一地。")
        self.assertTrue(report["fuseTriggered"])
        self.assertEqual(report["categories"][0]["code"], "violent-bloody")

        merged = merge_fuse_with_cli(report, {"passed": True, "fuseTriggered": False})
        self.assertTrue(merged["fuseTriggered"])

    def test_passes_clean_text(self):
        from apps.creation.compliance_fuse import run_compliance_fuse_scan

        report = run_compliance_fuse_scan("林小雨转身离开，心里暗暗下定决心。")
        self.assertFalse(report["fuseTriggered"])


class ThemeRecommenderTests(SimpleTestCase):
    def test_recommend_family_revenge_from_hook(self):
        from apps.creation.theme_recommender import merge_theme_recommendations, recommend_themes

        recs = recommend_themes({"coreHook": "婆婆刁难儿媳，女主复仇打脸"}, limit=3)
        self.assertGreaterEqual(len(recs), 1)
        codes = [r["themeCode"] for r in recs]
        self.assertIn("family-revenge", codes)

        brief = merge_theme_recommendations({"coreHook": "甜宠霸总"})
        self.assertTrue(brief.get("themeRecommendations"))


class SmartSearchTests(SimpleTestCase):
    def test_search_reference_scripts(self):
        from apps.creation.smart_search import run_smart_search

        out = run_smart_search("错嫁", limit=5)
        self.assertGreaterEqual(out["resultCount"], 1)
        self.assertTrue(any(r.get("type") == "reference-script" for r in out["results"]))


class ComplianceContentTests(SimpleTestCase):
    def test_detects_false_advertising(self):
        from apps.creation.compliance_content import run_compliance_content_scan

        report = run_compliance_content_scan("本产品最有效，100%根治，央视推荐。")
        self.assertFalse(report["passed"])
        self.assertGreater(report.get("findingCount") or 0, 0)

    def test_passes_clean_copy(self):
        from apps.creation.compliance_content import run_compliance_content_scan

        report = run_compliance_content_scan("林小雨在雨夜里下定决心反击。")
        self.assertTrue(report["passed"])

    def test_hot_sensitive_triggers_fuse(self):
        from apps.creation.compliance_content import run_compliance_content_scan

        report = run_compliance_content_scan("剧情影射唐山打人事件。")
        self.assertTrue(report.get("fuseTriggered"))
        self.assertFalse(report["passed"])


class IpLockTests(SimpleTestCase):
    def test_character_ip_lock_builds_roster(self):
        from apps.creation.ip_lock import merge_character_ip_lock, run_script_ip_lock

        bible = {
            "protagonists": [{"id": "p1", "name": "林小雨", "roleType": "protagonist-female"}],
            "antagonists": [{"id": "a1", "name": "赵婆", "roleType": "antagonist-female"}],
        }
        brief = {"creationEntry": "ip-sequel", "ipKeepRules": "林小雨"}
        out = merge_character_ip_lock(bible, brief)
        self.assertGreaterEqual(len(out.get("ipLockRoster") or []), 2)
        self.assertTrue((out.get("ipCharacterLockLog") or {}).get("passed"))

        script = {
            "characterIdToNameMap": {"p1": "林小雨", "a1": "赵婆"},
            "episodes": [
                {
                    "episodeNumber": 1,
                    "scriptMarkdown": "林小雨：我不会再忍了。赵婆冷笑。",
                }
            ],
        }
        script_report = run_script_ip_lock(script, brief=brief, character_bible=out)
        self.assertTrue(script_report.get("passed"))

    def test_character_ip_lock_accepts_name_aliases(self):
        from apps.creation.ip_lock import merge_character_ip_lock

        bible = {
            "protagonists": [
                {
                    "characterId": "p1",
                    "characterName": "林小雨",
                    "role": "protagonist-female",
                }
            ],
            "antagonists": [
                {
                    "character_id": "a1",
                    "displayName": "赵婆",
                    "characterRole": "antagonist-female",
                }
            ],
        }
        brief = {"creationEntry": "ip-sequel", "ipKeepRules": "林小雨"}

        out = merge_character_ip_lock(bible, brief)

        self.assertEqual(len(out.get("ipLockRoster") or []), 2)
        self.assertTrue((out.get("ipCharacterLockLog") or {}).get("passed"))


class ScriptPsychologyTests(SimpleTestCase):
    def test_build_episode_hints(self):
        from apps.creation.script_psychology import build_episode_psychology_hints

        hints = build_episode_psychology_hints(
            {
                "creativePlan": {
                    "psychologyStrategy": {
                        "dominantArchetype": "catharsis",
                        "audiencePainPoint": "压抑后宣泄",
                        "informationGapStrategy": "身份分批揭露",
                    },
                    "paymentCheckpoints": [{"episode": 10}],
                    "conflictStrategy": {
                        "conflictCycle": [{"episode": 3, "note": "小危机"}],
                    },
                }
            },
            from_episode=1,
            to_episode=10,
        )
        self.assertEqual(hints.get("dominantArchetype"), "catharsis")
        self.assertEqual(len(hints.get("episodes") or []), 10)
        ep3 = next(e for e in hints["episodes"] if e["episode"] == 3)
        self.assertTrue(ep3.get("directives"))

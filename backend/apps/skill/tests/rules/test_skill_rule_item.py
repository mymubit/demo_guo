# -*- coding: utf-8 -*-
import json
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.skill.models import SkillRuleConfig, SkillRuleItem
from apps.skill.skills.loader import SkillRuleLoader
from apps.skill.skills.rule_item_flatten import flatten_config
from apps.skill.skills.rule_item_service import SkillRuleItemService

_SAMPLES_PATH = Path(__file__).resolve().parents[3] / "tmp_rule_samples.json"


def _load_sample(section_key: str) -> dict:
    if not _SAMPLES_PATH.exists():
        return {}
    data = json.loads(_SAMPLES_PATH.read_text(encoding="utf-8"))
    entry = data.get(section_key) or {}
    return entry.get("content") or {}


class SkillRuleItemFlattenTests(TestCase):
    def test_flatten_writing_prohibitions_list(self):
        config = SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="writing_prohibitions",
            content=["禁止 AI 腔", "禁止流水账"],
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        items = flatten_config(config)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "禁止 AI 腔")

    def test_flatten_genre_full_requirements(self):
        content = _load_sample("T2/genre_full") or {
            "requirements": [{"element": "首次甜点", "standard": "Ep1-5内必须有糖分场景"}],
            "prohibitions": ["连续超过5集纯甜或纯虐"],
        }
        config = SkillRuleConfig.objects.create(
            tier=2,
            scope_type=SkillRuleConfig.SCOPE_GENRE,
            scope_key="sweet-pet",
            section="genre_full",
            content=content,
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        items = flatten_config(config)
        titles = {row["title"] for row in items}
        self.assertIn("首次甜点", titles)
        self.assertTrue(any("纯甜" in row["body"] for row in items))
        self.assertFalse(any(len(row["body"]) == 1 for row in items))

    def test_flatten_keyword_blacklist_no_single_char_garbage(self):
        content = _load_sample("T1/ai-keywords-blacklist")
        if not content:
            content = {
                "替换映射": {"其次": ["还有啊", "再说了"]},
                "自然停顿词": ["嗯", "哦"],
            }
        config = SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="ai-keywords-blacklist",
            content=content,
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        items = flatten_config(config)
        self.assertGreaterEqual(len(items), 3)
        pause_items = [row for row in items if row["payload"].get("kind") == "pause_word"]
        self.assertEqual({row["title"] for row in pause_items}, {"嗯", "哦"})
        for row in items:
            self.assertGreater(len(row["body"]), 1)

    def test_flatten_skips_aggregate_bundle(self):
        config = SkillRuleConfig.objects.create(
            tier=2,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="tier2-genre-rules",
            content={"genres": {"x": {"label": "test"}}},
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        self.assertEqual(flatten_config(config), [])

    def test_flatten_pipeline_node_constraints(self):
        content = _load_sample("T3/pipeline_node_full") or {
            "name": "剧本润色",
            "constraints": ["不得改变情节走向"],
            "gate_conditions": ["review_report存在"],
        }
        config = SkillRuleConfig.objects.create(
            tier=3,
            scope_type=SkillRuleConfig.SCOPE_NODE,
            scope_key="node-7-polish",
            section="pipeline_node_full",
            content=content,
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        items = flatten_config(config)
        bodies = " ".join(row["body"] for row in items)
        self.assertIn("不得改变情节走向", bodies)
        self.assertIn("review_report", bodies)

    def test_flatten_service_creates_rows(self):
        SkillRuleConfig.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="philosophy",
            content={"core_formula": "冲突先行"},
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        result = SkillRuleItemService.flatten_from_configs(overwrite=True, as_draft=False)
        self.assertGreater(result["created"], 0)
        self.assertTrue(
            SkillRuleItem.objects.filter(section="philosophy", status=SkillRuleConfig.STATUS_ACTIVE).exists()
        )


class SkillRuleItemLoaderTests(TestCase):
    @patch(
        "apps.skill.skills.loader.resolve_tier1_sections",
        return_value=["writing_prohibitions"],
    )
    def test_loader_prefers_items_and_records_apply(self, _mock_sections):
        SkillRuleItem.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="writing_prohibitions",
            rule_key="t1.global.writing_prohibitions.test",
            title="测试铁律",
            body="冲突必须在前三集爆发",
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        loader = SkillRuleLoader()
        prompt = loader.build_full_system_prompt(node_id="node_script", genre="")
        self.assertIn("冲突必须在前三集爆发", prompt)
        row = SkillRuleItem.objects.get(rule_key="t1.global.writing_prohibitions.test")
        self.assertEqual(row.apply_count, 1)
        self.assertIsNotNone(row.last_applied_at)

    @patch(
        "apps.skill.skills.loader.resolve_tier1_sections",
        return_value=["writing_prohibitions"],
    )
    def test_loader_tier1_snippet_filters_section(self, _mock_sections):
        SkillRuleItem.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="writing_prohibitions",
            rule_key="t1.global.writing_prohibitions.snippet",
            title="禁止项",
            body="造梦公式",
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        SkillRuleItem.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="not-in-node-sections",
            rule_key="t1.global.other.snippet",
            title="其他",
            body="不应出现",
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )
        snippet = SkillRuleLoader().build_tier1_node_snippet("node_script")
        self.assertIn("造梦公式", snippet)
        self.assertNotIn("不应出现", snippet)


class SkillRuleItemApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900006602",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.item = SkillRuleItem.objects.create(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            scope_key="",
            section="philosophy",
            rule_key="t1.global.philosophy.api",
            title="API 测试",
            body="正文",
            status=SkillRuleConfig.STATUS_DRAFT,
            source=SkillRuleConfig.SOURCE_ADMIN,
        )

    def test_list_rule_items(self):
        resp = self.client.get("/api/admin/skills/rule-items/?tier=1&status=draft")
        self.assertEqual(resp.status_code, 200)
        ids = [item["id"] for item in resp.data["data"]["items"]]
        self.assertIn(str(self.item.id), ids)

    def test_update_rule_item(self):
        resp = self.client.put(
            f"/api/admin/skills/rule-items/{self.item.id}/",
            {"title": "更新标题", "body": "更新正文"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "更新标题")

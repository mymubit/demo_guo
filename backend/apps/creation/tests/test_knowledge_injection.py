# -*- coding: utf-8 -*-
"""知识库相关性注入：类别排除、相关性匹配、Top-N、去重、后台策略。"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import (
    AgentDefinition,
    AgentKnowledgeBinding,
    AgentKnowledgeItem,
)
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.models import Project

User = get_user_model()


class KnowledgeInjectionTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.agent = AgentDefinitionService.get_runnable("drama.script-writer")
        # 清掉默认种子绑定，专注验证本测试构造的数据
        self.agent.knowledge_bindings.all().delete()
        self.user = User.objects.create_user(phone="13900007777", password="pass-123456")
        self.project = Project.objects.create(
            user=self.user,
            title="kn-test",
            theme="overbearing-ceo",
            core_idea="测试",
            episode_count=6,
            format_variant="B",
            target_platform="douyin",
        )

    def _bind(self, knowledge_id, category, *, themes=None, platforms=None,
              injectable=True, content="内容", priority=100, order=0, title=None):
        item = AgentKnowledgeItem.objects.create(
            knowledge_id=knowledge_id,
            title=title or knowledge_id,
            category=category,
            content_text=content,
            match_themes=themes or [],
            match_platforms=platforms or [],
            is_prompt_injectable=injectable,
            priority=priority,
        )
        AgentKnowledgeBinding.objects.create(
            agent=self.agent,
            knowledge=item,
            binding_type=AgentKnowledgeBinding.BindingType.OPTIONAL,
            inject_position=AgentKnowledgeBinding.InjectPosition.CONTEXT,
            order_index=order,
            is_enabled=True,
        )
        return item

    def _keys(self, project=None):
        rows = IndependentAgentService.load_knowledge(self.agent, project or self.project)
        return [r["knowledge_id"] for r in rows]

    def test_excludes_validator_and_schema_categories(self):
        self._bind("rule-1", AgentKnowledgeItem.Category.RULE)
        self._bind("validator-1", AgentKnowledgeItem.Category.VALIDATOR, injectable=False)
        self._bind("schema-1", AgentKnowledgeItem.Category.SCHEMA, injectable=False)
        keys = self._keys()
        self.assertIn("rule-1", keys)
        self.assertNotIn("validator-1", keys)
        self.assertNotIn("schema-1", keys)

    def test_excludes_non_injectable_items(self):
        self._bind("noinject", AgentKnowledgeItem.Category.KNOWLEDGE, injectable=False)
        self.assertNotIn("noinject", self._keys())

    def test_theme_relevance_filters_out_mismatched(self):
        self._bind("ceo-script", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, themes=["overbearing-ceo"])
        self._bind("revenge-script", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, themes=["family-revenge"])
        self._bind("universal-script", AgentKnowledgeItem.Category.REFERENCE_SCRIPT)
        keys = self._keys()
        self.assertIn("ceo-script", keys)
        self.assertIn("universal-script", keys)
        self.assertNotIn("revenge-script", keys)

    def test_platform_relevance_filters_out_mismatched(self):
        self._bind("douyin-ref", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, platforms=["douyin"])
        self._bind("kuaishou-ref", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, platforms=["kuaishou"])
        keys = self._keys()
        self.assertIn("douyin-ref", keys)
        self.assertNotIn("kuaishou-ref", keys)

    def test_category_cap_limits_reference_scripts(self):
        for i in range(5):
            self._bind(f"ref-{i}", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, order=i, title=f"ref-{i}")
        keys = [k for k in self._keys() if k.startswith("ref-")]
        # 默认策略 reference_script 上限为 2
        self.assertEqual(len(keys), 2)

    def test_dedup_same_title_across_sources(self):
        self._bind("src-a:同名剧本", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, title="同名剧本", order=0)
        self._bind("src-b:同名剧本", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, title="同名剧本", order=1)
        keys = self._keys()
        self.assertEqual(len([k for k in keys if "同名剧本" in k]), 1)

    def test_agent_policy_override_excludes_category(self):
        self._bind("ex-1", AgentKnowledgeItem.Category.EXAMPLE)
        self.agent.knowledge_injection_policy = {"excluded_categories": ["example", "validator", "schema"]}
        self.agent.save(update_fields=["knowledge_injection_policy"])
        self.agent.refresh_from_db()
        self.assertNotIn("ex-1", self._keys())

    def test_rules_not_capped_by_default(self):
        for i in range(30):
            self._bind(f"rule-{i}", AgentKnowledgeItem.Category.RULE, order=i, title=f"rule-{i}")
        keys = [k for k in self._keys() if k.startswith("rule-")]
        self.assertEqual(len(keys), 30)

    def test_none_project_skips_relevance_filter(self):
        self._bind("ceo-only", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, themes=["overbearing-ceo"])
        self._bind("revenge-only", AgentKnowledgeItem.Category.REFERENCE_SCRIPT, themes=["family-revenge"])
        rows = IndependentAgentService.load_knowledge(self.agent, None)
        keys = [r["knowledge_id"] for r in rows]
        self.assertIn("ceo-only", keys)
        self.assertIn("revenge-only", keys)

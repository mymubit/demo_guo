# -*- coding: utf-8 -*-
"""PromptBuilder 注入完整契约块：嵌套必填路径 + 示例 JSON。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import SKILLS_ROOT

_SETTINGS = {
    "title": "玉石宫闱",
    "entry_type": "original_track",
    "episode_count": 40,
    "genre_matrix": {
        "emotion": "ambition",
        "identity": "hidden-elite",
        "conflict": "power",
        "world": "ancient",
    },
}


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class PromptSchemaInjectionTests(SimpleTestCase):
    def setUp(self) -> None:
        self.builder = PromptBuilder(loader=SkillsBundleLoader(root=SKILLS_ROOT))

    def test_episode_designer_prompt_locks_opening_hook_key(self) -> None:
        system, _user = self.builder.build(
            "drama.episode-designer",
            settings=_SETTINGS,
            workflow_state={"current_phase": "episode_design"},
            artifacts={},
        )
        self.assertIn("opening_hook", system)
        self.assertIn("episode_narrative_designs[].opening_hook", system)
        self.assertIn('"opening_hook"', system)  # 示例里的 JSON 键
        # 旧的仅顶层提示可消失或并存，但必须有嵌套路径
        self.assertNotIn("必填字段: episode_narrative_designs\n", system)

    def test_story_bible_prompt_locks_surface_desire_and_arc_start(self) -> None:
        system, _user = self.builder.build(
            "drama.story-bible",
            settings=_SETTINGS,
            workflow_state={"current_phase": "blueprint"},
            artifacts={},
        )
        self.assertIn("surface_desire", system)
        self.assertIn("characters[].arc.start", system)
        self.assertIn('"surface_desire"', system)

    def test_user_prompt_carries_full_schema_required_paths(self) -> None:
        _system, user = self.builder.build(
            "drama.episode-designer",
            settings=_SETTINGS,
            workflow_state={"current_phase": "episode_design"},
            artifacts={},
        )
        self.assertIn("schema_required_paths", user)
        self.assertIn("episode_narrative_designs[].opening_hook", user)

    def test_project_brief_keeps_behavior_constraints_without_top_required(self) -> None:
        system, _user = self.builder.build(
            "drama.topic-director",
            settings=_SETTINGS,
            workflow_state={"current_phase": "blueprint"},
            artifacts={},
        )
        # 行为约束保留
        self.assertIn("schema 外字段", system)
        # 旧的仅顶层必填字段提示应消失
        self.assertNotIn("必填字段: title", system)

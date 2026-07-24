# -*- coding: utf-8 -*-
"""project_brief 实质门禁：拒绝占位竞品与口号差异化。"""
from __future__ import annotations

from django.test import SimpleTestCase

from apps.drama.services.artifact_normalize import project_brief_too_thin


def _ok_brief(**overrides: object) -> dict:
    base = {
        "title": "归园田居",
        "market_opportunity": "乡土治愈赛道热度上升，缺「做菜过程可视化+邻里秘密」组合。",
        "differentiation_strategy": "每道菜绑定一位邻居的往事；禁止空喊治愈口号，冲突落在信任试探。",
        "first_episode_hook": "返乡第一顿饭翻车，被陌生邻居递来一碗热汤并点破他不会过日子。",
        "paywall_direction": "观众想知道他城市身份与邻里能否共存，催付费看身份摊牌。",
        "competitor_references": [
            {
                "title": "去有风的地方",
                "inspiration": "慢节奏烟火与旅居疗愈的感官细节。",
                "avoidance": "避免长时间无冲突的散文式散漫。",
            },
            {
                "title": "小巷人家",
                "inspiration": "邻里群像用小事件推进人物关系。",
                "avoidance": "避免群像平均用力导致主角动机模糊。",
            },
        ],
    }
    base.update(overrides)
    return base


class ProjectBriefSubstanceTests(SimpleTestCase):
    def test_concrete_brief_passes(self) -> None:
        self.assertFalse(project_brief_too_thin(_ok_brief()))

    def test_placeholder_competitor_fails(self) -> None:
        brief = _ok_brief(
            competitor_references=[
                {"title": "竞品1", "inspiration": "学一点节奏", "avoidance": "别太散"},
                {
                    "title": "去有风的地方",
                    "inspiration": "慢节奏烟火细节可借鉴。",
                    "avoidance": "避免无冲突散文式散漫。",
                },
            ]
        )
        self.assertTrue(project_brief_too_thin(brief))

    def test_missing_inspiration_fails(self) -> None:
        brief = _ok_brief(
            competitor_references=[
                {"title": "去有风的地方", "avoidance": "避免无冲突散文式散漫。"},
                {
                    "title": "小巷人家",
                    "inspiration": "邻里群像用小事件推进。",
                    "avoidance": "避免主角动机模糊。",
                },
            ]
        )
        self.assertTrue(project_brief_too_thin(brief))

    def test_slogan_differentiation_fails(self) -> None:
        brief = _ok_brief(differentiation_strategy="我们质量更好更有深度")
        self.assertTrue(project_brief_too_thin(brief))

    def test_vague_hook_fails(self) -> None:
        brief = _ok_brief(first_episode_hook="婚礼现场反击")
        self.assertTrue(project_brief_too_thin(brief))

    def test_too_few_competitors_fails(self) -> None:
        brief = _ok_brief(
            competitor_references=[
                {
                    "title": "去有风的地方",
                    "inspiration": "慢节奏烟火细节可借鉴。",
                    "avoidance": "避免无冲突散文式散漫。",
                }
            ]
        )
        self.assertTrue(project_brief_too_thin(brief))

# -*- coding: utf-8 -*-
"""产物版本与 latest_script 测试。"""
from django.test import TestCase, override_settings

from apps.drama.services.artifact_service import ArtifactService
from apps.drama.tests.helpers import create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT="/workspace", LLM_ENABLED=False)
class ArtifactServiceTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = ArtifactService()

    def _episode_scripts_payload(self, script: str = "测试剧本"):
        return {
            "episodes": [
                {
                    "episode_number": 1,
                    "title": "第一集",
                    "script": script,
                    "word_count": len(script),
                    "dialogue_ratio": 0.4,
                    "scene_count": 1,
                    "golden_lines": [],
                    "format_check": {},
                    "memory_checkpoint": {
                        "episode": 1,
                        "character_states": [],
                        "active_clues": [],
                        "foreshadowing": [],
                        "relationship_changes": [],
                        "prop_states": [],
                        "rhythm_state": {
                            "plot_pace": "tight",
                            "emotion_pace": "heavy",
                            "episode_ev": 5,
                            "episode_et": 3,
                            "episode_tp": "测试",
                        },
                        "next_episode_constraints": [],
                    },
                    "production_notes": {
                        "tags": [],
                        "complexity_score": 0,
                        "complexity_band": "lean",
                        "high_cost_scenes": [],
                        "lower_cost_alternatives": [],
                    },
                }
            ]
        }

    def test_artifact_version_increment(self):
        self.svc.save_artifact(
            self.project, "episode_scripts", self._episode_scripts_payload("v1")
        )
        self.svc.save_artifact(
            self.project, "episode_scripts", self._episode_scripts_payload("v2")
        )
        artifact = self.svc.get_artifact(self.project, "episode_scripts")
        self.assertEqual(artifact["version"], 2)
        self.assertEqual(artifact["payload"]["episodes"][0]["script"], "v2")

    def _polished_script_payload(self, script: str = "polished"):
        episode = self._episode_scripts_payload(script)["episodes"][0]
        episode.pop("golden_lines", None)
        episode.pop("format_check", None)
        return {
            "episodes": [episode],
            "revision_summary": [],
            "resolved_issues": [],
            "remaining_issues": [],
        }

    def test_latest_script_prefers_polished(self):
        self.svc.save_artifact(
            self.project, "episode_scripts", self._episode_scripts_payload("draft")
        )
        self.svc.save_artifact(
            self.project,
            "polished_script",
            self._polished_script_payload("polished"),
        )
        resolved = self.svc.latest_script(self.project)
        self.assertEqual(resolved["resolved_script_key"], "polished_script")

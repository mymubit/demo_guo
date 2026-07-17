from django.test import SimpleTestCase, override_settings

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.schema_prompt_contract import build_output_skeleton, extract_required_paths
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT


class ExtractRequiredPathsTests(SimpleTestCase):
    def test_narrative_plan_includes_nested_opening_hook(self) -> None:
        schema = {
            "type": "object",
            "required": ["episode_narrative_designs"],
            "properties": {
                "episode_narrative_designs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["episode", "opening_hook", "ending_hook"],
                        "properties": {
                            "episode": {"type": "integer"},
                            "opening_hook": {"type": "string"},
                            "ending_hook": {"type": "string"},
                        },
                    },
                }
            },
        }
        paths = extract_required_paths(schema)
        self.assertIn("episode_narrative_designs", paths)
        self.assertIn("episode_narrative_designs[].opening_hook", paths)
        self.assertIn("episode_narrative_designs[].ending_hook", paths)

    def test_story_bible_includes_character_arc_start(self) -> None:
        schema = {
            "type": "object",
            "required": ["characters"],
            "properties": {
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "surface_desire", "arc"],
                        "properties": {
                            "name": {"type": "string"},
                            "surface_desire": {"type": "string"},
                            "arc": {
                                "type": "object",
                                "required": ["start", "end"],
                                "properties": {
                                    "start": {"type": "string"},
                                    "end": {"type": "string"},
                                },
                            },
                        },
                    },
                }
            },
        }
        paths = extract_required_paths(schema)
        self.assertIn("characters[].surface_desire", paths)
        self.assertIn("characters[].arc.start", paths)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class StoryBibleFewshotSchemaTests(SimpleTestCase):
    """Task 5: 首个 fewshot 必须是完整 schema 合法的 story_bible。"""

    def test_first_fewshot_output_validates(self) -> None:
        import yaml
        from pathlib import Path

        path = Path(SKILLS_ROOT) / "roles/drama-story-bible/fewshots.v1.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        output = data["fewshots"][0]["output"]
        SchemaValidator().validate_file(
            output, "schemas/artifacts/story_bible/1.schema.json"
        )

    def test_first_fewshot_output_has_no_alias_keys(self) -> None:
        import yaml
        from pathlib import Path

        path = Path(SKILLS_ROOT) / "roles/drama-story-bible/fewshots.v1.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        output = data["fewshots"][0]["output"]
        # want/initial 等别名键禁止出现在 fewshot output
        self.assertNotIn("want", output)
        self.assertNotIn("initial", output)
        for char in output.get("characters", []):
            self.assertNotIn("want", char)
            self.assertNotIn("initial", char)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class BuildOutputSkeletonTests(SimpleTestCase):
    def test_narrative_plan_skeleton_validates(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("narrative_plan")
        skeleton = build_output_skeleton(
            schema, fixture=FIXTURES["narrative_plan"]
        )
        self.assertIn("opening_hook", skeleton["episode_narrative_designs"][0])
        SchemaValidator().validate_file(
            skeleton, "schemas/artifacts/narrative_plan/1.schema.json"
        )

    def test_story_bible_skeleton_uses_surface_desire_not_want(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("story_bible")
        skeleton = build_output_skeleton(schema, fixture=FIXTURES["story_bible"])
        char = skeleton["characters"][0]
        self.assertIn("surface_desire", char)
        self.assertNotIn("want", char)
        self.assertIn("start", char["arc"])
        SchemaValidator().validate_file(
            skeleton, "schemas/artifacts/story_bible/1.schema.json"
        )

    def test_six_stage_structure_exactly_six(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("story_bible")
        skeleton = build_output_skeleton(schema, fixture=FIXTURES["story_bible"])
        stages = skeleton["series_structure"]["six_stage_structure"]
        self.assertEqual(len(stages), 6)

    def test_synthesize_without_fixture_validates_story_bible(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("story_bible")
        skeleton = build_output_skeleton(schema)
        self.assertIn("surface_desire", skeleton["characters"][0])
        self.assertEqual(len(skeleton["series_structure"]["six_stage_structure"]), 6)
        SchemaValidator().validate_file(
            skeleton, "schemas/artifacts/story_bible/1.schema.json"
        )

    def test_hook_grade_only_from_enum(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("narrative_plan")
        skeleton = build_output_skeleton(schema, fixture=FIXTURES["narrative_plan"])
        self.assertIn(skeleton["episode_narrative_designs"][0]["hook_grade"], {"S", "A", "B", "C"})

    def test_prune_strips_unknown_keys_when_additional_properties_false(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("story_bible")
        bloated_fixture = {
            **FIXTURES["story_bible"],
            "want": "should_be_removed",
        }
        skeleton = build_output_skeleton(schema, fixture=bloated_fixture)
        self.assertNotIn("want", skeleton)

    def test_prune_synthesizes_missing_required_field(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("narrative_plan")
        incomplete = {
            "episode_narrative_designs": [
                {
                    "episode": 1,
                    "title": "归来",
                    "core_event": "主角拒绝签字",
                    "goal_conflict": "保住股权×家族逼迫",
                    "emotion_intensity": 8,
                    # opening_hook 缺失，需由 _synthesize_from_schema 补齐
                    "ending_hook": "证据出现",
                    "satisfaction_points": ["当众拒绝"],
                    "reversal": "主角掌握录音",
                    "paywall_hook": "录音内容未公开",
                    "rhythm_tag": "tight-heavy",
                    "foreshadowing": {"setup": ["怀表"], "payoff": []},
                    "hook_grade": "B",
                    "characters": ["林夏"],
                    "emotion_nodes": {"EV": {"value": 8}, "ET": {"value": 3}, "TP": {"content": "拒绝签字"}},
                }
            ]
        }
        skeleton = build_output_skeleton(schema, fixture=incomplete)
        self.assertIn("opening_hook", skeleton["episode_narrative_designs"][0])
        SchemaValidator().validate_file(
            skeleton, "schemas/artifacts/narrative_plan/1.schema.json"
        )

    def test_render_contract_block_returns_markdown(self) -> None:
        from apps.drama.services.schema_prompt_contract import render_contract_block

        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("narrative_plan")
        block = render_contract_block(
            "narrative_plan", schema, fixture=FIXTURES["narrative_plan"]
        )
        self.assertIn("artifact_key: narrative_plan", block)
        self.assertIn("episode_narrative_designs[].opening_hook", block)
        self.assertIn("```json", block)

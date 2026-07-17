from django.test import SimpleTestCase

from apps.drama.services.schema_prompt_contract import extract_required_paths


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

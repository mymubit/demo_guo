from __future__ import annotations

import unittest

from v6.engine.validators.story_bible import COMPONENTS, STAGE_ORDER, validate_component_references, validate_mode_source, validate_stage_ranges


class StoryBibleValidatorTests(unittest.TestCase):
    def test_original_and_adaptation_use_mode_specific_source(self):
        self.assertEqual(validate_mode_source("original", "project_brief", None), [])
        treatment = {key: [] for key in ["extracted_characters", "extracted_structure", "retained", "enhanced", "rewritten"]}
        treatment.update({"extracted_conflict": "conflict", "originality_report_version": 1})
        self.assertEqual(validate_mode_source("adaptation", "external_story", treatment), [])
        self.assertTrue(validate_mode_source("adaptation", "project_brief", treatment))

    def test_component_references_are_exact_and_versioned(self):
        valid = {name: {"schema": name, "schema_version": 1, "artifact_version": 1} for name in COMPONENTS}
        self.assertEqual(validate_component_references(valid), [])
        del valid["world_system"]
        self.assertTrue(validate_component_references(valid))

    def test_six_stages_are_ordered_contiguous_and_complete(self):
        stages = [{"name": name, "start_episode": index * 2 + 1, "end_episode": index * 2 + 2} for index, name in enumerate(STAGE_ORDER)]
        self.assertEqual(validate_stage_ranges(stages, 12), [])
        stages[2]["start_episode"] = 7
        self.assertTrue(validate_stage_ranges(stages, 12))

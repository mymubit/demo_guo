from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from build.lib.parameter_schema_generator import (  # noqa: E402
    generated_artifacts,
    generate_parameters_schema,
)
from build.lib.parameter_resolver import resolve_enum, resolve_max_items  # noqa: E402
from build.lib.schema_validator import SchemaValidator  # noqa: E402


class ParameterSchemaGenerationTests(unittest.TestCase):
    def test_generated_artifacts_match_committed_files(self):
        for relative_path, expected in generated_artifacts(ROOT).items():
            actual = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertEqual(actual, expected, relative_path)

    def test_entry_type_enum_from_orchestration(self):
        contract = json.loads(
            (ROOT / "schemas/generated/parameters.schema.json").read_text(encoding="utf-8")
        )
        entry_enum = set(contract["$defs"]["entry_type"]["enum"])
        self.assertEqual(entry_enum, {"original_track", "story_adapt"})

    def test_flavor_tags_max_items_from_theme_matrix(self):
        contract = json.loads(
            (ROOT / "schemas/generated/parameters.schema.json").read_text(encoding="utf-8")
        )
        parameters = (
            __import__("yaml")
            .safe_load((ROOT / "contracts/parameters.yaml").read_text(encoding="utf-8"))
            .get("parameters")
        )
        expected = resolve_max_items(parameters["flavor_tags"], ROOT)
        self.assertEqual(contract["$defs"]["flavor_tags"]["maxItems"], expected)

    def test_project_settings_fixture_validates_with_refs(self):
        validator = SchemaValidator(ROOT / "schemas")
        project = json.loads(
            (ROOT / "build/fixtures/config/project-settings.json").read_text(encoding="utf-8")
        )
        schema = validator.load(ROOT / "schemas/project-settings.v1.schema.json")
        validator.validate(project, schema)


class ParameterResolverTests(unittest.TestCase):
    def test_resolve_enum_for_entry_type(self):
        parameters = (
            __import__("yaml")
            .safe_load((ROOT / "contracts/parameters.yaml").read_text(encoding="utf-8"))
            .get("parameters")
        )
        values = resolve_enum(parameters["entry_type"], ROOT)
        self.assertEqual(values, ["original_track", "story_adapt"])

    def test_all_parameters_have_defs(self):
        parameters = (
            __import__("yaml")
            .safe_load((ROOT / "contracts/parameters.yaml").read_text(encoding="utf-8"))
            .get("parameters")
        )
        defs = generate_parameters_schema(ROOT)["$defs"]
        self.assertEqual(set(defs), set(parameters))


if __name__ == "__main__":
    unittest.main()

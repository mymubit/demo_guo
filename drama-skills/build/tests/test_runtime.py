from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "build"))

from build.lib.condition_eval import evaluate
from build.lib.config_resolver import (
    ConfigResolver,
    ConfigRevisionStore,
    OverlayPolicyError,
)
from build.lib.schema_validator import SchemaValidationError, SchemaValidator
from runtime.workflow_engine import (
    ConcurrencyError,
    WorkflowEngine,
    WorkflowError,
    detect_trend,
    resolve_latest_script,
)


def load_yaml(path: str):
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8")) or {}


class ConditionTests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "entry_type": "story_adapt",
            "enable_delivery": True,
            "deliverables": ["budget", "release"],
        }

    def test_string_equality(self):
        self.assertTrue(evaluate("entry_type == 'story_adapt'", self.context))

    def test_boolean_equality(self):
        self.assertTrue(evaluate("enable_delivery == true", self.context))

    def test_contains(self):
        self.assertTrue(evaluate("deliverables contains 'budget'", self.context))

    def test_missing_path_is_false(self):
        self.assertFalse(evaluate("missing == true", self.context))

    def test_unknown_expression_rejected(self):
        with self.assertRaises(ValueError):
            evaluate("entry_type != 'story_adapt'", self.context)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_yaml("manifest/config-policy.yaml")
        self.resolver = ConfigResolver(self.policy)
        self.seeds = {
            path: load_yaml(path) for path in self.policy["overlay_files"]
        }

    def test_allowed_overlay(self):
        overlay = {
            "overrides": {
                "foundation/constraints/quality-scoring.yaml": {
                    "grade_thresholds": {"B": 79}
                }
            }
        }
        resolved = self.resolver.apply_overlay(self.seeds, overlay)
        self.assertEqual(
            resolved["foundation/constraints/quality-scoring.yaml"][
                "grade_thresholds"
            ]["B"],
            79,
        )

    def test_protected_file_rejected(self):
        with self.assertRaises(OverlayPolicyError):
            self.resolver.apply_overlay(
                self.seeds, {"overrides": {"registry.yaml": {"version": "x"}}}
            )

    def test_protected_leaf_rejected(self):
        with self.assertRaises(OverlayPolicyError):
            self.resolver.apply_overlay(
                self.seeds,
                {
                    "overrides": {
                        "foundation/constraints/quality-scoring.yaml": {
                            "dimensions": []
                        }
                    }
                },
            )

    def test_seed_is_not_mutated(self):
        before = copy.deepcopy(self.seeds)
        self.resolver.apply_overlay(self.seeds, {"overrides": {}})
        self.assertEqual(before, self.seeds)

    def test_revision_rollback_appends_history(self):
        store = ConfigRevisionStore()
        store.append({"value": 1}, "admin", "init")
        store.append({"value": 2}, "admin", "change")
        rollback = store.rollback(1, "admin", "rollback")
        self.assertEqual(rollback.revision, 3)
        self.assertEqual(rollback.value, {"value": 1})


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine(
            load_yaml("orchestration/workflow-transitions.yaml")
        )

    def test_original_initial_phase(self):
        self.assertEqual(
            self.engine.create("p", "original_track")["current_phase"], "strategy"
        )

    def test_adapt_initial_phase(self):
        self.assertEqual(
            self.engine.create("p", "story_adapt")["current_phase"], "blueprint"
        )

    def test_unknown_entry_rejected(self):
        with self.assertRaises(WorkflowError):
            self.engine.create("p", "unknown")

    def test_optimistic_lock(self):
        state = self.engine.create("p", "original_track")
        with self.assertRaises(ConcurrencyError):
            self.engine.apply(state, "project_brief_completed", "c", 1)

    def test_idempotent_command(self):
        state = self.engine.create("p", "original_track")
        once = self.engine.apply(state, "project_brief_completed", "c", 0)
        twice = self.engine.apply(once, "project_brief_completed", "c", 0)
        self.assertEqual(once, twice)

    def test_latest_script_prefers_polished(self):
        result = resolve_latest_script(
            {"episode_scripts": "draft", "polished_script": "polished"}
        )
        self.assertEqual(result["value"], "polished")

    def test_latest_script_missing_rejected(self):
        with self.assertRaises(WorkflowError):
            resolve_latest_script({})

    def test_trend_stagnant(self):
        self.assertEqual(detect_trend([70, 70.5]), "stagnant")

    def test_trend_diverging(self):
        self.assertEqual(detect_trend([75, 70]), "diverging")

    def test_trend_oscillating(self):
        self.assertEqual(detect_trend([70, 75, 72]), "oscillating")


class ArtifactSchemaTests(unittest.TestCase):
    def setUp(self):
        self.validator = SchemaValidator(ROOT / "schemas" / "artifacts")
        self.fixtures = json.loads(
            (
                ROOT / "build/fixtures/artifacts/valid-artifacts.json"
            ).read_text(encoding="utf-8")
        )
        self.contract = load_yaml("contracts/artifacts.yaml")

    def test_all_valid_fixtures(self):
        for artifact_key, fixture in self.fixtures.items():
            schema_path = ROOT / self.contract["artifacts"][artifact_key]["schema_path"]
            schema = self.validator.load(schema_path)
            self.validator.validate(fixture, schema)

    def test_missing_required_rejected(self):
        fixture = copy.deepcopy(self.fixtures["project_brief"])
        fixture.pop("title")
        schema = self.validator.load(
            ROOT / self.contract["artifacts"]["project_brief"]["schema_path"]
        )
        with self.assertRaises(SchemaValidationError):
            self.validator.validate(fixture, schema)

    def test_invalid_enum_rejected(self):
        fixture = copy.deepcopy(self.fixtures["compliance_report"])
        fixture["overall_result"] = "未知"
        schema = self.validator.load(
            ROOT / self.contract["artifacts"]["compliance_report"]["schema_path"]
        )
        with self.assertRaises(SchemaValidationError):
            self.validator.validate(fixture, schema)


if __name__ == "__main__":
    unittest.main()

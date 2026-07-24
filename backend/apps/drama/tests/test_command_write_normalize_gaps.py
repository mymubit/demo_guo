# -*- coding: utf-8 -*-
"""全链路：命令写入产物空对象经 normalize 后必须过 schema。"""
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.artifact_normalize import normalize_artifact
from apps.drama.skills_bridge.recipe_map import COMMAND_RECIPES
from apps.drama.skills_bridge.validate import (
    _resolve_artifact_schema_path,
    validate_artifact_payload,
)
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class CommandWriteNormalizeGapTests(SimpleTestCase):
    """防止再出现「线上漏一个字段 → 用户反复重试」的回归。"""

    def setUp(self) -> None:
        self.settings = {
            "title": "全链路审计短剧",
            "entry_type": "original",
            "core_idea": "审计核心创意",
            "resolved_script_key": "episode_scripts",
        }

    def test_every_command_write_empty_payload_validates(self) -> None:
        writes = sorted(
            {w for recipe in COMMAND_RECIPES.values() for w in (recipe.get("writes") or [])}
        )
        self.assertTrue(writes)
        failures: list[str] = []
        for key in writes:
            try:
                _resolve_artifact_schema_path(
                    __import__(
                        "apps.drama.services.skills_loader", fromlist=["get_skills_loader"]
                    ).get_skills_loader(),
                    key,
                )
            except KeyError:
                continue
            out = normalize_artifact(key, {}, self.settings)
            errors = validate_artifact_payload(key, out)
            if errors:
                failures.append(f"{key}: {errors[:3]}")
        self.assertEqual(failures, [], failures)

    def test_omit_each_top_required_still_validates_for_schemaed_writes(self) -> None:
        from apps.drama.services.skills_loader import get_skills_loader
        from apps.core.schema_validator import SchemaValidator

        loader = get_skills_loader()
        validator = SchemaValidator(schema_root=loader.root)
        writes = sorted(
            {w for recipe in COMMAND_RECIPES.values() for w in (recipe.get("writes") or [])}
        )
        failures: list[str] = []
        for key in writes:
            try:
                sp = _resolve_artifact_schema_path(loader, key)
            except KeyError:
                continue
            schema = validator.load_schema(sp)
            required = list(schema.get("required") or [])
            base = normalize_artifact(key, {}, self.settings)
            if validate_artifact_payload(key, base):
                failures.append(f"{key}:base-invalid")
                continue
            for req in required:
                raw = dict(base)
                raw.pop(req, None)
                out = normalize_artifact(key, raw, self.settings)
                errors = validate_artifact_payload(key, out)
                if errors:
                    failures.append(f"{key}:omit:{req}:{errors[0]}")
        self.assertEqual(failures, [], failures)

    def test_extra_top_level_keys_are_stripped_when_schema_forbids(self) -> None:
        """additionalProperties=false 的产物：多吐字段必须被剥掉后仍过校验。"""
        from apps.drama.services.artifact_normalize import _schema_top_level_allowed_keys
        from apps.drama.services.skills_loader import get_skills_loader
        from apps.core.schema_validator import SchemaValidator

        _schema_top_level_allowed_keys.cache_clear()
        loader = get_skills_loader()
        validator = SchemaValidator(schema_root=loader.root)
        writes = sorted(
            {w for recipe in COMMAND_RECIPES.values() for w in (recipe.get("writes") or [])}
        )
        failures: list[str] = []
        for key in writes:
            try:
                sp = _resolve_artifact_schema_path(loader, key)
            except KeyError:
                continue
            schema = validator.load_schema(sp)
            if schema.get("additionalProperties") is not False:
                continue
            raw = normalize_artifact(key, {}, self.settings)
            raw = dict(raw)
            raw["__llm_extra_field__"] = "should-be-stripped"
            raw["total_score"] = 99
            out = normalize_artifact(key, raw, self.settings)
            if "__llm_extra_field__" in out:
                failures.append(f"{key}:extra-not-stripped")
                continue
            errors = validate_artifact_payload(key, out)
            if errors:
                failures.append(f"{key}:{errors[0]}")
        self.assertEqual(failures, [], failures)

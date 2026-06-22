# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.agent.models import ReviewScoringDimension, ReviewScoringPreset
from apps.skill.config.portal.creation_form import CreationFormOverrideService
from apps.skill.config.portal.review_scoring import ReviewScoringService
from apps.skill.models import CreationFormOverrideConfig
from apps.skill.models_creation_form import CreationPlatform
from apps.skill.services.creation_form_atomic_sync import migrate_from_overrides
from apps.skill.services.review_scoring_atomic import seed_presets_from_defaults


class CreationFormAtomicTests(TestCase):
    def test_atomic_platforms_override_json(self):
        CreationFormOverrideConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "overrides": {
                    "platforms": [{"key": "legacy", "name": "旧平台", "description": ""}],
                },
                "episode_settings": {},
            },
        )
        migrate_from_overrides(overwrite=True)
        CreationPlatform.objects.filter(config_key="default", item_key="legacy").update(is_active=False)
        CreationPlatform.objects.create(
            config_key="default",
            item_key="douyin",
            name="抖音原子",
            description="原子表",
            sort_order=0,
            is_active=True,
        )
        platforms = CreationFormOverrideService.get_platforms()
        keys = {p["key"] for p in platforms}
        self.assertIn("douyin", keys)
        self.assertNotIn("legacy", keys)


class ReviewScoringAtomicTests(TestCase):
    def test_resolve_reads_active_preset(self):
        seed_presets_from_defaults(overwrite=True)
        strict = ReviewScoringPreset.objects.get(preset_id="strict")
        ReviewScoringPreset.objects.update(is_active=False)
        strict.is_active = True
        strict.save(update_fields=["is_active"])
        cfg = ReviewScoringService.resolve()
        self.assertEqual(cfg["pass_threshold"], strict.pass_threshold)
        self.assertTrue(
            ReviewScoringDimension.objects.filter(preset=strict, dimension_key="rhythm").exists()
        )

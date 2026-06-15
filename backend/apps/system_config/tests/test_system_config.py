from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.system_config.models import SystemConfigCategory, SystemConfigItem
from apps.system_config.services import SystemConfigService, get_config, get_int
from apps.system_config.validators import normalize_value, validate_schema


class SystemConfigValidatorTests(TestCase):
    def test_normalize_value_by_type(self):
        self.assertEqual(normalize_value(SystemConfigItem.ValueType.INT, "12"), 12)
        self.assertEqual(normalize_value(SystemConfigItem.ValueType.FLOAT, "1.5"), 1.5)
        self.assertIs(normalize_value(SystemConfigItem.ValueType.BOOL, "true"), True)
        self.assertEqual(normalize_value(SystemConfigItem.ValueType.ARRAY, [1, 2]), [1, 2])

    def test_validate_schema_rejects_out_of_range_value(self):
        with self.assertRaises(ValidationError):
            validate_schema(11, {"min": 1, "max": 10})


class SystemConfigServiceTests(TestCase):
    def test_seed_defaults_and_read_config(self):
        result = SystemConfigService.seed_defaults()

        self.assertGreaterEqual(result["created_categories"], 1)
        self.assertEqual(get_config("system.site_name"), "ScriptForge 短剧创作平台")
        self.assertEqual(get_int("creation.max_outline_chars"), 8000)

    def test_public_config_payload_only_returns_public_non_sensitive_items(self):
        category = SystemConfigCategory.objects.create(code="test", name="测试")
        SystemConfigItem.objects.create(
            category=category,
            config_key="test.public",
            config_name="公开配置",
            value_type=SystemConfigItem.ValueType.STRING,
            value="ok",
            default_value="ok",
            is_active=True,
            is_public=True,
        )
        SystemConfigItem.objects.create(
            category=category,
            config_key="test.secret",
            config_name="敏感配置",
            value_type=SystemConfigItem.ValueType.STRING,
            value="secret",
            default_value="secret",
            is_active=True,
            is_public=True,
            is_sensitive=True,
        )

        payload = SystemConfigService.public_config_payload()

        self.assertEqual(payload["values"]["test.public"], "ok")
        self.assertNotIn("test.secret", payload["values"])

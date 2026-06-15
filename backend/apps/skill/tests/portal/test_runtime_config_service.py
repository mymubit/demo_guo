# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, TestCase, override_settings

from apps.skill.models import SkillConfig
from apps.skill.config.portal.runtime_config import RuntimeConfigService


class RuntimeConfigServiceTests(TestCase):
    def test_dj_queue_queues_reads_skill_config(self):
        obj = SkillConfig(config_key="runtime.dj_queue.queues", description="test")
        obj.set_encrypted_value("creation,custom")
        obj.save()
        self.assertEqual(RuntimeConfigService.dj_queue_queues(), ["creation", "custom"])


class RuntimeConfigEnvFallbackTests(SimpleTestCase):
    @override_settings(DJ_QUEUE_QUEUES=["creation", "default"])
    def test_dj_queue_queues_falls_back_to_settings(self):
        queues = RuntimeConfigService.dj_queue_queues()
        self.assertIn("creation", queues)

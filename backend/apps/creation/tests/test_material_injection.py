# -*- coding: utf-8 -*-
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.library.models import ReferenceMaterial, ReferenceMaterialInjection
from apps.creation.models import Project


class MaterialInjectionRuntimeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            phone="13900009901",
            password="test-pass-123",
        )
        self.project = Project.objects.create(
            user=self.user,
            theme="测试主题",
            title="测试项目",
        )
        AgentDefinitionService.ensure_defaults()
        agents = AgentDefinitionService.active_agents()
        self.agent = agents[0] if agents else None
        self.assertIsNotNone(self.agent)

    def test_build_agent_input_without_materials(self):
        self.agent.input_contract = {"required_artifacts": [], "optional_artifacts": []}
        self.agent.save(update_fields=["input_contract"])
        payload = IndependentAgentService.build_agent_input(self.project, self.agent, {})
        self.assertNotIn("reference_materials", payload)

    def test_build_agent_input_includes_injected_materials(self):
        self.agent.input_contract = {"required_artifacts": [], "optional_artifacts": []}
        self.agent.save(update_fields=["input_contract"])
        material = ReferenceMaterial.objects.create(
            user=self.user,
            name="参考小说",
            material_type=ReferenceMaterial.TYPE_NOVEL,
            parse_status=ReferenceMaterial.STATUS_READY,
            parsed_content={
                "world": {"setting": "都市"},
                "characters": [{"name": "主角"}],
            },
        )
        ReferenceMaterialInjection.objects.create(
            project=self.project,
            material=material,
            injected_fields=["world", "characters"],
        )
        payload = IndependentAgentService.build_agent_input(self.project, self.agent, {})
        self.assertIn("reference_materials", payload)
        self.assertEqual(len(payload["reference_materials"]), 1)
        self.assertEqual(payload["reference_materials"][0]["material_name"], "参考小说")
        self.assertIn("world", payload["reference_materials"][0])

    def test_build_agent_input_via_run_params_material_id(self):
        self.agent.input_contract = {"required_artifacts": [], "optional_artifacts": []}
        self.agent.save(update_fields=["input_contract"])
        material = ReferenceMaterial.objects.create(
            user=self.user,
            name="参数注入素材",
            material_type=ReferenceMaterial.TYPE_NOVEL,
            parse_status=ReferenceMaterial.STATUS_READY,
            parsed_content={"world": {"setting": "古代"}},
        )
        payload = IndependentAgentService.build_agent_input(
            self.project,
            self.agent,
            {"material_id": str(material.id), "material_fields": ["world"]},
        )
        self.assertIn("reference_materials", payload)
        self.assertTrue(any("world" in item for item in payload["reference_materials"]))

# -*- coding: utf-8 -*-
"""后台：Agent Registry 配置读写。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.agent.registry import AgentRegistryConfigService
from apps.agent.definition_service import AgentDefinitionService
from apps.agent.models import (
    AgentDefinition,
    AgentKnowledgeBinding,
    AgentKnowledgeItem,
    AgentPromptVersion,
)

from apps.console.responses import api_fail, api_ok


class AgentRegistryConfigView(APIView):
    """GET/PUT /api/admin/agent/registry/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(AgentRegistryConfigService.admin_payload())

    def put(self, request):
        data = request.data or {}
        registry = data.get("registry")
        if registry is None:
            return api_fail("缺少 registry 字段")
        try:
            row = AgentRegistryConfigService.save_registry(
                registry,
                note=str(data.get("note") or "后台保存")[:255],
                activate=data.get("activate", True) is not False,
            )
        except ValueError as exc:
            return api_fail(str(exc))
        payload = AgentRegistryConfigService.admin_payload()
        payload["saved_id"] = str(row.id)
        return api_ok(payload, message="技能注册表已保存并生效")


class AgentRegistryMigrateView(APIView):
    """POST /api/admin/agent/registry/migrate/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        from apps.agent.routes import AgentLlmRouteService

        AgentRegistryConfigService.ensure_defaults()
        seeded = AgentLlmRouteService.seed_defaults()
        migrated = AgentRegistryConfigService.migrate_pipeline_skill_config()
        payload = AgentRegistryConfigService.admin_payload()
        payload["migrated_count"] = migrated
        payload["seeded_routes"] = seeded
        return api_ok(payload, message=f"已迁移 {migrated} 个技能配置")


class AgentRegistryImportView(APIView):
    """POST /api/admin/agent/registry/import/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        overwrite = (request.data or {}).get("overwrite", True) is not False
        try:
            AgentRegistryConfigService.import_from_file(overwrite=overwrite)
        except ValueError as exc:
            return api_fail(str(exc))
        except FileNotFoundError as exc:
            return api_fail(str(exc))
        return api_ok(AgentRegistryConfigService.admin_payload(), message="已从磁盘 registry.json 导入")


class IndependentAgentListView(APIView):
    """GET/POST /api/admin/agent/definitions/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        AgentDefinitionService.ensure_defaults()
        return api_ok({"agents": AgentDefinitionService.admin_list()})

    def post(self, request):
        data = request.data or {}
        agent_id = str(data.get("agent_id") or "").strip()
        if not agent_id:
            return api_fail("缺少 agent_id")
        row, _ = AgentDefinition.objects.update_or_create(
            agent_id=agent_id,
            defaults={
                "name": str(data.get("name") or agent_id)[:128],
                "name_zh": str(data.get("name_zh") or data.get("name") or agent_id)[:128],
                "description": str(data.get("description") or ""),
                "category": str(data.get("category") or "creation")[:64],
                "workspace_order": data.get("workspace_order"),
                "is_enabled": data.get("is_enabled", True) is not False,
                "lifecycle_status": str(data.get("lifecycle_status") or AgentDefinition.LifecycleStatus.DRAFT),
                "default_output_artifact_key": str(data.get("default_output_artifact_key") or "")[:64],
                "input_contract": data.get("input_contract") or {},
                "output_contract": data.get("output_contract") or {},
                "runtime_policy": data.get("runtime_policy") or {},
                "ui_schema": data.get("ui_schema") or {},
            },
        )
        return api_ok({"id": str(row.id), "agent_id": row.agent_id}, message="Agent 已保存")


class IndependentAgentDetailView(APIView):
    """GET/PUT /api/admin/agent/definitions/<agent_id>/"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, agent_id: str):
        return AgentDefinition.objects.filter(agent_id=agent_id).first()

    def get(self, request, agent_id: str):
        row = self.get_object(agent_id)
        if not row:
            return api_fail("Agent 不存在")
        return api_ok({
            "agent": {
                "agent_id": row.agent_id,
                "name": row.name,
                "name_zh": row.name_zh,
                "description": row.description,
                "is_enabled": row.is_enabled,
                "lifecycle_status": row.lifecycle_status,
                "input_contract": row.input_contract,
                "output_contract": row.output_contract,
                "runtime_policy": row.runtime_policy,
                "ui_schema": row.ui_schema,
                "health": AgentDefinitionService.health(row),
            }
        })

    def put(self, request, agent_id: str):
        row = self.get_object(agent_id)
        if not row:
            return api_fail("Agent 不存在")
        data = request.data or {}
        for field in [
            "name",
            "name_zh",
            "description",
            "category",
            "workspace_order",
            "is_enabled",
            "lifecycle_status",
            "default_output_artifact_key",
            "input_contract",
            "output_contract",
            "runtime_policy",
            "ui_schema",
        ]:
            if field in data:
                setattr(row, field, data[field])
        row.save()
        return api_ok({"agent_id": row.agent_id, "health": AgentDefinitionService.health(row)}, message="Agent 已更新")


class IndependentPromptListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, agent_id: str):
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return api_fail("Agent 不存在")
        rows = agent.prompt_versions.order_by("-created_at")
        return api_ok({
            "prompts": [
                {
                    "id": str(row.id),
                    "version": row.version,
                    "system_prompt": row.system_prompt,
                    "user_prompt_template": row.user_prompt_template,
                    "output_format_prompt": row.output_format_prompt,
                    "constraints_prompt": row.constraints_prompt,
                    "few_shot_examples": row.few_shot_examples,
                    "is_active": row.is_active,
                    "change_notes": row.change_notes,
                }
                for row in rows
            ]
        })

    def post(self, request, agent_id: str):
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return api_fail("Agent 不存在")
        data = request.data or {}
        version = str(data.get("version") or "").strip()
        if not version:
            return api_fail("缺少 version")
        row, _ = AgentPromptVersion.objects.update_or_create(
            agent=agent,
            version=version,
            defaults={
                "system_prompt": str(data.get("system_prompt") or ""),
                "user_prompt_template": str(data.get("user_prompt_template") or ""),
                "output_format_prompt": str(data.get("output_format_prompt") or ""),
                "constraints_prompt": str(data.get("constraints_prompt") or ""),
                "few_shot_examples": data.get("few_shot_examples") or [],
                "change_notes": str(data.get("change_notes") or ""),
                "created_by": str(getattr(request.user, "id", "") or ""),
            },
        )
        return api_ok({"id": str(row.id), "version": row.version}, message="Prompt 已保存")


class IndependentPromptActivateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, agent_id: str, version: str):
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return api_fail("Agent 不存在")
        prompt = agent.prompt_versions.filter(version=version).first()
        if not prompt:
            return api_fail("Prompt 版本不存在")
        agent.prompt_versions.update(is_active=False)
        prompt.is_active = True
        prompt.save(update_fields=["is_active", "updated_at"])
        return api_ok({"agent_id": agent.agent_id, "version": version}, message="Prompt 已激活")


class IndependentKnowledgeListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        rows = AgentKnowledgeItem.objects.order_by("category", "priority", "knowledge_id")[:200]
        return api_ok({
            "knowledge": [
                {
                    "id": str(row.id),
                    "knowledge_id": row.knowledge_id,
                    "title": row.title,
                    "category": row.category,
                    "source_origin": row.source_origin,
                    "tags": row.tags,
                    "is_enabled": row.is_enabled,
                    "checksum": row.checksum,
                }
                for row in rows
            ]
        })

    def post(self, request):
        data = request.data or {}
        knowledge_id = str(data.get("knowledge_id") or "").strip()
        if not knowledge_id:
            return api_fail("缺少 knowledge_id")
        row, _ = AgentKnowledgeItem.objects.update_or_create(
            knowledge_id=knowledge_id,
            defaults={
                "title": str(data.get("title") or knowledge_id)[:255],
                "category": str(data.get("category") or AgentKnowledgeItem.Category.KNOWLEDGE),
                "content_text": str(data.get("content_text") or ""),
                "content_json": data.get("content_json") or {},
                "tags": data.get("tags") or [],
                "applies_to_agents": data.get("applies_to_agents") or [],
                "priority": int(data.get("priority") or 100),
                "is_enabled": data.get("is_enabled", True) is not False,
            },
        )
        return api_ok({"id": str(row.id), "knowledge_id": row.knowledge_id}, message="Knowledge 已保存")


class IndependentKnowledgeBindingView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, agent_id: str):
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return api_fail("Agent 不存在")
        rows = agent.knowledge_bindings.select_related("knowledge").order_by("order_index", "knowledge__knowledge_id")
        return api_ok({
            "bindings": [
                {
                    "id": str(row.id),
                    "knowledge_id": row.knowledge.knowledge_id,
                    "knowledge_title": row.knowledge.title,
                    "binding_type": row.binding_type,
                    "inject_position": row.inject_position,
                    "order_index": row.order_index,
                    "max_chars": row.max_chars,
                    "is_enabled": row.is_enabled,
                }
                for row in rows
            ]
        })

    def post(self, request, agent_id: str):
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return api_fail("Agent 不存在")
        data = request.data or {}
        knowledge = AgentKnowledgeItem.objects.filter(knowledge_id=data.get("knowledge_id")).first()
        if not knowledge:
            return api_fail("Knowledge 不存在")
        binding, _ = AgentKnowledgeBinding.objects.update_or_create(
            agent=agent,
            knowledge=knowledge,
            binding_type=str(data.get("binding_type") or AgentKnowledgeBinding.BindingType.OPTIONAL),
            inject_position=str(data.get("inject_position") or AgentKnowledgeBinding.InjectPosition.CONTEXT),
            defaults={
                "order_index": int(data.get("order_index") or 0),
                "max_chars": data.get("max_chars"),
                "condition_expr": str(data.get("condition_expr") or "")[:255],
                "is_enabled": data.get("is_enabled", True) is not False,
            },
        )
        return api_ok({"id": str(binding.id)}, message="Binding 已保存")


class IndependentKnowledgeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, knowledge_id: str):
        row = AgentKnowledgeItem.objects.filter(knowledge_id=knowledge_id).first()
        if not row:
            return api_fail("Knowledge 不存在", code=404)
        return api_ok({
            "knowledge": {
                "id": str(row.id),
                "knowledge_id": row.knowledge_id,
                "title": row.title,
                "category": row.category,
                "source_origin": row.source_origin,
                "content_text": row.content_text,
                "content_json": row.content_json or {},
                "tags": row.tags,
                "applies_to_agents": row.applies_to_agents,
                "priority": row.priority,
                "is_enabled": row.is_enabled,
                "checksum": row.checksum,
            }
        })

    def delete(self, request, knowledge_id: str):
        row = AgentKnowledgeItem.objects.filter(knowledge_id=knowledge_id).first()
        if not row:
            return api_fail("Knowledge 不存在", code=404)
        row.is_enabled = False
        row.save(update_fields=["is_enabled", "updated_at"])
        return api_ok({"knowledge_id": knowledge_id}, message="Knowledge 已停用")


class IndependentKnowledgeBindingDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, agent_id: str, binding_id: str):
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return api_fail("Agent 不存在")
        deleted, _ = agent.knowledge_bindings.filter(id=binding_id).delete()
        if not deleted:
            return api_fail("Binding 不存在", code=404)
        return api_ok({"id": binding_id}, message="Binding 已删除")


class IndependentAgentRunsListView(APIView):
    """GET /api/admin/agent/runs/ — 最近独立 Agent 运行（可按 agent_id 过滤）。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from django.db.models import Sum

        from apps.creation.models import AgentExecutionRun
        from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
        from apps.skill.models import LlmUsageLog

        agent_id = str(request.query_params.get("agent_id") or "").strip()
        try:
            limit = int(request.query_params.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))

        qs = AgentExecutionRun.objects.select_related("project").order_by("-started_at")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        runs = list(qs[:limit])
        run_ids = [run.id for run in runs]
        cost_by_run = {
            str(row["execution_run_id"]): float(row["cost"] or 0)
            for row in LlmUsageLog.objects.filter(execution_run_id__in=run_ids)
            .values("execution_run_id")
            .annotate(cost=Sum("estimated_cost_yuan"))
        }
        items = []
        for run in runs:
            payload = AgentExecutionRunService.serialize_run(run, include_sensitive=True, include_sub_skills=True)
            payload.update({
                "project_id": str(run.project_id),
                "project_title": (run.project.title or run.project.theme or "")[:120],
                "estimated_cost_yuan": cost_by_run.get(str(run.id), 0),
            })
            items.append(payload)
        return api_ok({"runs": items, "limit": limit, "agent_id": agent_id or None})

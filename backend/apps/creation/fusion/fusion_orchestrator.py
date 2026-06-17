# -*- coding: utf-8 -*-
# ⚠️ [legacy] 旧引擎 —— FusionOrchestrator
# =========================================================
# 【P0】本文件已下线：所有创作请求已统一走新引擎 WorkflowEngine。
#
# 下线说明（2026-06-17）：
#   • 新引擎通过 OrchestrationAdapter 统一入口
#   • 旧 FusionOrchestrator 不再被任何代码路径调用
#   • 保留本文件 30 天观察期后删除（预计 2026-07-17）
#
# 新调用路径：
#   OrchestrationAdapter.run(project, user_id, ...)
#     → WorkflowScheduler.start_for_project()
#       → WorkflowInstance.objects.create(...)
#         → run_workflow_instance.delay()
#           → WorkflowEngine.run()
#             → SkillBridge.run()
#               → SkillInvoker.invoke() 或 Python 函数
#
# 如需查阅旧逻辑用于迁移参考，请保留此文件；否则请删除。
# =========================================================
"""
主链执行基础设施：进度、artifact 落库、CLI/配置桥接。

业务调度统一由 AgentOrchestrator 负责；本模块不再硬编码 node → Agent 映射。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from apps.common.user_messages import humanize_pipeline_error, humanize_user_message
from apps.workflow.fusion import FusionCliRunner, FusionNodeRegistry, get_artifact_registry, get_fusion_config
from apps.workflow.fusion.prompt_builder import FusionPromptBuilder
from apps.workflow.fusion.ssot_catalog import get_ssot_catalog
from apps.skill.llm.chat import LlmService, LlmServiceError

from ..artifact_renderer import episode_scripts_to_legacy_scripts
from ..artifact_service import get_artifact, save_artifact
from ..models import CreationNode, Project
from ..services import refresh_project_progress
from ..display.structure_display import sync_project_title_from_structure
from ..pipeline_debug_log import (
    log_fusion_node_begin,
    log_fusion_node_done,
    log_fusion_node_fail,
    summarize_loaded_artifacts,
)

logger = logging.getLogger(__name__)

_NODE_IDS_1_5_CACHE: Optional[List[str]] = None


def _fusion_node_ids_1_5() -> List[str]:
    global _NODE_IDS_1_5_CACHE
    if _NODE_IDS_1_5_CACHE is None:
        _NODE_IDS_1_5_CACHE = get_artifact_registry().fusion_node_ids_1_5()
    return _NODE_IDS_1_5_CACHE


class FusionOrchestrator:
    def __init__(self, project: Project, *, dry_run: bool = False):
        self.project = project
        self.dry_run = dry_run
        self.config = get_fusion_config()
        self.catalog = get_ssot_catalog()
        pack_id = str(project.pipeline_pack_id) if getattr(project, "pipeline_pack_id", None) else None
        self.registry = FusionNodeRegistry(self.config, pack_id=pack_id)
        self.artifact_registry = get_artifact_registry(self.config, pack_id=pack_id)
        self.prompts = FusionPromptBuilder(self.config)
        self.runner = FusionCliRunner(self.config)
        self.work_dir = Path(
            getattr(settings, "CREATION_FUSION_WORK_DIR", "/tmp/scriptforge_fusion")
        )
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.strict_schema = getattr(settings, "FUSION_SCHEMA_STRICT", False)

    def load_artifacts_from_db(self) -> Dict[str, Any]:
        """从 DB 加载已确认的上游产物（分步模式）。"""
        artifacts: Dict[str, Any] = {}
        for key in self.artifact_registry.main_chain_artifact_keys_nodes_1_5():
            val = get_artifact(self.project, key)
            if val:
                artifacts[key] = val
        return artifacts

    def run(self) -> Dict[str, Any]:
        artifacts: Dict[str, Any] = {}
        errors: List[str] = []

        for node_id in _fusion_node_ids_1_5():
            try:
                payload = self._run_single_node(node_id, artifacts)
                key = self.artifact_registry.primary_artifact_for_fusion_node(node_id)
                if not key:
                    raise ValueError(f"未配置节点产物: {node_id}")
                artifacts[key] = payload
                if self.dry_run:
                    self._artifacts_cache = getattr(self, "_artifacts_cache", {})
                    self._artifacts_cache[key] = payload
                self._persist_node(node_id, payload)
            except Exception as exc:  # noqa: BLE001
                logger.exception("节点 %s 失败 project=%s", node_id, self.project.id)
                msg = humanize_pipeline_error(f"{node_id}: {exc}")
                errors.append(msg)
                self._mark_node_failed(node_id, humanize_user_message(str(exc), default="节点执行失败"))
                self._flush_progress()
                return self._build_result(artifacts, status="error", errors=errors)

        return self._build_result(artifacts, status="completed", errors=errors)

    def _run_single_node(self, node_id: str, artifacts: Dict[str, Any]) -> dict:
        """委托调度引擎执行 Agent，FusionOrchestrator 仅负责进度与落库基础设施。"""
        from apps.workflow.fusion import FusionNodeRegistry

        from ..orchestration.orchestrator import run_pipeline_step_by_index

        registry = FusionNodeRegistry(self.config)
        node_index = None
        for node in registry.main_chain_nodes():
            if node.get("fusion_node_id") == node_id:
                node_index = node.get("index")
                break
        if not node_index:
            raise ValueError(f"未知节点 {node_id}")

        out = run_pipeline_step_by_index(self.project, int(node_index))
        if out.get("status") == "error":
            raise ValueError("; ".join(out.get("errors") or ["节点执行失败"]))

        key = self.artifact_registry.primary_artifact_for_fusion_node(node_id)
        if not key:
            raise ValueError(f"未配置节点产物: {node_id}")
        payload = get_artifact(self.project, key) or {}
        if not payload:
            raise ValueError(f"节点 {node_id} 执行完成但未产生产物")
        return payload

    def _require_llm(self, node_id: str) -> None:
        if not LlmService.is_enabled():
            raise LlmServiceError(
                f"{node_id} 需要 LLM：请设置 FUSION_LLM_ENABLED=true 并配置 llm.enabled / api_key / base_url"
            )

    def generate_outline_episode_range(
        self,
        artifacts: Dict[str, Any],
        from_episode: int,
        to_episode: int,
        *,
        existing: Optional[dict] = None,
        framework_only: bool = False,
    ) -> dict:
        """兼容入口：委托 OutlineAgentEngine。"""
        from ..orchestration.outline_engine import OutlineAgentEngine

        engine = OutlineAgentEngine(self)
        return engine.run_workspace(
            artifacts,
            framework_only=framework_only,
            from_episode=from_episode,
            to_episode=to_episode,
            existing=existing,
        )

    def generate_script_episode_range(
        self,
        artifacts: Dict[str, Any],
        from_episode: int,
        to_episode: int,
        *,
        existing: Optional[dict] = None,
    ) -> dict:
        """兼容入口：委托 ScriptAgentEngine。"""
        from ..orchestration.script_engine import ScriptAgentEngine

        engine = ScriptAgentEngine(self)
        return engine.run_workspace(
            artifacts,
            from_episode=from_episode,
            to_episode=to_episode,
            existing=existing,
        )

    def _persist_node(self, node_id: str, payload: dict) -> None:
        key = self.artifact_registry.primary_artifact_for_fusion_node(node_id)
        if not key:
            raise ValueError(f"未配置节点产物: {node_id}")
        if not self.dry_run:
            save_artifact(self.project, key, payload)
            if node_id == "node-2-structure":
                sync_project_title_from_structure(self.project, payload)
            log_fusion_node_done(
                project_id=self.project.id,
                node_id=node_id,
                artifact_key=key,
                payload=payload,
            )
            if self.project.pipeline_mode == Project.MODE_AUTO:
                idx = self._node_index(node_id)
                if idx:
                    from apps.billing.services import BillingService

                    BillingService.charge_node(
                        self.project.user,
                        idx,
                        reference_id=f"{self.project.id}:n{idx}",
                    )
        summary = self._summarize(node_id, payload)
        self._mark_node_completed(node_id, summary)
        self._update_fusion_status(node_id)

    def _summarize(self, node_id: str, payload: dict) -> str:
        if node_id == "node-1-input":
            return payload.get("workingTitle") or self.project.theme
        if node_id == "node-2-structure":
            return f"{payload.get('totalEpisodes')}集 · 6阶段结构"
        if node_id == "node-3-character":
            n = len(payload.get("protagonists") or []) + len(payload.get("antagonists") or [])
            return f"角色体系 · {n}+人设"
        if node_id == "node-4-outline":
            return f"{len(payload.get('episodes') or [])}集大纲"
        if node_id == "node-5-script":
            eps = payload.get("episodes") or []
            passed = sum(1 for e in eps if (e.get("gateLog") or {}).get("passed"))
            if passed:
                return f"{len(eps)}集剧本 · gate {passed}/{len(eps)} 通过"
            return f"{len(eps)}集剧本"
        return "完成"

    def _node_index(self, node_id: str) -> Optional[int]:
        for n in self.registry.main_chain_nodes():
            if n["fusion_node_id"] == node_id:
                return n["index"]
        return None

    def _node_label(self, node_id: str) -> str:
        for n in self.registry.main_chain_nodes():
            if n["fusion_node_id"] == node_id:
                return n.get("name") or node_id
        return node_id

    def _flush_progress(
        self,
        *,
        node_id: str | None = None,
        summary: str | None = None,
        sub_pct: int | None = None,
    ) -> None:
        if self.dry_run:
            return
        if node_id and summary is not None:
            idx = self._node_index(node_id)
            if idx:
                CreationNode.objects.filter(
                    project=self.project, node_index=idx
                ).update(summary_text=summary[:500])

        pct: int | None = None
        if node_id is not None and sub_pct is not None:
            idx = self._node_index(node_id) or 1
            total = max(1, self.project.total_nodes or len(_fusion_node_ids_1_5()))
            base = int((idx - 1) / total * 100)
            span = max(1, int(100 / total))
            pct = min(99, base + span * sub_pct // 100)

        refresh_project_progress(self.project, progress_percent=pct)

    def _mark_node_running(self, node_id: str) -> None:
        if self.dry_run:
            return
        idx = self._node_index(node_id)
        if idx is None:
            return
        label = self._node_label(node_id)
        CreationNode.objects.filter(project=self.project, node_index=idx).update(
            status=CreationNode.STATUS_RUNNING,
            started_at=timezone.now(),
            summary_text=f"正在执行 · {label}"[:500],
        )
        self.project.current_node_index = idx
        self.project.save(update_fields=["current_node_index", "updated_at"])
        self._flush_progress(node_id=node_id, summary=f"正在执行 · {label}", sub_pct=0)

    def _mark_node_completed(self, node_id: str, summary: str) -> None:
        if self.dry_run:
            return
        idx = self._node_index(node_id)
        if idx is None:
            return
        CreationNode.objects.filter(project=self.project, node_index=idx).update(
            status=CreationNode.STATUS_COMPLETED,
            summary_text=summary[:500],
            completed_at=timezone.now(),
        )
        pct = self._progress_for_node(idx)
        self.project.current_node_index = idx
        self.project.progress_percent = pct
        refresh_project_progress(self.project, progress_percent=pct)

    def _progress_for_node(self, node_index: int, *, awaiting: bool = False) -> int:
        total = max(1, self.project.total_nodes or len(_fusion_node_ids_1_5()))
        if awaiting:
            return min(99, int(node_index / total * 100))
        return min(100, int(node_index / total * 100))

    def _mark_node_failed(self, node_id: str, error: str) -> None:
        if self.dry_run:
            return
        idx = self._node_index(node_id)
        if idx is None:
            return
        CreationNode.objects.filter(project=self.project, node_index=idx).update(
            status=CreationNode.STATUS_FAILED,
            error_message=error[:500],
            summary_text="执行失败",
        )

    def _update_fusion_status(self, node_id: str) -> None:
        if self.dry_run:
            return
        self.project.fusion_status = self.registry.status_for_fusion_node(node_id)
        self.project.skill_version = self.config.version
        self.project.save(update_fields=["fusion_status", "skill_version", "updated_at"])

    def _build_result(self, artifacts: Dict[str, Any], *, status: str, errors: List[str]) -> dict:
        brief = artifacts.get("project_brief") or {}
        structure = artifacts.get("structure_plan") or {}
        characters = artifacts.get("character_bible") or {}
        outline = artifacts.get("series_outline") or {}
        scripts_schema = artifacts.get("episode_scripts") or {}
        legacy_scripts = episode_scripts_to_legacy_scripts(scripts_schema) if scripts_schema else {}

        return {
            "status": status,
            "project_brief": brief,
            "structure": structure,
            "characters": characters,
            "outlines": outline,
            "scripts": legacy_scripts,
            "review": {},
            "export": self._minimal_export(brief, legacy_scripts),
            "errors": errors,
            "artifacts": artifacts,
        }

    def _minimal_export(self, brief: dict, scripts: dict) -> dict:
        title = brief.get("workingTitle") or self.project.title
        html_parts = [f'<div class="creation-result"><h2>{title}</h2>']
        for ep in (scripts.get("episodes") or [])[:5]:
            html_parts.append(f"<h3>第{ep.get('episode')}集</h3>")
            html_parts.append(f"<pre>{ep.get('full_script_text', '')[:800]}</pre>")
        html_parts.append("</div>")
        return {
            "total_files": 1,
            "rendered_html": "".join(html_parts),
            "rendered_progress_html": "",
        }


def run_fusion_nodes_for_project(project: Project) -> Dict[str, Any]:
    return FusionOrchestrator(project).run()


def run_fusion_node_by_index(
    project: Project,
    node_index: int,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_from: Optional[int] = None,
    outline_to: Optional[int] = None,
) -> Dict[str, Any]:
    """分步/工作台：委托 AgentOrchestrator 执行（registry 驱动）。"""
    from ..orchestration.orchestrator import run_pipeline_step_by_index

    registry = FusionNodeRegistry()
    node_id = registry.fusion_node_id_for_index(node_index) or f"node-{node_index}"
    runner_type = registry.runner_type_for_index(node_index) or "fusion_node"
    if runner_type not in ("fusion_node", "fusion_review", "fusion_score", ""):
        raise ValueError(f"节点 {node_index} 不可由调度引擎执行")

    log_fusion_node_begin(
        project_id=project.id,
        node_id=node_id,
        node_index=node_index,
        extra={
            "runnerType": runner_type,
            "scriptFrom": script_from,
            "scriptTo": script_to,
            "outlineMode": outline_mode,
            "outlineFrom": outline_from,
            "outlineTo": outline_to,
        },
    )
    out = run_pipeline_step_by_index(
        project,
        node_index,
        script_from=script_from,
        script_to=script_to,
        outline_mode=outline_mode,
        outline_from=outline_from,
        outline_to=outline_to,
    )
    if out.get("status") == "error":
        msg = "; ".join(out.get("errors") or ["节点执行失败"])
        log_fusion_node_fail(
            project_id=project.id,
            node_id=node_id,
            node_index=node_index,
            error=msg,
            upstream=None,
        )
        orch = FusionOrchestrator(project)
        orch._mark_node_failed(node_id, humanize_user_message(msg, default="节点执行失败"))
        orch._flush_progress()
    return out

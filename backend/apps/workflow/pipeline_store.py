# -*- coding: utf-8 -*-
"""Workflow and schema database SSOT for the ScriptForge runtime."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import transaction

from apps.common.agent_term import alias_agent_id, normalize_pipeline_runner_path
from apps.workflow.bootstrap.workflow_disk import (
    DISK_ARTIFACT_BY_NODE,
    DISK_EXTRA_ARTIFACTS_BY_NODE,
    DISK_INDEX_BY_NODE,
    DISK_PIPELINE_RESULT_KEY_BY_NODE,
    DISK_RUNNER_PATH_BY_NODE,
    DISK_RUNNER_TYPE_BY_NODE,
    DISK_STATUS_BY_NODE,
)

logger = logging.getLogger(__name__)


class FusionPipelineDbService:
    DEFAULT_MAIN_CHAIN: Tuple[Dict[str, Any], ...] = (
        {
            "fusion_node_id": "node_brief",
            "name": "Brief",
            "description": "Project brief",
            "chain_order": 1,
            "website_index": 1,
            "runner_type": "fusion_node",
            "skill_id": "creation.brief",
            "artifact_key": "project_brief",
            "pipeline_result_key": "project_brief",
            "fusion_status": "draft",
            "coin_cost": 10,
        },
        {
            "fusion_node_id": "node_structure",
            "name": "Structure",
            "description": "Story structure plan",
            "chain_order": 2,
            "website_index": 2,
            "runner_type": "fusion_node",
            "skill_id": "creation.structure",
            "artifact_key": "structure_plan",
            "pipeline_result_key": "structure",
            "fusion_status": "planning",
            "coin_cost": 10,
        },
        {
            "fusion_node_id": "node_character",
            "name": "Character",
            "description": "Character bible",
            "chain_order": 3,
            "website_index": 3,
            "runner_type": "fusion_node",
            "skill_id": "creation.character",
            "artifact_key": "character_bible",
            "pipeline_result_key": "characters",
            "fusion_status": "planning",
            "coin_cost": 10,
        },
        {
            "fusion_node_id": "node_outline",
            "name": "Outline",
            "description": "Episode outline",
            "chain_order": 4,
            "website_index": 4,
            "runner_type": "fusion_node",
            "skill_id": "creation.outline",
            "artifact_key": "series_outline",
            "pipeline_result_key": "outlines",
            "fusion_status": "planning",
            "coin_cost": 20,
        },
        {
            "fusion_node_id": "node_script",
            "name": "Script",
            "description": "Episode scripts",
            "chain_order": 5,
            "website_index": 5,
            "runner_type": "fusion_node",
            "skill_id": "creation.script",
            "artifact_key": "episode_scripts",
            "pipeline_result_key": "scripts",
            "fusion_status": "writing",
            "coin_cost": 30,
        },
    )

    @classmethod
    @lru_cache(maxsize=1)
    def fusion_node_columns(cls) -> frozenset[str]:
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError

        try:
            with connection.cursor() as cursor:
                return frozenset(
                    col.name
                    for col in connection.introspection.get_table_description(
                        cursor, "skill_fusion_pipeline_node"
                    )
                )
        except (ProgrammingError, OperationalError):
            return frozenset()

    @classmethod
    def fusion_node_has_column(cls, column: str) -> bool:
        return column in cls.fusion_node_columns()

    @classmethod
    def db_config_enabled(cls) -> bool:
        return bool(getattr(settings, "FUSION_DB_CONFIG", True))

    @classmethod
    def disk_fallback_enabled(cls) -> bool:
        return False

    @classmethod
    def get_active_pack(cls):
        from django.db.utils import ProgrammingError, OperationalError

        from apps.workflow.models import FusionPipelinePack

        try:
            return FusionPipelinePack.objects.filter(is_active=True).first()
        except (ProgrammingError, OperationalError):
            return None
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == "DatabaseOperationForbidden":
                return None
            raise

    @classmethod
    def has_active_nodes(cls) -> bool:
        pack = cls.get_active_pack()
        if pack is None:
            return False
        try:
            expected = [item["fusion_node_id"] for item in cls.DEFAULT_MAIN_CHAIN]
            actual = list(
                pack.nodes.filter(enabled=True, portal_visible=True)
                .order_by("chain_order")
                .values_list("fusion_node_id", flat=True)
            )
            return actual == expected and list(pack.terminal_node_ids or []) == ["node_script"]
        except Exception:  # noqa: BLE001
            return False

    @classmethod
    def should_use_db(cls) -> bool:
        return cls.db_config_enabled() and cls.has_active_nodes()

    @classmethod
    @transaction.atomic
    def ensure_builtin_default_pack(cls):
        """Create the DB-only 5-step default pack without reading external assets."""
        from apps.workflow.models import FusionPipelineNode, FusionPipelinePack

        pack, _ = FusionPipelinePack.objects.update_or_create(
            slug="short-drama-v1",
            defaults={
                "version": "short-drama-v1.0",
                "display_name": "鐭墽鍒涗綔鏍囧噯娴佺▼ v1",
                "description": "鐭墽鍓ф湰鍒涗綔鏍囧噯宸ヤ綔娴侊細绔嬮」 鈫?缁撴瀯 鈫?瑙掕壊 鈫?澶х翰 鈫?鍓ф湰",
                "is_active": True,
                "is_published_to_portal": True,
                "is_default_for_creation": True,
                "pack_status": "active",
                "gray_weight": 100,
                "terminal_node_ids": ["node_script"],
                "post_script_chain": [],
                "engine_config": {
                    "enabled": True,
                    "max_retries": 3,
                    "timeout_seconds": 1800,
                    "heartbeat_interval_seconds": 60,
                },
            },
        )
        FusionPipelinePack.objects.exclude(pk=pack.pk).filter(is_active=True).update(is_active=False)
        keep_ids = [item["fusion_node_id"] for item in cls.DEFAULT_MAIN_CHAIN]
        FusionPipelineNode.objects.filter(pack=pack).exclude(fusion_node_id__in=keep_ids).delete()
        for item in cls.DEFAULT_MAIN_CHAIN:
            FusionPipelineNode.objects.update_or_create(
                pack=pack,
                fusion_node_id=item["fusion_node_id"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "chain_order": item["chain_order"],
                    "website_index": item["website_index"],
                    "runner_type": item["runner_type"],
                    "runner_path": "",
                    "skill_id": item["skill_id"],
                    "output_key": item["artifact_key"],
                    "artifact_key": item["artifact_key"],
                    "pipeline_result_key": item["pipeline_result_key"],
                    "extra_artifact_keys": [],
                    "is_terminal": item["fusion_node_id"] == "node_script",
                    "fusion_status": item["fusion_status"],
                    "enabled": True,
                    "requires_confirm": True,
                    "portal_visible": True,
                    "coin_cost": item["coin_cost"],
                    "runtime_config": {
                        "timeout_seconds": 600,
                        "retry_policy": {
                            "max_retries": 3,
                            "backoff": "exponential",
                            "base_seconds": 2,
                        },
                        "allow_skip": False,
                        "is_checkpoint": True,
                    },
                },
            )
        cls.clear_caches()
        return pack

    @classmethod
    def config_source(cls) -> str:
        if cls.should_use_db():
            return "db"
        return "none"

    @classmethod
    def clear_caches(cls) -> None:
        cls.fusion_node_columns.cache_clear()
        cls.main_chain_nodes_cached.cache_clear()
        cls._nodes_tuple_for_pack.cache_clear()
        cls.main_chain_artifacts_map_cached.cache_clear()
        cls.get_schema_json_cached.cache_clear()
        try:
            from apps.workflow.fusion.config_loader import get_fusion_config

            get_fusion_config.cache_clear()
        except Exception:  # noqa: BLE001
            pass
        try:
            from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

            get_ssot_catalog.cache_clear()
        except Exception:  # noqa: BLE001
            pass

    @classmethod
    def get_pack_by_id(cls, pack_id):
        from django.db.utils import ProgrammingError, OperationalError

        from apps.workflow.models import FusionPipelinePack

        if not pack_id:
            return None
        try:
            return FusionPipelinePack.objects.filter(pk=pack_id).first()
        except (ProgrammingError, OperationalError):
            return None

    @classmethod
    def resolve_pack_for_creation(cls, pack_id: Optional[str] = None):
        """Resolve the workflow pack for a new creation."""
        from apps.workflow.models import FusionPipelinePack

        if pack_id:
            pack = cls.get_pack_by_id(pack_id)
            if pack and pack.nodes.exists():
                return pack
        default = FusionPipelinePack.objects.filter(is_default_for_creation=True).first()
        if default and default.nodes.exists():
            return default
        published = (
            FusionPipelinePack.objects.filter(is_published_to_portal=True)
            .order_by("-updated_at")
            .first()
        )
        if published and published.nodes.exists():
            return published
        active = cls.get_active_pack()
        if active and active.nodes.exists():
            return active
        return None

    @classmethod
    @lru_cache(maxsize=32)
    def _nodes_tuple_for_pack(cls, pack_id: str) -> Tuple[Dict[str, Any], ...]:
        from django.db.utils import ProgrammingError, OperationalError

        from apps.workflow.models import FusionPipelineNode, FusionPipelinePack

        try:
            pack = FusionPipelinePack.objects.filter(pk=pack_id).first()
        except (ProgrammingError, OperationalError):
            return tuple()
        if pack is None:
            return tuple()
        try:
            fields = [
                "fusion_node_id",
                "website_index",
                "name",
                "description",
                "runner_type",
                "runner_path",
                "output_key",
                "artifact_key",
                "schema__filename",
                "schema__schema_key",
                "is_terminal",
                "fusion_status",
                "chain_order",
            ]
            columns = cls.fusion_node_columns()
            if "runner_type" not in columns:
                fields.remove("runner_type")
            if "runner_path" not in columns:
                fields.remove("runner_path")
            if "extra_artifact_keys" in columns:
                fields.append("extra_artifact_keys")
            if "pipeline_result_key" in columns:
                fields.append("pipeline_result_key")
            for optional in (
                "enabled",
                "requires_confirm",
                "portal_visible",
                "coin_cost",
            ):
                if optional in columns:
                    fields.append(optional)
            if "id" in columns:
                fields.insert(0, "id")
            rows = (
                FusionPipelineNode.objects.filter(pack=pack)
                .order_by("chain_order")
                .values(*fields)
            )
        except (ProgrammingError, OperationalError):
            return tuple()
        out: List[Dict[str, Any]] = []
        for row in rows:
            schema_file = row.get("schema__filename") or ""
            node_index = row.get("website_index")
            agent_id = ""
            if node_index is not None:
                try:
                    from apps.agent.binding import agent_id_for_pipeline_index

                    agent_id = agent_id_for_pipeline_index(int(node_index)) or ""
                except Exception:  # noqa: BLE001
                    agent_id = ""
            out.append(
                alias_agent_id(
                    {
                        "id": str(row.get("id")) if row.get("id") else "",
                        "fusion_node_id": row.get("fusion_node_id") or "",
                        "agent_id": agent_id,
                        "index": node_index,
                        "name": row.get("name") or "",
                        "description": row.get("description") or "",
                        "runner_type": row.get("runner_type") or "",
                        "runner_path": row.get("runner_path") or "",
                        "output_key": row.get("output_key") or "",
                        "artifact_key": row.get("artifact_key") or "",
                        "pipeline_result_key": row.get("pipeline_result_key") or "",
                        "extra_artifact_keys": list(row.get("extra_artifact_keys") or []),
                        "enabled": row.get("enabled", True),
                        "requires_confirm": row.get("requires_confirm", True),
                        "portal_visible": row.get("portal_visible", True),
                        "coin_cost": row.get("coin_cost", 10),
                        "schema_file": schema_file,
                        "schema_key": row.get("schema__schema_key") or "",
                        "is_terminal": row.get("is_terminal"),
                        "fusion_status": row.get("fusion_status") or "",
                        "chain_order": row.get("chain_order"),
                    }
                )
            )
        return tuple(out)

    @classmethod
    @lru_cache(maxsize=1)
    def main_chain_nodes_cached(cls) -> Tuple[Dict[str, Any], ...]:
        pack = cls.get_active_pack()
        if pack is None:
            return tuple()
        return cls._nodes_tuple_for_pack(str(pack.id))

    @classmethod
    def main_chain_nodes(cls, pack_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if pack_id:
            return list(cls._nodes_tuple_for_pack(str(pack_id)))
        if not cls.should_use_db():
            return []
        return list(cls.main_chain_nodes_cached())

    @classmethod
    @lru_cache(maxsize=1)
    def main_chain_artifacts_map_cached(cls) -> Dict[str, Dict[str, Any]]:
        artifacts: Dict[str, Dict[str, Any]] = {}
        for node in cls.main_chain_nodes_cached():
            key = node.get("artifact_key")
            if not key:
                continue
            artifacts[key] = {
                "output_key": node.get("output_key") or "",
                "schema": node.get("schema_file") or "",
                "node_id": node.get("fusion_node_id") or "",
                "pipeline_result_key": node.get("pipeline_result_key") or "",
            }
        return artifacts

    @classmethod
    def main_chain_artifacts_map(cls) -> Dict[str, Dict[str, Any]]:
        if not cls.should_use_db():
            return {}
        return dict(cls.main_chain_artifacts_map_cached())

    @classmethod
    def active_version(cls) -> str:
        pack = cls.get_active_pack()
        if pack:
            return pack.version
        return ""

    @classmethod
    @lru_cache(maxsize=64)
    def get_schema_json_cached(cls, schema_key: str) -> Optional[str]:
        from django.db.utils import ProgrammingError, OperationalError

        from apps.workflow.models import FusionJsonSchema

        try:
            row = FusionJsonSchema.objects.filter(schema_key=schema_key).first()
            if row is None:
                filename = schema_key.replace("schemas/", "")
                row = FusionJsonSchema.objects.filter(filename=filename).first()
        except (ProgrammingError, OperationalError):
            return None
        if row is None:
            return None
        return json.dumps(row.schema_json, ensure_ascii=False)

    @classmethod
    def get_schema_dict(cls, schema_file: str) -> Optional[dict]:
        if not cls.should_use_db():
            return None
        rel = schema_file.replace("schemas/", "")
        key_candidates = [rel, rel.replace(".schema.json", "").replace("-", "_")]
        for key in key_candidates:
            raw = cls.get_schema_json_cached(key)
            if raw:
                return json.loads(raw)
        raw = cls.get_schema_json_cached(rel)
        return json.loads(raw) if raw else None

    @classmethod
    def resolve_schema_file(cls, schema_file: str) -> Optional[str]:
        """Resolve schema filenames through DB only."""
        if not cls.should_use_db():
            return schema_file
        rel = schema_file.replace("schemas/", "")
        if cls.get_schema_dict(rel) is not None:
            return rel
        return schema_file

    @staticmethod
    def _skill_root_display(skill_root: str) -> str:
        if not skill_root:
            return ""
        normalized = skill_root.replace("\\", "/")
        parts = [part for part in normalized.rstrip("/").split("/") if part]
        if len(parts) >= 2:
            return "/".join(parts[-2:])
        return parts[0] if parts else skill_root

    @classmethod
    def meta_payload(cls) -> Dict[str, Any]:
        pack = cls.get_active_pack()
        skill_root = ""
        try:
            from apps.workflow.fusion.config_loader import resolve_skill_root

            skill_root = str(resolve_skill_root())
        except Exception:  # noqa: BLE001
            skill_root = ""

        node_count = pack.nodes.count() if pack else 0
        db_version = pack.version if pack else None
        return {
            "config_source": cls.config_source(),
            "db_version": db_version,
            "skill_version": db_version,
            "pack_id": str(pack.id) if pack else None,
            "node_count": node_count,
            "skill_root": skill_root,
            "skill_root_display": cls._skill_root_display(skill_root),
            "db_config_enabled": cls.db_config_enabled(),
            "disk_fallback_enabled": cls.disk_fallback_enabled(),
        }

    @classmethod
    @transaction.atomic
    def activate_pack(cls, pack_id) -> None:
        from apps.workflow.models import FusionPipelinePack

        FusionPipelinePack.objects.filter(is_active=True).update(is_active=False)
        pack = FusionPipelinePack.objects.get(pk=pack_id)
        pack.is_active = True
        pack.save(update_fields=["is_active", "updated_at"])
        cls.clear_caches()

    @classmethod
    def _load_project_config(cls, root: Optional[str] = None):
        from apps.workflow.fusion.config_loader import FusionSkillConfig, resolve_skill_root

        skill_root = Path(root) if root else resolve_skill_root()
        cfg = FusionSkillConfig(skill_root)
        project = cfg.project_config
        node_flow = project.get("nodeFlow", {})
        main_chain = node_flow.get("mainChain") or cfg.main_chain
        terminal_nodes = node_flow.get("terminalNodes") or cfg.terminal_nodes
        project_meta = project.get("projectMeta") or {}
        return skill_root, cfg, main_chain, terminal_nodes, project_meta

    @classmethod
    def _schema_rows_for_pack(cls, pack, skill_root: Path) -> Dict[str, Any]:
        from apps.workflow.models import FusionJsonSchema

        schema_by_filename: Dict[str, FusionJsonSchema] = {}
        schemas_dir = skill_root / "schemas"
        if schemas_dir.is_dir():
            for path in sorted(schemas_dir.glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                stem = path.stem.replace(".schema", "")
                schema_key = stem.replace("-", "_")
                # schema_key 鍏ㄥ眬鍞竴锛涘 Pack 鍚屾鏃舵寜 key 鍚堝苟锛岄伩鍏嶉噸澶嶆彃鍏?
                row, _ = FusionJsonSchema.objects.update_or_create(
                    schema_key=schema_key,
                    defaults={
                        "pack": pack,
                        "filename": path.name,
                        "schema_json": data,
                    },
                )
                schema_by_filename[path.name] = row
        return schema_by_filename

    @classmethod
    def _apply_disk_tier1_to_agents(cls, node_id: str, tier1_sections: List[str]) -> None:
        if not tier1_sections:
            return
        try:
            from apps.agent.binding import agent_id_for_fusion_node
            from apps.agent.registry import AgentRegistryConfigService

            agent_id = agent_id_for_fusion_node(node_id)
            if not agent_id:
                return
            AgentRegistryConfigService.ensure_defaults()
            AgentRegistryConfigService.patch_agent(
                agent_id,
                {"tier1_sections": list(tier1_sections)},
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("[FusionPipelineDb] tier1鈫抋gent skipped %s: %s", node_id, exc)

    @classmethod
    def _structural_node_fields(
        cls,
        *,
        cfg,
        node_id: str,
        order: int,
        schema_by_filename: Dict[str, Any],
        terminal_nodes: List[str],
    ) -> Dict[str, Any]:
        from apps.workflow.bootstrap.workflow_disk import DEFAULT_STEP_OPS_BY_NODE
        from apps.workflow.tier1_sections import DEFAULT_TIER1_SECTIONS_BY_NODE

        node = cfg.node_by_id(node_id) or {}
        website_index = DISK_INDEX_BY_NODE.get(node_id)
        if website_index is None:
            return {}
        schema_file = (node.get("schemaFile") or "").replace("schemas/", "")
        schema_row = schema_by_filename.get(schema_file) or schema_by_filename.get(Path(schema_file).name)
        ops = DEFAULT_STEP_OPS_BY_NODE.get(node_id, {})
        tier1_sections = list(
            node.get("tier1Sections") or DEFAULT_TIER1_SECTIONS_BY_NODE.get(node_id, [])
        )
        cls._apply_disk_tier1_to_agents(node_id, tier1_sections)
        runner_type = str(node.get("runnerType") or DISK_RUNNER_TYPE_BY_NODE.get(node_id, ""))[:32]
        runner_path = normalize_pipeline_runner_path(
            node.get("runnerPath") or DISK_RUNNER_PATH_BY_NODE.get(node_id, ""),
            runner_type,
        )[:255]
        return {
            "fusion_node_id": node_id,
            "chain_order": order,
            "website_index": website_index,
            "name": str(node.get("name") or node_id)[:128],
            "description": str(node.get("description") or ""),
            "runner_type": runner_type,
            "runner_path": runner_path,
            "output_key": str(node.get("outputKey") or "")[:64],
            "artifact_key": DISK_ARTIFACT_BY_NODE.get(node_id, "")[:64],
            "pipeline_result_key": DISK_PIPELINE_RESULT_KEY_BY_NODE.get(node_id, "")[:64],
            "extra_artifact_keys": list(
                node.get("extraArtifactKeys") or DISK_EXTRA_ARTIFACTS_BY_NODE.get(node_id, [])
            ),
            "schema": schema_row,
            "is_terminal": node_id in terminal_nodes,
            "fusion_status": DISK_STATUS_BY_NODE.get(node_id, "draft"),
            "_ops_defaults": ops,
        }

    @classmethod
    @transaction.atomic
    def removed_disk_sync(cls, *, root: Optional[str] = None) -> None:
        raise RuntimeError("disk sync has been removed; use DB defaults")

    @classmethod
    @transaction.atomic
    def removed_disk_import(cls, *, activate: bool = True, root: Optional[str] = None) -> str:
        raise RuntimeError("disk import has been removed; use DB defaults")

    @classmethod
    def _hydrate_pack_from_registry_meta(cls, pack) -> None:
        """Hydrate optional pack metadata from the DB agent registry."""
        if not pack:
            return
        update_fields: List[str] = []
        try:
            from apps.agent.registry import AgentRegistryConfigService

            reg_payload = AgentRegistryConfigService.admin_payload()
            meta = (reg_payload.get("registry") or {}).get("_meta") or {}
        except Exception:  # noqa: BLE001
            return
        if not pack.flow_graph and isinstance(meta.get("flow_graph"), dict):
            pack.flow_graph = dict(meta.get("flow_graph") or {})
            update_fields.append("flow_graph")
        if pack.post_script_chain:
            pack.post_script_chain = []
            update_fields.append("post_script_chain")
        if not pack.display_name:
            pack.display_name = pack.version
            update_fields.append("display_name")
        if update_fields:
            update_fields.append("updated_at")
            pack.save(update_fields=update_fields)

    @classmethod
    @transaction.atomic
    def duplicate_pack(
        cls,
        source_pack_id,
        *,
        display_name: str,
        slug: str = "",
        activate: bool = False,
    ):
        import uuid as uuid_lib

        from apps.workflow.models import FusionPipelineNode, FusionPipelinePack

        source = FusionPipelinePack.objects.get(pk=source_pack_id)
        suffix = uuid_lib.uuid4().hex[:8]
        new_version = f"{source.version}-copy-{suffix}"
        new_pack = FusionPipelinePack.objects.create(
            version=new_version,
            display_name=(display_name or f"{source.display_name or source.version} 鍓湰").strip()[:128],
            description=source.description or "",
            slug=(slug or "").strip()[:64] or None,
            flow_graph=dict(source.flow_graph or {}),
            post_script_chain=[],
            terminal_node_ids=list(source.terminal_node_ids or []),
            project_meta=dict(source.project_meta or {}),
            imported_from_root=source.imported_from_root or "",
            notes=f"duplicate:{source.id}",
            is_active=False,
            is_published_to_portal=False,
            is_default_for_creation=False,
        )
        for node in source.nodes.select_related("schema").order_by("chain_order"):
            FusionPipelineNode.objects.create(
                pack=new_pack,
                fusion_node_id=node.fusion_node_id,
                chain_order=node.chain_order,
                website_index=node.website_index,
                name=node.name,
                description=node.description,
                runner_type=node.runner_type,
                runner_path=normalize_pipeline_runner_path(node.runner_path, node.runner_type),
                output_key=node.output_key,
                artifact_key=node.artifact_key,
                pipeline_result_key=node.pipeline_result_key,
                extra_artifact_keys=list(node.extra_artifact_keys or []),
                schema=node.schema,
                is_terminal=node.is_terminal,
                fusion_status=node.fusion_status,
                enabled=node.enabled,
                requires_confirm=node.requires_confirm,
                portal_visible=node.portal_visible,
                coin_cost=node.coin_cost,
            )
        if activate:
            cls.activate_pack(new_pack.id)
        cls.clear_caches()
        return new_pack

    @classmethod
    @transaction.atomic
    def update_pack_meta(cls, pack_id, data: Dict[str, Any]):
        from apps.workflow.models import FusionPipelinePack

        pack = FusionPipelinePack.objects.get(pk=pack_id)
        update_fields: List[str] = []
        if "display_name" in data:
            pack.display_name = str(data.get("display_name") or "").strip()[:128]
            update_fields.append("display_name")
        if "description" in data:
            pack.description = str(data.get("description") or "")
            update_fields.append("description")
        if "slug" in data:
            slug = str(data.get("slug") or "").strip()[:64]
            pack.slug = slug or None
            update_fields.append("slug")
        if "flow_graph" in data:
            raw = data.get("flow_graph")
            pack.flow_graph = raw if isinstance(raw, dict) else {}
            update_fields.append("flow_graph")
        if pack.post_script_chain:
            pack.post_script_chain = []
            update_fields.append("post_script_chain")
        if "is_published_to_portal" in data:
            pack.is_published_to_portal = bool(data.get("is_published_to_portal"))
            update_fields.append("is_published_to_portal")
        if update_fields:
            update_fields.append("updated_at")
            pack.save(update_fields=update_fields)
            cls.clear_caches()
        return pack

    @classmethod
    @transaction.atomic
    def set_default_for_creation(cls, pack_id) -> None:
        from apps.workflow.models import FusionPipelinePack

        FusionPipelinePack.objects.filter(is_default_for_creation=True).update(
            is_default_for_creation=False
        )
        pack = FusionPipelinePack.objects.get(pk=pack_id)
        pack.is_default_for_creation = True
        pack.save(update_fields=["is_default_for_creation", "updated_at"])
        cls.clear_caches()

    @classmethod
    def pack_step_preview(cls, pack_id: str, limit: int = 8) -> List[str]:
        names: List[str] = []
        for node in cls.main_chain_nodes(pack_id=pack_id):
            if not node.get("enabled", True) or not node.get("portal_visible", True):
                continue
            label = str(node.get("name") or node.get("fusion_node_id") or "").strip()
            if label:
                names.append(label)
            if len(names) >= limit:
                break
        return names

    @classmethod
    def list_portal_pipelines(cls) -> List[Dict[str, Any]]:
        from apps.workflow.models import FusionPipelinePack

        packs = FusionPipelinePack.objects.filter(is_published_to_portal=True).order_by(
            "-is_default_for_creation", "-updated_at"
        )
        return [cls.serialize_pack_portal(p) for p in packs if p.nodes.exists()]

    @classmethod
    def serialize_pack_portal(cls, pack) -> Dict[str, Any]:
        pack_id = str(pack.id)
        nodes = cls.main_chain_nodes(pack_id=pack_id)
        visible = [
            n for n in nodes if n.get("enabled", True) and n.get("portal_visible", True)
        ]
        return {
            "id": pack_id,
            "displayName": pack.display_name or pack.version,
            "description": pack.description or "",
            "slug": pack.slug or "",
            "isDefault": bool(pack.is_default_for_creation),
            "stepCount": len(visible),
            "stepPreview": cls.pack_step_preview(pack_id),
            "estimatedAutoCost": sum(int(n.get("coin_cost") or 0) for n in visible),
        }

    @classmethod
    def serialize_pack_summary(cls, pack) -> Dict[str, Any]:
        return {
            "id": str(pack.id),
            "version": pack.version,
            "display_name": pack.display_name or "",
            "description": pack.description or "",
            "slug": pack.slug or "",
            "is_active": pack.is_active,
            "is_published_to_portal": pack.is_published_to_portal,
            "is_default_for_creation": pack.is_default_for_creation,
            "node_count": pack.nodes.count(),
            "schema_count": pack.schemas.count(),
            "step_preview": cls.pack_step_preview(str(pack.id)),
            "imported_from_root": pack.imported_from_root,
            "updated_at": pack.updated_at,
        }





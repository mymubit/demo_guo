# -*- coding: utf-8 -*-
"""DB-only workflow config facade."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from django.conf import settings


def resolve_skill_root() -> Path:
    return Path(getattr(settings, "SCRIPT_FORGE_ASSET_ROOT", Path(settings.BASE_DIR) / "apps" / "skill" / "assets"))


class FusionSkillConfig:
    """融合技能配置门面（缓存只读）。"""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or resolve_skill_root()
        self.config_dir = self.root / "config"
        self.runtime_dir = self.root / "runtime-disabled"
        self.schemas_dir = self.root / "schemas"
        self.asset_root = self.root

    @property
    def project_config(self) -> Dict[str, Any]:
        return {"projectMeta": {"version": "db-only"}, "nodeFlow": {"mainChain": [], "terminalNodes": []}}

    @property
    def sub_skills(self) -> Dict[str, Any]:
        return {}

    @property
    def skill_thresholds(self) -> Dict[str, Any]:
        return {}

    @property
    def version(self) -> str:
        return self.project_config.get("projectMeta", {}).get("version", "unknown")

    @property
    def main_chain(self) -> list:
        return self.project_config.get("nodeFlow", {}).get("mainChain", [])

    @property
    def terminal_nodes(self) -> list:
        return self.project_config.get("nodeFlow", {}).get("terminalNodes", [])

    def schema_path(self, schema_file: str) -> Path:
        return self.schemas_dir / schema_file.replace("schemas/", "")

    def node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        nodes = self.project_config.get("nodeFlow", {}).get("nodes", [])
        return next((n for n in nodes if n.get("id") == node_id), None)

    def release_pass_score(self) -> int:
        t = self.skill_thresholds.get("thresholds", {})
        return int(t.get("releasePassScore", 85))

    def health(self) -> Dict[str, Any]:
        return {
            "skill_root": str(self.root),
            "version": self.version,
            "project_config": False,
            "sub_skills": False,
            "external_runtime": False,
            "ok": True,
            "mode": "db-only",
        }


@lru_cache(maxsize=1)
def get_fusion_config() -> FusionSkillConfig:
    return FusionSkillConfig()

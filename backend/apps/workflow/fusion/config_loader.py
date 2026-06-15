# -*- coding: utf-8 -*-
"""从 demo4book/short-drama-script-creator 加载融合配置（只读 SSOT）。"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def resolve_skill_root() -> Path:
    raw = getattr(settings, "FUSION_SKILL_ROOT", "") or ""
    if raw:
        p = Path(raw).expanduser().resolve()
        if p.is_dir():
            return p
        logger.warning("FUSION_SKILL_ROOT 无效：%s", raw)

    # 开发默认：flickplay/demo4book/short-drama-script-creator
    backend_dir = Path(settings.BASE_DIR)
    candidates = [
        backend_dir.parent.parent / "demo4book" / "short-drama-script-creator",
        backend_dir.parent / "demo4book" / "short-drama-script-creator",
    ]
    for c in candidates:
        if (c / "config" / "project-config.json").is_file():
            return c.resolve()

    raise FileNotFoundError(
        "未找到融合技能根目录。请设置环境变量 FUSION_SKILL_ROOT="
        "指向 demo4book/short-drama-script-creator"
    )


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class FusionSkillConfig:
    """融合技能配置门面（缓存只读）。"""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or resolve_skill_root()
        self.config_dir = self.root / "config"
        self.runtime_dir = self.root / "runtime"
        self.schemas_dir = self.root / "schemas"
        self.demo4book_root = self.root.parent if self.root.name == "short-drama-script-creator" else self.root

    @property
    def project_config(self) -> Dict[str, Any]:
        return _read_json(self.config_dir / "project-config.json")

    @property
    def sub_skills(self) -> Dict[str, Any]:
        return _read_json(self.config_dir / "sub-skills.json")

    @property
    def skill_thresholds(self) -> Dict[str, Any]:
        return _read_json(self.config_dir / "skill-thresholds.json")

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
        checks = {
            "skill_root": str(self.root),
            "version": self.version,
            "project_config": (self.config_dir / "project-config.json").is_file(),
            "sub_skills": (self.config_dir / "sub-skills.json").is_file(),
            "runtime_gate": (self.runtime_dir / "sub-gate" / "index.js").is_file(),
            "runtime_score": (self.runtime_dir / "sub-score" / "index.js").is_file(),
        }
        checks["ok"] = all(
            checks[k] for k in ("project_config", "sub_skills", "runtime_gate", "runtime_score")
        )
        return checks


@lru_cache(maxsize=1)
def get_fusion_config() -> FusionSkillConfig:
    return FusionSkillConfig()

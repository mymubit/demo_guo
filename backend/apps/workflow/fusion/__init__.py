"""
融合技能桥接层 — 网站适配 demo4book，技能为 SSOT。

原则：只读 project-config / schemas / sub-skills；通过 subprocess 调用 runtime/sub-* CLI。
禁止在 demo4book 内为网站特例改阈值或裁剪节点。
"""
from .config_loader import FusionSkillConfig, get_fusion_config
from .registry import FusionNodeRegistry
from .cli_runner import FusionCliRunner
from .readiness import evaluate_project_readiness
from .schema_registry import FusionSchemaRegistry
from .artifact_registry import FusionArtifactRegistry, get_artifact_registry

__all__ = [
    "FusionSkillConfig",
    "FusionNodeRegistry",
    "FusionCliRunner",
    "evaluate_project_readiness",
    "FusionSchemaRegistry",
    "FusionArtifactRegistry",
    "get_artifact_registry",
]

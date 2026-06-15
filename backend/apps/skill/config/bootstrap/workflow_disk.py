# -*- coding: utf-8 -*-
"""融合主链磁盘导入 / 无 DB 时的节点字段兜底（与 skill.0017–0022 回填对齐）。"""

DISK_INDEX_BY_NODE = {
    "node-1-input": 1,
    "node-2-structure": 2,
    "node-3-character": 3,
    "node-4-outline": 4,
    "node-5-script": 5,
    "node-6-review": 6,
    "node-8-score": 7,
}

DISK_ARTIFACT_BY_NODE = {
    "node-1-input": "project_brief",
    "node-2-structure": "structure_plan",
    "node-3-character": "character_bible",
    "node-4-outline": "series_outline",
    "node-5-script": "episode_scripts",
    "node-6-review": "quality_report",
    "node-8-score": "script_score_report",
}

DISK_PIPELINE_RESULT_KEY_BY_NODE = {
    "node-1-input": "project_brief",
    "node-2-structure": "structure",
    "node-3-character": "characters",
    "node-4-outline": "outlines",
    "node-5-script": "scripts",
}

DISK_STATUS_BY_NODE = {
    "node-1-input": "draft",
    "node-2-structure": "planning",
    "node-3-character": "planning",
    "node-4-outline": "planning",
    "node-5-script": "writing",
    "node-6-review": "reviewing",
    "node-8-score": "scoring",
}

DISK_EXTRA_ARTIFACTS_BY_NODE = {
    "node-6-review": ["gate_full", "compliance"],
}

DISK_RUNNER_TYPE_BY_NODE = {
    "node-1-input": "fusion_node",
    "node-2-structure": "fusion_node",
    "node-3-character": "fusion_node",
    "node-4-outline": "fusion_node",
    "node-5-script": "fusion_node",
    "node-6-review": "fusion_review",
    "node-8-score": "fusion_score",
}

DISK_RUNNER_PATH_BY_NODE = {
    "node-1-input": "apps.creation.step_mode.run_orchestrator_step",
    "node-2-structure": "apps.creation.step_mode.run_orchestrator_step",
    "node-3-character": "apps.creation.step_mode.run_orchestrator_step",
    "node-4-outline": "apps.creation.step_mode.run_orchestrator_step",
    "node-5-script": "apps.creation.step_mode.run_orchestrator_step",
    "node-6-review": "apps.creation.step_mode.run_fusion_review_step",
    "node-8-score": "apps.creation.step_mode.run_fusion_score_step",
}

# 导入磁盘 pack 时的运营默认值（与 billing 旧 _DEFAULT_NODES 对齐）
DEFAULT_STEP_OPS_BY_NODE = {
    "node-1-input": {"coin_cost": 5, "portal_visible": True},
    "node-2-structure": {"coin_cost": 10, "portal_visible": True},
    "node-3-character": {"coin_cost": 10, "portal_visible": True},
    "node-4-outline": {"coin_cost": 15, "portal_visible": True},
    "node-5-script": {"coin_cost": 30, "portal_visible": True},
    "node-6-review": {"coin_cost": 10, "portal_visible": False},
    "node-8-score": {"coin_cost": 10, "portal_visible": False},
}

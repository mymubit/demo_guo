# -*- coding: utf-8 -*-
"""节点索引与产物 key 映射（独立 Agent 产物预览用）。"""
from __future__ import annotations

from typing import List, Optional

from apps.workflow.fusion import get_artifact_registry

_artifact_reg = get_artifact_registry()


def artifact_key_for_node(node_index: int) -> Optional[str]:
    return _artifact_reg.artifact_key_for_index(node_index)


def artifacts_for_node(node_index: int) -> List[str]:
    return _artifact_reg.artifacts_for_node(node_index)


ARTIFACTS_BY_NODE = {
    i: _artifact_reg.artifacts_for_node(i) for i in range(1, _artifact_reg.max_node_index() + 1)
}
NODE_ARTIFACT_KEYS = {
    i: _artifact_reg.artifact_key_for_index(i)
    for i in range(1, _artifact_reg.max_node_index() + 1)
    if _artifact_reg.artifact_key_for_index(i)
}

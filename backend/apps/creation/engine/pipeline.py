# -*- coding: utf-8 -*-
"""ScriptForge 5-step creation pipeline entrypoint."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .base import Pipeline, PipelineContext
from .node1_input import Node1Input
from .node2_structure import Node2Structure
from .node3_character import Node3Character
from .node4_outline import Node4Outline
from .node5_script import Node5Script

logger = logging.getLogger(__name__)


class ScriptPipeline:
    def __init__(self):
        self.pipeline = Pipeline()
        self._setup_nodes()

    def _setup_nodes(self) -> None:
        self.pipeline.add_node(Node1Input())
        self.pipeline.add_node(Node2Structure())
        self.pipeline.add_node(Node3Character())
        self.pipeline.add_node(Node4Outline())
        self.pipeline.add_node(Node5Script())

    def execute(self, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.now()
        initial_data = {
            "inputs": user_inputs,
            "user_id": user_inputs.get("user_id", "anonymous"),
            "project_id": user_inputs.get("project_id", "unknown"),
            "started_at": start_time.isoformat(),
            "status": "running",
        }
        context = self.pipeline.execute(initial_data)
        total_seconds = (datetime.now() - start_time).total_seconds()
        result = {
            "status": context.data.get("status", "unknown"),
            "project_brief": context.data.get("project_brief"),
            "structure": context.data.get("structure"),
            "characters": context.data.get("characters"),
            "outlines": context.data.get("outlines"),
            "scripts": context.data.get("scripts"),
            "final_result": context.data.get("final_result") or context.data.get("scripts"),
            "errors": context.get_errors(),
            "warnings": context.get_warnings(),
            "total_time_seconds": round(total_seconds, 2),
            "node_count": len(self.pipeline.nodes),
        }
        if result["status"] == "completed":
            result["progress"] = {
                "completed": True,
                "progress_percent": 100,
                "current_node": 5,
                "total_nodes": 5,
            }
        else:
            result["progress"] = self.pipeline.get_progress()
        return result

    def get_node_status(self, node_index: int) -> Optional[Dict[str, Any]]:
        if 0 <= node_index < len(self.pipeline.nodes):
            node = self.pipeline.nodes[node_index]
            return {
                "index": node.index,
                "name": node.name,
                "description": node.description,
                "status": node.get_status(),
                "metadata": node.get_metadata(),
            }
        return None

    def get_progress(self) -> Dict[str, Any]:
        return self.pipeline.get_progress()


class NodeExecutor:
    def __init__(self):
        self.nodes = {
            1: Node1Input(),
            2: Node2Structure(),
            3: Node3Character(),
            4: Node4Outline(),
            5: Node5Script(),
        }

    def execute_node(self, node_index: int, context_data: Dict[str, Any]) -> Dict[str, Any]:
        if node_index not in self.nodes:
            raise ValueError(f"Invalid ScriptForge main-chain node index: {node_index}")
        node = self.nodes[node_index]
        context = PipelineContext(context_data)
        result = node.run(context)
        return {
            "node_index": node_index,
            "node_name": node.name,
            "status": "completed",
            "result": result,
            "errors": context.get_errors(),
            "warnings": context.get_warnings(),
        }

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        node1 = self.nodes[1]
        validation = node1.validate({"inputs": inputs})
        return {
            "valid": validation["valid"],
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", []),
        }


_pipeline_instance: Optional[ScriptPipeline] = None
_executor_instance: Optional[NodeExecutor] = None


def get_pipeline() -> ScriptPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ScriptPipeline()
    return _pipeline_instance


def get_executor() -> NodeExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = NodeExecutor()
    return _executor_instance


def run_full_pipeline(user_inputs: Dict[str, Any]) -> Dict[str, Any]:
    return get_pipeline().execute(user_inputs)


def run_single_node(node_index: int, context_data: Dict[str, Any]) -> Dict[str, Any]:
    return get_executor().execute_node(node_index, context_data)

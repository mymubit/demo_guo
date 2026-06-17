# -*- coding: utf-8 -*-
"""编排画布前后端数据协议 —— Pack ↔ React Flow
========================================================
面向前端可视化编排画布（React Flow 或类似）提供：

  pack_to_canvas(pack)             —— pack 数据 → React Flow nodes+edges
  canvas_to_pack(pack, nodes, edges) —— 画布编辑 → pack 数据回写
  NODE_TEMPLATES                   —— 节点类型清单（前端可用生成节点模板）
  generate_condition_help()        —— 条件表达式帮助文档（前端提示）

React Flow 约定
--------------
{
  "nodes": [
    {"id": "<node_id>", "type": "skill"|"condition"|"parallel"|"end",
     "position": {"x": 100, "y": 200},
     "data": {... node config ...}}
  ],
  "edges": [
    {"id": "e1", "source": "<from_id>", "target": "<to_id>",
     "label": "ctx.score >= 60", "animated": true}
  ]
}

下游：
  - 前端画布：前端渲染 DAG + 配置节点属性
  - api.py：管理端「发布/校验」等调用本协议

使用示例：
    from apps.workflow.canvas_protocol import pack_to_canvas
    json_response = pack_to_canvas(pack_instance)
========================================================
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =========================================================
# 节点类型清单（前端可用生成节点面板）
# =========================================================
NODE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "type": "start",
        "label": "开始节点",
        "description": "工作流入口，只有一个",
        "icon": "▶️",
        "fields": [],
    },
    {
        "type": "skill",
        "label": "技能调用",
        "description": "调用 FusionSkill（LLM/合成/合规/人工）",
        "icon": "🤖",
        "fields": [
            {"key": "skill_id", "label": "技能 ID", "type": "text",
             "required": True, "placeholder": "fusion.skill.<module>.<name>"},
            {"key": "skill_title", "label": "技能标题", "type": "text",
             "required": False},
            {"key": "model_hint", "label": "模型偏好", "type": "text",
             "required": False},
            {"key": "instruction_override", "label": "覆盖指令", "type": "textarea",
             "required": False},
            {"key": "max_retries", "label": "重试次数", "type": "number",
             "required": False, "default": 3, "min": 0, "max": 10},
            {"key": "timeout_sec", "label": "超时(秒)", "type": "number",
             "required": False, "default": 600, "min": 5},
            {"key": "fallback_on_failure", "label": "失败降级",
             "type": "select", "required": False,
             "options": ["continue", "abort", "retry_only"]},
        ],
    },
    {
        "type": "condition",
        "label": "条件分支",
        "description": "按 ctx / prev.output 做多路分支",
        "icon": "🔀",
        "fields": [
            {"key": "condition_expr", "label": "条件表达式",
             "type": "textarea", "required": True,
             "placeholder": "ctx.topic == '爱情'"},
            {"key": "branches", "label": "分支列表",
             "type": "list<object>", "required": True,
             "sub_fields": [
                 {"key": "label", "label": "分支名", "type": "text"},
                 {"key": "expr", "label": "表达式", "type": "textarea"},
                 {"key": "target", "label": "目标节点", "type": "node-picker"},
             ]},
        ],
    },
    {
        "type": "parallel",
        "label": "并行网关",
        "description": "并行跑所有下游，全部完成后再汇聚",
        "icon": "🌿",
        "fields": [],
    },
    {
        "type": "loop",
        "label": "循环节点",
        "description": "按条件重复执行子流程",
        "icon": "🔁",
        "fields": [
            {"key": "max_iterations", "label": "最大循环次数",
             "type": "number", "default": 10, "required": True, "min": 1},
            {"key": "continue_expr", "label": "继续条件", "type": "textarea",
             "required": True, "placeholder": "ctx.quality_score < 80"},
        ],
    },
    {
        "type": "human",
        "label": "人工审核",
        "description": "等待运营侧人工确认",
        "icon": "👤",
        "fields": [
            {"key": "reviewer_role", "label": "审核角色",
             "type": "select", "required": False,
             "options": ["editor", "pm", "compliance"]},
            {"key": "timeout_hours", "label": "超时小时数",
             "type": "number", "default": 48},
        ],
    },
    {
        "type": "end",
        "label": "结束节点",
        "description": "工作流终点",
        "icon": "🏁",
        "fields": [],
    },
]


# =========================================================
# 条件表达式帮助文档（前端编辑器 tooltip）
# =========================================================
def generate_condition_help() -> Dict[str, Any]:
    return {
        "available_variables": [
            {"name": "ctx", "description": "当前工作流的全部上下文字典"},
            {"name": "prev", "description": "上一个节点的输出，含 prev.output / prev.status"},
            {"name": "nodes", "description": "所有已执行节点的输出字典 nodes.<node_id>.output"},
            {"name": "constants", "description": "整数、字符串、布尔、None、list、dict"},
        ],
        "allowed_operators": [
            "and", "or", "not", "==", "!=", ">", ">=", "<", "<=",
            "in", "not in", "+", "-", "*", "/", "%",
        ],
        "examples": [
            "ctx.topic == '爱情'",
            "prev.output.get('score', 0) >= 80",
            "ctx.episodes_created < ctx.episodes_total",
            "'合规通过' in prev.output.get('review', '')",
        ],
        "forbidden": [
            "不允许：__import__、exec、eval、lambda、open、breakpoint、__ 前缀属性",
        ],
    }


# =========================================================
# pack → React Flow
# =========================================================
def pack_to_canvas(pack) -> Dict[str, Any]:
    """把一个 FusionPipelinePack 转换为 React Flow 的 nodes + edges。

    Args:
        pack: FusionPipelinePack 实例（含 nodes 反向访问）。

    Returns:
        {
          "nodes": [...],
          "edges": [...],
          "pack": {
            "id": "...",
            "version": "...",
            "display_name": "...",
            "pack_status": "...",
            "gray_weight": <int>,
            "engine_config": {...},
          }
        }
    """
    nodes_qs = list(pack.nodes.all().order_by("chain_order"))

    # ——— 生成 nodes ———
    nodes: List[Dict[str, Any]] = []
    node_positions: Dict[str, Tuple[float, float]] = {}
    # 简单的自动布局：按 chain_order 一列向下
    for idx, node in enumerate(nodes_qs):
        x = 240
        y = 100 + idx * 220
        node_id = node.fusion_node_id
        node_positions[node_id] = (x, y)
        data = {
            "label": node.display_name,
            "runner_type": node.runner_type,
            "skill_id": node.skill_id,
            "runtime_config": node.runtime_config or {},
            "condition_expr": node.condition_expr,
            "upstream_deps": list(node.upstream_deps or []),
            "downstream_map": node.downstream_map or {},
            "coin_cost": node.coin_cost,
            "is_head": node.is_head,
            "chain_order": node.chain_order,
        }
        nodes.append({
            "id": node_id,
            "type": _map_runner_type(node.runner_type),
            "position": {"x": x, "y": y},
            "data": data,
        })

    # ——— 生成 edges ———
    edges: List[Dict[str, Any]] = []
    for idx, node in enumerate(nodes_qs):
        nid = node.fusion_node_id
        # 优先使用 upstream_deps（显式依赖）
        if node.upstream_deps:
            for dep in node.upstream_deps:
                edges.append({
                    "id": f"e-{dep}-{nid}",
                    "source": dep,
                    "target": nid,
                    "label": node.condition_expr or "",
                    "animated": bool(node.condition_expr),
                })
        # 回退：按 chain_order 线性
        else:
            prev_node = nodes_qs[idx - 1] if idx > 0 else None
            if prev_node:
                edges.append({
                    "id": f"e-linear-{prev_node.fusion_node_id}-{nid}",
                    "source": prev_node.fusion_node_id,
                    "target": nid,
                    "label": node.condition_expr or "",
                    "animated": bool(node.condition_expr),
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "pack": {
            "id": str(pack.id),
            "version": pack.version,
            "display_name": pack.display_name,
            "pack_status": pack.pack_status,
            "gray_weight": pack.gray_weight,
            "engine_config": pack.engine_config or {},
            "is_official": pack.is_official,
            "node_count": len(nodes_qs),
        },
    }


def _map_runner_type(runner_type: Optional[str]) -> str:
    """FusionPipelineNode.runner_type → React Flow 节点 type 映射。"""
    mapping = {
        "skill": "skill",
        "agent": "skill",            # agent 统一走 skill 面板
        "condition": "condition",
        "parallel": "parallel",
        "loop": "loop",
        "human_review": "human",
        "human": "human",
        "start": "start",
        "end": "end",
    }
    return mapping.get(runner_type or "skill", "skill")


# =========================================================
# 画布保存 → pack 数据回写
# =========================================================
def canvas_to_pack_data(
    nodes: Iterable[Dict[str, Any]],
    edges: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """根据 React Flow 的 nodes + edges 生成 FusionPipelineNode 的字段列表。

    说明：该函数仅返回「数据」，不修改数据库。真正写入需要调用 PackPublisher
    或在 DRF 里 save。

    Args:
        nodes: React Flow nodes（含 data.{runtime_config,skill_id,condition_expr,...}）
        edges: React Flow edges

    Returns:
        List[dict] —— 每一项对应一条节点记录，字段与 FusionPipelineNode 兼容。
    """
    node_list: List[Dict[str, Any]] = list(nodes)
    edge_list: List[Dict[str, Any]] = list(edges)

    # 记录 source → target 映射
    out_map: Dict[str, List[str]] = {}
    for e in edge_list:
        out_map.setdefault(e.get("source", ""), []).append(
            {"target": e.get("target", ""), "condition": e.get("label", "")}
        )

    upstream_map: Dict[str, List[str]] = {}
    for e in edge_list:
        upstream_map.setdefault(e.get("target", ""), []).append(e.get("source", ""))

    out_items: List[Dict[str, Any]] = []
    for idx, n in enumerate(node_list):
        nid = n.get("id", f"node-{idx}")
        data = n.get("data", {}) or {}
        position = n.get("position", {"x": 0, "y": 0})

        runtime = data.get("runtime_config", {}) or {}
        downstream_map = {}
        for branch in out_map.get(nid, []):
            downstream_map[branch["target"]] = {
                "condition": branch.get("condition") or None,
            }

        out_items.append({
            "fusion_node_id": nid,
            "display_name": data.get("label", f"节点 {idx + 1}"),
            "runner_type": _unmap_node_type(n.get("type", "skill")),
            "skill_id": data.get("skill_id"),
            "chain_order": idx,
            "condition_expr": data.get("condition_expr"),
            "runtime_config": runtime,
            "upstream_deps": sorted(set(upstream_map.get(nid, []))),
            "downstream_map": downstream_map,
            "coin_cost": int(data.get("coin_cost") or 0),
            "is_head": idx == 0,
            "position": position,  # 仅用于前端回显，数据库保存为 runtime_config["position"]
        })
    return out_items


def _unmap_node_type(node_type: Optional[str]) -> str:
    """React Flow 节点 type → FusionPipelineNode.runner_type 反向映射。"""
    mapping = {
        "start": "start",
        "skill": "skill",
        "condition": "condition",
        "parallel": "parallel",
        "loop": "loop",
        "human": "human_review",
        "end": "end",
    }
    return mapping.get(node_type or "skill", "skill")


# =========================================================
# 给管理端「调试」页的辅助：估算金币/耗时
# =========================================================
def summarize_canvas(nodes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """快速统计画布上节点的摘要（前端可用来展示 cost 预估）。"""
    coin_total = 0
    type_count: Dict[str, int] = {}
    for item in nodes_data:
        coin_total += int(item.get("coin_cost") or 0)
        t = item.get("runner_type", "skill")
        type_count[t] = type_count.get(t, 0) + 1
    return {
        "node_count": len(nodes_data),
        "coin_total": coin_total,
        "type_distribution": type_count,
    }


__all__ = [
    "pack_to_canvas",
    "canvas_to_pack_data",
    "NODE_TEMPLATES",
    "generate_condition_help",
    "summarize_canvas",
]

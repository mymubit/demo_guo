"""流水线元信息 — 优先从 demo4book 融合 project-config 读取（技能 SSOT）。"""

import logging

logger = logging.getLogger(__name__)


def _load_pipeline_nodes():
    from django.conf import settings

    if getattr(settings, "FUSION_SKILL_ENABLED", True):
        try:
            from apps.workflow.services.pipeline_service import WorkflowPipelineService

            nodes = WorkflowPipelineService.pipeline_nodes_for_creation()
            if nodes:
                return nodes
        except Exception as exc:
            logger.warning("流程编排加载失败，回退融合注册表: %s", exc)
        try:
            from apps.workflow.fusion import FusionNodeRegistry

            return FusionNodeRegistry().pipeline_nodes_legacy_shape()
        except Exception as exc:
            logger.warning("融合节点注册表加载失败，回退旧 PIPELINE_NODES: %s", exc)
    return [
        {"index": 1, "name": "需求解析", "description": "解析输入参数，校验并规范化创意描述"},
        {"index": 2, "name": "剧本结构设计", "description": "设计整体故事线、章节节奏与冲突结构"},
        {"index": 3, "name": "人物设定", "description": "构建主要角色档案、人物关系与动机"},
        {"index": 4, "name": "分集大纲", "description": "为每一集生成关键情节与转折点"},
        {"index": 5, "name": "剧本正文", "description": "逐集生成剧本正文（场景/对白/动作）"},
        {"index": 6, "name": "审核与修订", "description": "一致性检查、敏感词过滤与文笔润色"},
        {"index": 7, "name": "剧本评分", "description": "8 维评分与系统放行线（融合 node-8）"},
    ]


PIPELINE_NODES = _load_pipeline_nodes()

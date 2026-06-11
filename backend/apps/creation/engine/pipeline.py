# -*- coding: utf-8 -*-
"""
7节点创作流水线入口
整合所有节点，提供统一的执行接口
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseNode, Pipeline, PipelineContext
from .node1_input import Node1Input
from .node2_structure import Node2Structure
from .node3_character import Node3Character
from .node4_outline import Node4Outline
from .node5_script import Node5Script
from .node6_review import Node6Review
from .node7_export import Node7Export


logger = logging.getLogger(__name__)


class ScriptPipeline:
    """
    短剧剧本创作流水线
    7节点顺序执行：信息收集→结构规划→人设开发→大纲撰写→剧本创作→质量审查→输出交付
    """

    def __init__(self):
        self.pipeline = Pipeline()
        self._setup_nodes()

    def _setup_nodes(self):
        """初始化7个节点"""
        self.pipeline.add_node(Node1Input())
        self.pipeline.add_node(Node2Structure())
        self.pipeline.add_node(Node3Character())
        self.pipeline.add_node(Node4Outline())
        self.pipeline.add_node(Node5Script())
        self.pipeline.add_node(Node6Review())
        self.pipeline.add_node(Node7Export())

    def execute(self, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整创作流水线

        参数:
            user_inputs: 用户提交的创作参数
                - theme: str 题材代码
                - core_idea: str 一句话创意
                - episode_count: int 集数
                - episode_duration: int 单集时长（分钟）
                - format_variant: str 格式变体 A/B/C/D
                - audience: str 目标受众（可选）
                - reference_work: str 参考作品（可选）
                - user_id: str 用户ID
                - project_id: str 项目ID

        返回:
            执行结果字典，包含:
                - status: str 执行状态
                - project_brief: dict 项目简报
                - structure: dict 结构规划
                - characters: dict 角色体系
                - outlines: dict 分集大纲
                - scripts: dict 完整剧本
                - review: dict 质量审查
                - export: dict 导出包
                - errors: list 错误列表
                - warnings: list 警告列表
                - total_time_seconds: float 总耗时
        """
        start_time = datetime.now()

        # 准备初始数据
        initial_data = {
            'inputs': user_inputs,
            'user_id': user_inputs.get('user_id', 'anonymous'),
            'project_id': user_inputs.get('project_id', 'unknown'),
            'started_at': start_time.isoformat(),
            'status': 'running',
        }

        # 执行流水线
        context = self.pipeline.execute(initial_data)

        # 计算耗时
        end_time = datetime.now()
        total_seconds = (end_time - start_time).total_seconds()

        # 构建返回结果
        result = {
            'status': context.data.get('status', 'unknown'),
            'project_brief': context.data.get('project_brief'),
            'structure': context.data.get('structure'),
            'characters': context.data.get('characters'),
            'outlines': context.data.get('outlines'),
            'scripts': context.data.get('scripts'),
            'review': context.data.get('review'),
            'export': context.data.get('export'),
            'final_result': context.data.get('final_result'),
            'errors': context.get_errors(),
            'warnings': context.get_warnings(),
            'total_time_seconds': round(total_seconds, 2),
            'node_count': len(self.pipeline.nodes),
        }

        # 如果成功，添加进度信息
        if result['status'] == 'completed':
            result['progress'] = {
                'completed': True,
                'progress_percent': 100,
                'current_node': 7,
                'total_nodes': 7,
            }
        else:
            result['progress'] = self.pipeline.get_progress()

        return result

    def get_node_status(self, node_index: int) -> Dict[str, Any]:
        """获取指定节点的状态"""
        if 0 <= node_index < len(self.pipeline.nodes):
            node = self.pipeline.nodes[node_index]
            return {
                'index': node.index,
                'name': node.name,
                'description': node.description,
                'status': node.get_status(),
                'metadata': node.get_metadata(),
            }
        return None

    def get_progress(self) -> Dict[str, Any]:
        """获取当前执行进度"""
        return self.pipeline.get_progress()


class NodeExecutor:
    """
    单节点执行器
    支持单独执行某个节点（用于调试或增量生成）
    """

    def __init__(self):
        self.nodes = {
            1: Node1Input(),
            2: Node2Structure(),
            3: Node3Character(),
            4: Node4Outline(),
            5: Node5Script(),
            6: Node6Review(),
            7: Node7Export(),
        }

    def execute_node(
        self,
        node_index: int,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行单个节点

        参数:
            node_index: 节点编号 (1-7)
            context_data: 上下文数据（应包含前置节点的结果）

        返回:
            节点执行结果
        """
        if node_index not in self.nodes:
            raise ValueError(f"Invalid node index: {node_index}")

        node = self.nodes[node_index]
        context = PipelineContext(context_data)

        # 执行节点
        result = node.run(context)

        return {
            'node_index': node_index,
            'node_name': node.name,
            'status': 'completed',
            'result': result,
            'errors': context.get_errors(),
            'warnings': context.get_warnings(),
        }

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证节点1的输入

        参数:
            inputs: 用户输入参数

        返回:
            验证结果
        """
        node1 = self.nodes[1]
        validation = node1.validate({'inputs': inputs})

        return {
            'valid': validation['valid'],
            'errors': validation.get('errors', []),
            'warnings': validation.get('warnings', []),
        }


# 全局单例实例
_pipeline_instance = None
_executor_instance = None


def get_pipeline() -> ScriptPipeline:
    """获取流水线单例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ScriptPipeline()
    return _pipeline_instance


def get_executor() -> NodeExecutor:
    """获取节点执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = NodeExecutor()
    return _executor_instance


def run_full_pipeline(user_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    运行完整创作流水线的便捷函数

    参数:
        user_inputs: 用户输入参数

    返回:
        流水线执行结果
    """
    pipeline = get_pipeline()
    return pipeline.execute(user_inputs)


def run_single_node(node_index: int, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    运行单个节点的便捷函数

    参数:
        node_index: 节点编号
        context_data: 上下文数据

    返回:
        节点执行结果
    """
    executor = get_executor()
    return executor.execute_node(node_index, context_data)

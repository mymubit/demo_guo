# -*- coding: utf-8 -*-
"""
7节点流水线基类
定义所有节点的通用接口和方法
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BaseNode(ABC):
    """创作流水线节点基类"""

    # 节点基本信息
    index: int = 0
    name: str = "BaseNode"
    description: str = ""

    # 节点状态
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点逻辑

        参数:
            context: 上下文数据，包含项目信息和上游节点输出

        返回:
            更新后的 context
        """
        pass

    def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        节点输入验证（可选覆盖）

        返回:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
            }
        """
        return {
            'valid': True,
            'errors': [],
            'warnings': [],
        }

    def get_status(self) -> str:
        """获取节点状态"""
        return self._status if hasattr(self, '_status') else self.STATUS_PENDING

    def set_status(self, status: str) -> None:
        """设置节点状态"""
        self._status = status

    def get_metadata(self) -> Dict[str, Any]:
        """获取节点元信息"""
        return {
            'index': self.index,
            'name': self.name,
            'description': self.description,
            'status': self.get_status(),
            'timestamp': datetime.now().isoformat(),
        }

    def log(self, message: str, level: str = "INFO") -> None:
        """节点日志记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [{self.name}] {message}"
        print(log_entry)
        # 实际项目中应写入日志文件或日志服务

    def _get_timestamp(self) -> str:
        """获取当前时间戳字符串"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _get_iso_timestamp(self) -> str:
        """获取ISO格式时间戳"""
        return datetime.now().isoformat()


class PipelineContext:
    """
    流水线上下文管理器
    封装节点间共享的数据和状态
    """

    def __init__(self, initial_data: Dict[str, Any] = None):
        self.data = initial_data or {}
        self.errors = []
        self.warnings = []
        self.node_results = []
        self.started_at = datetime.now()
        self._status = "initialized"

    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self.data

    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append({
            'error': error,
            'timestamp': datetime.now().isoformat(),
        })

    def add_warning(self, warning: str) -> None:
        """添加警告"""
        self.warnings.append({
            'warning': warning,
            'timestamp': datetime.now().isoformat(),
        })

    def add_node_result(self, node_name: str, result: Any) -> None:
        """记录节点执行结果"""
        self.node_results.append({
            'node': node_name,
            'result': result,
            'timestamp': datetime.now().isoformat(),
        })

    def get_errors(self) -> list:
        """获取所有错误"""
        return self.errors

    def get_warnings(self) -> list:
        """获取所有警告"""
        return self.warnings

    def get_node_results(self) -> list:
        """获取所有节点结果"""
        return self.node_results

    def is_valid(self) -> bool:
        """检查上下文是否有效（无错误）"""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data': self.data,
            'errors': self.errors,
            'warnings': self.warnings,
            'node_results': self.node_results,
            'started_at': self.started_at.isoformat(),
            'status': self._status,
        }


class Pipeline:
    """
    7节点创作流水线
    负责按顺序执行所有节点并管理上下文
    """

    def __init__(self):
        self.nodes = []
        self.context = PipelineContext()
        self._is_running = False
        self._is_completed = False

    def add_node(self, node: BaseNode) -> 'Pipeline':
        """添加节点到流水线"""
        self.nodes.append(node)
        return self

    def execute(self, initial_data: Dict[str, Any] = None) -> PipelineContext:
        """
        执行完整流水线

        参数:
            initial_data: 初始数据（如用户输入）

        返回:
            PipelineContext: 执行完成后的上下文
        """
        if self._is_running:
            raise RuntimeError("Pipeline is already running")

        self._is_running = True
        self.context = PipelineContext(initial_data)

        try:
            for node in self.nodes:
                # 设置节点状态
                node.set_status(BaseNode.STATUS_RUNNING)
                self.context.set('current_node', node.index)

                # 执行节点
                node.log(f"Starting execution")
                result = node.run(self.context)
                self.context.data.update(result)

                # 记录节点结果
                self.context.add_node_result(node.name, result)

                # 设置完成状态
                node.set_status(BaseNode.STATUS_COMPLETED)
                node.log(f"Completed successfully")

            self._is_completed = True
            self.context.data['status'] = 'completed'

        except Exception as e:
            # 处理执行异常
            error_msg = f"Pipeline execution failed at node {self.context.get('current_node', 'unknown')}: {str(e)}"
            self.context.add_error(error_msg)
            self.context.data['status'] = 'failed'
            self.context.data['error'] = str(e)
            print(error_msg)

        finally:
            self._is_running = False
            self.context.data['completed_at'] = datetime.now().isoformat()

        return self.context

    def get_progress(self) -> Dict[str, Any]:
        """获取流水线执行进度"""
        completed = sum(1 for n in self.nodes if n.get_status() == BaseNode.STATUS_COMPLETED)
        total = len(self.nodes)

        return {
            'total_nodes': total,
            'completed_nodes': completed,
            'current_node': self.context.get('current_node', 0),
            'progress_percent': round((completed / total) * 100, 1) if total > 0 else 0,
            'is_running': self._is_running,
            'is_completed': self._is_completed,
            'status': self.context.data.get('status', 'unknown'),
        }

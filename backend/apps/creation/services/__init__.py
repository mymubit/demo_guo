"""
创作模块业务服务层

核心职责：
1. 校验会员身份与创作次数
2. 管理 Project 生命周期
3. 与 dj_queue（Django 6 @task）协作，驱动 7 节点流水线
4. 将原始剧本数据渲染为预渲染 HTML 片段（安全：不暴露原始结构）
5. 生成一次性下载 token 与分享链接
6. 处理二进制文件下载流
"""

from ._pipeline import PIPELINE_NODES
from ._rendering import (
    _render_progress_html,
    _render_result_html,
    refresh_project_progress,
)
from .facade import CreationService

__all__ = [
    "CreationService",
    "PIPELINE_NODES",
    "refresh_project_progress",
    "_render_progress_html",
    "_render_result_html",
]

"""
创作模块业务服务层

核心职责：
1. 校验会员身份与创作次数
2. 管理 Project 生命周期
3. 将原始剧本数据渲染为预渲染 HTML 片段
4. 生成一次性下载 token 与分享链接
"""

from ._rendering import (
    _render_progress_html,
    _render_result_html,
    refresh_project_progress,
)
from .facade import CreationService

__all__ = [
    "CreationService",
    "refresh_project_progress",
    "_render_progress_html",
    "_render_result_html",
]

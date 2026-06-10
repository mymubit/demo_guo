"""
创作模块 - API 层

负责：创作任务提交、进度查询、作品管理、下载与分享
核心安全：绝不暴露原始剧本数据结构，结果以预渲染 HTML 或二进制文件输出
"""

default_app_config = "apps.creation.apps.CreationConfig"

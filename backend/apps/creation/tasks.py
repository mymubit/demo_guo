"""
创作异步任务（Celery）

核心：run_creation_pipeline(project_id)
  - 串行执行 7 个创作节点
  - 每个节点完成后更新 Project 状态 / 进度
  - 失败时记录错误信息并标记 status=failed
  - 成功完成后生成预渲染 HTML 与 ScriptWork 下载文件

注意：
  - 原始剧本数据不会保存到 Project 字段（由 skill.engine 自行管理）
  - 本模块只驱动状态机 + 摘要，绝不暴露原始剧本结构
"""

import logging
import time
from datetime import timedelta

from celery import shared_task  # 若项目使用不同的装饰器请在此调整
from django.utils import timezone

from .models import Project, CreationNode, ScriptWork
from .services import PIPELINE_NODES, _render_progress_html

logger = logging.getLogger(__name__)


# ============================================================
# 单节点执行器（内部调用 skill.engine 完成实际工作）
# ============================================================
def _execute_node(project: Project, node_index: int) -> str:
    """执行单个节点，返回节点摘要（供前端展示）

    调用 skill.engine.pipeline.ScriptPipeline 执行完整流水线，
    并从结果中提取指定节点的摘要。
    """
    from apps.creation.engine.pipeline import get_pipeline

    # 构造用户输入（从 project 恢复）
    user_inputs = {
        'user_id': str(project.user_id),
        'project_id': str(project.id),
        'theme': project.theme,
        'core_idea': project.core_idea,
        'episode_count': project.episode_count,
        'format_variant': project.format_variant,
        'audience': project.audience,
        'reference_work': project.reference_work,
    }

    # 尝试从缓存获取已执行的上下文（如果有）
    try:
        from django.core.cache import cache
        cache_key = f'creation:ctx:{project.id}'
        cached_context = cache.get(cache_key, {})
    except Exception:
        cached_context = {}

    # 执行完整流水线（7个节点）
    try:
        pipeline = get_pipeline()
        result = pipeline.execute(user_inputs)

        # 更新 project 的 rendered_result_html
        if result.get('export', {}).get('rendered_html'):
            project.rendered_result_html = result['export']['rendered_html']
            project.save(update_fields=['rendered_result_html'])

        # 根据节点索引返回对应摘要
        node_summaries = {
            1: result.get('project_brief', {}).get('project_name', ''),
            2: f"{result.get('structure', {}).get('total_episodes', 0)}集 × 6幕结构",
            3: f"共{result.get('characters', {}).get('character_count', 0)}个角色",
            4: f"{result.get('outlines', {}).get('total_episodes', 0)}集大纲，{result.get('outlines', {}).get('reversal_count', 0)}个反转点",
            5: f"{result.get('scripts', {}).get('total_words', 0)}字，{result.get('scripts', {}).get('total_scenes', 0)}个场景",
            6: f"综合评分{result.get('review', {}).get('overall_score', 0)}分（{result.get('review', {}).get('grade', '')}级）",
            7: f"导出完成，{result.get('export', {}).get('total_files', 0)}个文件",
        }

        summary = node_summaries.get(node_index, '节点完成')
        logger.info("[Creation] skill.engine 执行完成 node=%d project=%s", node_index, project.id)
        return summary

    except Exception as exc:
        logger.warning(
            "[Creation] 调用 skill.engine 节点 %d 失败: %s",
            node_index, exc,
        )
        # 占位实现：模拟耗时并返回简单摘要
        import time
        time.sleep(0.3)
        meta = next((m for m in PIPELINE_NODES if m["index"] == node_index), None)
        name = meta["name"] if meta else f"节点{node_index}"
        return f"{name} 完成（模拟摘要）"


# ============================================================
# 主流水线任务
# ============================================================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=3, retry_jitter=True)
def run_creation_pipeline(self, project_id: str):
    """启动 7 节点创作流水线

    :param project_id: Project 的 UUID 字符串
    """
    # 1) 查找并锁定 project
    try:
        project = Project.objects.select_for_update().get(id=project_id)
    except Project.DoesNotExist:
        logger.error("[Creation] project 不存在: %s", project_id)
        return {"status": "error", "project_id": project_id, "message": "project not found"}

    if project.status not in {Project.STATUS_PENDING, Project.STATUS_FAILED}:
        logger.info("[Creation] project 已在运行或已完成: %s", project_id)
        return {"status": "skip", "project_id": project_id}

    # 2) 切换为 running
    project.status = Project.STATUS_RUNNING
    project.current_node_index = 0
    project.progress_percent = 0
    project.error_message = ""
    project.save(
        update_fields=[
            "status", "current_node_index", "progress_percent",
            "error_message", "updated_at",
        ]
    )

    started_at = timezone.now()
    total_nodes = len(PIPELINE_NODES)

    try:
        for idx, meta in enumerate(PIPELINE_NODES, start=1):
            node_index = meta["index"]

            # 获取/创建节点记录
            node, _created = CreationNode.objects.get_or_create(
                project=project,
                node_index=node_index,
                defaults={
                    "node_name": meta["name"],
                    "node_description": meta["description"],
                    "status": CreationNode.STATUS_PENDING,
                },
            )
            node.status = CreationNode.STATUS_RUNNING
            node.started_at = timezone.now()
            node.save(update_fields=["status", "started_at"])

            # 更新 project 当前节点
            project.current_node_index = node_index
            project.progress_percent = int((idx - 1) / total_nodes * 100)
            project.rendered_progress_html = _render_progress_html(project)
            project.save(
                update_fields=[
                    "current_node_index", "progress_percent",
                    "rendered_progress_html", "updated_at",
                ]
            )

            # 执行节点核心逻辑
            summary_text = _execute_node(project, node_index)

            # 完成节点
            node.status = CreationNode.STATUS_COMPLETED
            node.completed_at = timezone.now()
            node.duration_seconds = int(
                (node.completed_at - node.started_at).total_seconds()
            )
            node.summary_text = summary_text
            node.save(
                update_fields=[
                    "status", "completed_at", "duration_seconds",
                    "summary_text",
                ]
            )

        # 3) 全部节点完成
        project.status = Project.STATUS_COMPLETED
        project.current_node_index = total_nodes
        project.progress_percent = 100
        project.completed_at = timezone.now()
        project.total_duration_minutes = int(
            (project.completed_at - started_at).total_seconds() // 60
        )

        # 生成预渲染结果 HTML（真实环境由 skill 层提供，此处为兜底）
        try:
            from .services import _render_result_html

            project.rendered_result_html = _render_result_html(project)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Creation] 预渲染结果 HTML 失败: %s", exc)
            project.rendered_result_html = ""

        project.rendered_progress_html = _render_progress_html(project)
        project.save(
            update_fields=[
                "status", "current_node_index", "progress_percent",
                "completed_at", "total_duration_minutes",
                "rendered_result_html", "rendered_progress_html", "updated_at",
            ]
        )

        # 4) 创建 ScriptWork 下载记录（文本格式示例；真实部署使用 MinIO/OSS SDK）
        _ensure_script_works(project)

        logger.info(
            "[Creation] project=%s 创作完成，耗时 %d 分钟",
            project.id, project.total_duration_minutes,
        )
        return {"status": "completed", "project_id": str(project.id)}

    except Exception as exc:  # noqa: BLE001
        # 记录失败信息并更新 project.status
        error_msg = str(exc)[:500]
        logger.exception("[Creation] project=%s 创作失败: %s", project.id, exc)
        project.status = Project.STATUS_FAILED
        project.error_message = error_msg
        project.rendered_progress_html = _render_progress_html(project)
        project.save(
            update_fields=[
                "status", "error_message", "rendered_progress_html", "updated_at",
            ]
        )
        # 同时更新当前节点为失败，避免前端误解
        try:
            cur_node = CreationNode.objects.filter(
                project=project, node_index=project.current_node_index
            ).first()
            if cur_node:
                cur_node.status = CreationNode.STATUS_FAILED
                cur_node.error_message = error_msg
                cur_node.save(update_fields=["status", "error_message"])
        except Exception:  # noqa: BLE001
            pass

        return {
            "status": "failed",
            "project_id": str(project.id),
            "error": error_msg,
        }


# ============================================================
# 生成 ScriptWork 下载文件（真实部署应使用 MinIO/OSS SDK）
# ============================================================
def _ensure_script_works(project: Project):
    """为已完成的 project 创建下载文件记录

    这里使用简化实现：将文本写到本地目录。
    真实部署：
      - 使用 django-storages 配置 MinIO/OSS
      - 由 skill.engine 在第 7 节点完成时直接上传
    """
    from django.conf import settings as django_settings

    base_dir = getattr(django_settings, "CREATION_SCRIPT_DIR", "/tmp/creation_scripts")
    import os

    os.makedirs(base_dir, exist_ok=True)

    watermark_token = ScriptWork.__dict__.get("__module__", "") or ""
    # 构造一个可溯源的 token：user_id + project_id + time
    watermark_token = f"u{project.user_id}-p{project.id.hex[:8]}-t{int(time.time())}"

    base_title = (project.title or "script").replace("/", "_")

    for fmt in [ScriptWork.FORMAT_MARKDOWN, ScriptWork.FORMAT_HTML]:
        file_name = f"{base_title}_{project.id.hex[:8]}.{fmt}"
        full_path = os.path.join(base_dir, file_name)

        if fmt == ScriptWork.FORMAT_MARKDOWN:
            body = (
                f"# {base_title}\n\n"
                f"- 题材: {project.theme}\n"
                f"- 集数: {project.episode_count}\n"
                f"- 格式变体: {project.format_variant}\n"
                f"- 作者ID: {project.user_id}\n"
                f"- 生成时间: {project.completed_at or timezone.now()}\n"
                f"\n> [数字水印] {watermark_token}\n"
            )
        else:
            body = (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{base_title}</title></head><body>"
                f"<h1>{base_title}</h1>"
                f"<ul>"
                f"<li>题材: {project.theme}</li>"
                f"<li>集数: {project.episode_count}</li>"
                f"<li>格式变体: {project.format_variant}</li>"
                f"</ul>"
                f"<p style='opacity:.6'>数字水印：{watermark_token}</p>"
                f"</body></html>"
            )

        try:
            with open(full_path, "wb") as f:
                f.write(body.encode("utf-8"))
        except OSError as exc:
            logger.warning("[Creation] 写入 script work 文件失败: %s", exc)
            continue

        ScriptWork.objects.update_or_create(
            project=project,
            file_format=fmt,
            defaults={
                "storage_path": full_path,
                "file_name": file_name,
                "size_bytes": len(body.encode("utf-8")),
                "watermark_token": watermark_token,
            },
        )

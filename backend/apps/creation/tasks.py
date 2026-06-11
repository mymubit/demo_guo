"""
创作异步任务（Celery）

核心：run_creation_pipeline(project_id)
  - 串行执行 run_full_pipeline 完成创作
  - 根据 pipeline 返回结果更新每个节点状态与摘要
  - 失败时记录错误信息并标记 status=failed
  - 成功完成后生成预渲染 HTML 与 ScriptWork 下载文件

同步 fallback：
  - 当 Celery 不可用时（如本地开发），可直接调用 run_creation_pipeline_sync()
    在当前进程内同步执行，不依赖消息队列。
"""

import logging
import time
from datetime import timedelta

from celery import shared_task  # 若项目使用不同的装饰器请在此调整
from django.utils import timezone

from .models import Project, CreationNode, ScriptWork
from .services import PIPELINE_NODES, _render_progress_html, _render_result_html

logger = logging.getLogger(__name__)


# ============================================================
# 主流水线任务（异步 / 同步通用执行体）
# ============================================================
def _execute_pipeline_for_project(project: Project) -> dict:
    """调用 skill.engine.run_full_pipeline 完成创作并返回结果

    :return: pipeline 返回的 result dict（含 status / project_brief /
             structure / characters / outlines / scripts / review / export 等）
    """
    from apps.creation.engine.pipeline import run_full_pipeline

    user_inputs = {
        "user_id": str(project.user_id),
        "project_id": str(project.id),
        "theme": project.theme,
        "core_idea": project.core_idea,
        "episode_count": project.episode_count,
        "format_variant": project.format_variant,
        "audience": project.audience,
        "reference_work": project.reference_work,
    }

    logger.info("[Creation] 开始执行 pipeline project=%s user=%s", project.id, project.user_id)
    result = run_full_pipeline(user_inputs)
    logger.info(
        "[Creation] pipeline 执行完成 project=%s status=%s total_time=%ss",
        project.id,
        result.get("status"),
        result.get("total_time_seconds", 0),
    )
    return result


def _update_nodes_from_result(project: Project, result: dict) -> None:
    """根据 pipeline 返回的 result 更新 7 个 CreationNode 的摘要与状态

    result 结构：
      - project_brief: { project_name, theme, episode_count, ... }
      - structure:     { acts, reversal_points, theme_code, ... }
      - characters:    { protagonist, antagonist, character_count, ... }
      - outlines:      { total_episodes, reversal_count, ... }
      - scripts:       { total_episodes, total_words, total_scenes, format_variant, ... }
      - review:        { overall_score, grade, ... }
      - export:        { total_files, rendered_html, rendered_progress_html, preview_html, ... }
    """
    brief = result.get("project_brief") or {}
    structure = result.get("structure") or {}
    characters = result.get("characters") or {}
    outlines = result.get("outlines") or {}
    scripts = result.get("scripts") or {}
    review = result.get("review") or {}
    export = result.get("export") or {}

    # 每个节点对应的摘要生成函数
    node_summaries = {
        1: (
            brief.get("project_name")
            or f"{brief.get('theme', project.theme)} · {project.episode_count}集"
        ),
        2: (
            f"{structure.get('total_episodes', project.episode_count)}集 × "
            f"{structure.get('acts', 6)}幕结构, "
            f"{structure.get('reversal_count', 0)}个反转点"
        ),
        3: (
            f"共{characters.get('character_count', 0)}个角色, "
            f"主角「{characters.get('protagonist', '')[:16]}」"
        ),
        4: (
            f"{outlines.get('total_episodes', project.episode_count)}集大纲, "
            f"{outlines.get('reversal_count', 0)}个反转点"
        ),
        5: (
            f"{scripts.get('total_words', 0)}字, "
            f"{scripts.get('total_scenes', 0)}个场景, "
            f"格式变体 {scripts.get('format_variant', project.format_variant)}"
        ),
        6: (
            f"综合评分 {review.get('overall_score', 0)}分 "
            f"({review.get('grade', '')}级)"
        ),
        7: (
            f"导出完成, {export.get('total_files', 0)}个文件, "
            f"含数字水印"
        ),
    }

    now = timezone.now()
    for node_index in range(1, len(PIPELINE_NODES) + 1):
        try:
            node = CreationNode.objects.get(project=project, node_index=node_index)
        except CreationNode.DoesNotExist:
            continue
        node.status = CreationNode.STATUS_COMPLETED
        node.completed_at = now
        node.summary_text = node_summaries.get(node_index, "节点完成")
        node.save(update_fields=["status", "completed_at", "summary_text"])


def _update_project_after_pipeline(project: Project, result: dict, started_at) -> None:
    """根据 pipeline result 更新 Project 状态、进度、预渲染 HTML"""
    export = result.get("export") or {}

    project.status = Project.STATUS_COMPLETED
    project.current_node_index = len(PIPELINE_NODES)
    project.progress_percent = 100
    project.completed_at = timezone.now()
    project.total_duration_minutes = int(
        (project.completed_at - started_at).total_seconds() // 60
    )

    # 优先使用 skill 层生成的 rendered_html
    project.rendered_result_html = (
        export.get("rendered_html")
        or export.get("rendered_progress_html")
        or _render_result_html(project)
    )
    project.rendered_progress_html = (
        export.get("rendered_progress_html") or _render_progress_html(project)
    )

    project.save(
        update_fields=[
            "status",
            "current_node_index",
            "progress_percent",
            "completed_at",
            "total_duration_minutes",
            "rendered_result_html",
            "rendered_progress_html",
            "updated_at",
        ]
    )


def _run_creation_pipeline_core(project_id: str) -> dict:
    """pipeline 实际执行体（可被异步任务或同步函数调用）

    :return: { "status": ..., "project_id": ..., ... }
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
            "status",
            "current_node_index",
            "progress_percent",
            "error_message",
            "updated_at",
        ]
    )

    started_at = timezone.now()

    try:
        # 3) 执行完整 pipeline 并更新所有节点
        result = _execute_pipeline_for_project(project)

        if result.get("status") == "error":
            # pipeline 明确返回错误
            error_msg = "; ".join(result.get("errors") or ["pipeline error"])
            logger.error("[Creation] pipeline 返回错误 project=%s: %s", project.id, error_msg)
            project.status = Project.STATUS_FAILED
            project.error_message = error_msg[:500]
            project.rendered_progress_html = _render_progress_html(project)
            project.save(
                update_fields=[
                    "status",
                    "error_message",
                    "rendered_progress_html",
                    "updated_at",
                ]
            )
            return {"status": "failed", "project_id": str(project.id), "error": error_msg}

        # 4) 更新节点摘要 + 项目状态 + 预渲染 HTML
        _update_nodes_from_result(project, result)
        _update_project_after_pipeline(project, result, started_at)

        # 5) 创建 ScriptWork 下载文件
        _ensure_script_works(project)

        logger.info(
            "[Creation] project=%s 创作完成, 耗时 %d 分钟",
            project.id,
            project.total_duration_minutes,
        )
        return {"status": "completed", "project_id": str(project.id)}

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)[:500]
        logger.exception("[Creation] project=%s 创作失败: %s", project.id, exc)
        project.status = Project.STATUS_FAILED
        project.error_message = error_msg
        project.rendered_progress_html = _render_progress_html(project)
        project.save(
            update_fields=[
                "status",
                "error_message",
                "rendered_progress_html",
                "updated_at",
            ]
        )
        # 同时标记当前节点为失败
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

        return {"status": "failed", "project_id": str(project.id), "error": error_msg}


# ============================================================
# Celery 异步任务入口
# ============================================================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=3, retry_jitter=True)
def run_creation_pipeline(self, project_id: str):
    """启动 7 节点创作流水线（异步）

    :param project_id: Project 的 UUID 字符串
    """
    return _run_creation_pipeline_core(project_id)


# ============================================================
# 同步 fallback（Celery 不可用时直接调用）
# ============================================================
def run_creation_pipeline_sync(project_id: str) -> dict:
    """同步执行创作流水线（不依赖 Celery / 消息队列）

    典型场景：
      - 本地开发环境，Celery broker 未配置
      - 小体量部署，无需异步队列
      - views.py 中检测到 Celery 不可用时的 fallback 路径

    :return: 与 run_creation_pipeline 相同的 dict 结构
    """
    logger.info("[Creation] 同步执行 pipeline project=%s", project_id)
    return _run_creation_pipeline_core(project_id)


# ============================================================
# 生成 ScriptWork 下载文件（真实部署应使用 MinIO/OSS SDK）
# ============================================================
def _ensure_script_works(project: Project):
    """为已完成的 project 创建下载文件记录

    简化实现：将文本写到本地目录。
    真实部署：
      - 使用 django-storages 配置 MinIO/OSS
      - 由 skill.engine 在第 7 节点完成时直接上传
    """
    from django.conf import settings as django_settings

    base_dir = getattr(django_settings, "CREATION_SCRIPT_DIR", "/tmp/creation_scripts")
    import os

    os.makedirs(base_dir, exist_ok=True)

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
                f"<p style='opacity:.6'>数字水印: {watermark_token}</p>"
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

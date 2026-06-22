"""分享链接与剧本下载。"""

import logging
import os
from datetime import timedelta
from html import escape
from typing import Optional, Tuple

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from ..models import DownloadToken, Project, ScriptWork, ShareLink
from ._helpers import _get_user_project
from ._rendering import _render_share_html
from .content_quality import record_final_export

logger = logging.getLogger(__name__)


def _require_deliverable(project: Project) -> None:
    from apps.drama.progress_service import DramaProjectProgressService

    if not DramaProjectProgressService.is_deliverable(project):
        raise PermissionDenied("仅已完成的作品可分享或下载")


@transaction.atomic
def generate_share_link(
    project_id: str,
    user,
    view_limit: int = 100,
    valid_days: int = 7,
    allow_download: bool = False,
    custom_title: str = "",
) -> dict:
    """为作品生成分享链接。"""
    project = _get_user_project(project_id, user)
    _require_deliverable(project)

    token = ShareLink.generate_token()
    expires_at = timezone.now() + timedelta(days=max(1, min(30, valid_days)))

    share = ShareLink.objects.create(
        project=project,
        user=user,
        token=token,
        view_limit=max(1, min(1000, view_limit)),
        expires_at=expires_at,
        allow_download=bool(allow_download),
        custom_title=custom_title or "",
    )

    # 【运营 M6】埋点：生成分享链接
    try:
        from apps.operations.services import track_event
        track_event(
            event_name="share_link_generated",
            user=user,
            project_id=str(project.id),
            page=f"/api/creation/{project.id}/share",
            payload={
                "valid_days": valid_days,
                "view_limit": share.view_limit,
                "allow_download": share.allow_download,
            },
            source="backend",
        )
    except Exception:  # noqa: BLE001
        pass

    frontend_host = getattr(settings, "FRONTEND_HOST", "https://example.com")
    share_url = f"{frontend_host.rstrip('/')}/share/{share.token}"

    return {
        "share_id": str(share.id),
        "share_token": share.token,
        "share_url": share_url,
        "expires_at": share.expires_at,
        "view_limit": share.view_limit,
        "allow_download": share.allow_download,
        "custom_title": share.custom_title,
    }


def get_share_view(share_token: str) -> dict:
    """匿名访问分享页。"""
    with transaction.atomic():
        try:
            share = (
                ShareLink.objects.select_for_update()
                .select_related("project", "user")
                .get(token=share_token)
            )
        except ObjectDoesNotExist:
            raise PermissionDenied("分享链接无效或已过期")

        if not share.is_available:
            raise PermissionDenied("分享链接已失效或查看次数已用完")

        next_count = share.view_count + 1
        should_deactivate = share.view_limit > 0 and next_count >= share.view_limit
        ShareLink.objects.filter(pk=share.pk).update(
            view_count=F("view_count") + 1,
            last_viewed_at=timezone.now(),
            is_active=not should_deactivate,
        )
        share.refresh_from_db()

    project = share.project
    _require_deliverable(project)

    user = share.user
    author_nickname = (
        getattr(user, "nickname", None)
        or getattr(user, "username", None)
        or "匿名用户"
    )

    remain = max(0, share.view_limit - share.view_count)

    return {
        "title": share.custom_title or project.title or "未命名剧本",
        "author_nickname": author_nickname,
        "created_at": share.created_at,
        "expires_at": share.expires_at,
        "remain_views": remain,
        "allow_download": share.allow_download,
        "rendered_share_html": _render_share_html(share),
    }


def download_script(
    project_id: str,
    user,
    file_format: str = "md",
) -> Tuple[bytes, str, str]:
    """下载剧本（返回二进制内容）。"""
    from ..script_export import export_work, project_has_exportable_content

    project = _get_user_project(project_id, user)
    file_format = (file_format or "md").lower()
    workspace_export = (
        project.pipeline_mode == Project.MODE_WORKSPACE
        and project_has_exportable_content(project)
    )
    if file_format in {"md", "zip", "html"} and workspace_export:
        pass
    else:
        _require_deliverable(project)

    try:
        work = ScriptWork.objects.filter(
            project=project, file_format=file_format
        ).first()
    except Exception:
        work = None

    content_type_map = {
        "md": "text/markdown; charset=utf-8",
        "html": "text/html; charset=utf-8",
        "zip": "application/zip",
        "pdf": "application/pdf",
    }
    content_type = content_type_map.get(file_format, "application/octet-stream")

    base_title = (project.title or "script").replace("/", "_")
    file_name = f"{base_title}_{str(project.id)[:8]}.{file_format}"

    if work and work.storage_path:
        file_bytes = _read_storage_bytes(work.storage_path)
        if file_bytes:
            return file_bytes, file_name, content_type

    if file_format in {"md", "zip", "html"}:
        try:
            pkg = export_work(project, file_format)
        except ValueError as exc:
            raise PermissionDenied(str(exc)) from exc
        raw = pkg["content"]
        file_bytes = raw if isinstance(raw, (bytes, bytearray)) else str(raw).encode("utf-8")
        # 【运营 M2】记录最终导出
        try:
            record_final_export(project)
        except Exception:  # noqa: BLE001
            pass
        # 【运营 M6】埋点：剧本导出
        try:
            from apps.operations.services import track_event
            track_event(
                event_name="script_exported",
                user=user,
                project_id=str(project.id),
                page=f"/api/creation/{project.id}/download",
                payload={
                    "file_format": file_format,
                    "exported_via": "authenticated",
                },
                source="backend",
            )
        except Exception:  # noqa: BLE001
            pass
        return file_bytes, pkg.get("filename") or file_name, pkg.get("content_type") or content_type

    watermark = (
        f"[WATERMARK] user={user.id} project={project.id} "
        f"time={timezone.now().isoformat()}[/WATERMARK]"
    )
    if file_format == "html":
        content = (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{escape(base_title)}</title></head>"
            f"<body><h1>{escape(base_title)}</h1>"
            f"<p>{escape(watermark)}</p></body></html>"
        ).encode("utf-8")
    else:
        content = (f"# {base_title}\n\n{watermark}\n").encode("utf-8")

    # 【运营 M2】记录最终导出
    try:
        record_final_export(project)
    except Exception:  # noqa: BLE001
        pass
    # 【运营 M6】埋点：剧本导出
    try:
        from apps.operations.services import track_event
        track_event(
            event_name="script_exported",
            user=user,
            project_id=str(project.id),
            page=f"/api/creation/{project.id}/download",
            payload={
                "file_format": file_format,
                "exported_via": "authenticated",
            },
            source="backend",
        )
    except Exception:  # noqa: BLE001
        pass
    return content, file_name, content_type


def download_by_token(
    token: str,
    file_format: str = "md",
) -> Tuple[bytes, str, str]:
    """使用一次性下载 token 下载剧本。"""
    with transaction.atomic():
        try:
            dl = (
                DownloadToken.objects.select_for_update()
                .select_related("project", "user")
                .get(token=token)
            )
        except ObjectDoesNotExist:
            raise PermissionDenied("下载链接无效或已过期")

        if not dl.is_valid:
            raise PermissionDenied("下载链接已使用或已过期")

        updated = DownloadToken.objects.filter(
            pk=dl.pk,
            is_used=False,
        ).update(is_used=True, used_at=timezone.now())
        if not updated:
            raise PermissionDenied("下载链接已使用或已过期")

    return download_script(
        str(dl.project.id), dl.user, file_format or dl.file_format
    )


def _read_storage_bytes(storage_path: str) -> Optional[bytes]:
    """读取存储路径的字节内容。"""
    if not storage_path:
        return None
    try:
        if os.path.isabs(storage_path) and os.path.isfile(storage_path):
            with open(storage_path, "rb") as f:
                return f.read()
    except OSError as exc:
        logger.warning("[Creation] 读取存储文件失败: %s", exc)
    return None

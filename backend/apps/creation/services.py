"""
创作模块业务服务层

核心职责：
1. 校验会员身份与创作次数
2. 管理 Project 生命周期
3. 与异步任务（Celery）协作，驱动 7 节点流水线
4. 将原始剧本数据渲染为预渲染 HTML 片段（安全：不暴露原始结构）
5. 生成一次性下载 token 与分享链接
6. 处理二进制文件下载流

安全设计：
- 所有对外返回的「剧本内容」只以预渲染 HTML 形式出现
- 下载文件均含数字水印 token（可溯源）
- 下载 token 仅 15 分钟有效，使用一次即失效
"""

import io
import logging
import os
import secrets
from datetime import timedelta
from html import escape
from typing import Optional, Tuple

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.membership.models import UserMembership
from apps.membership.services import MembershipService

from .models import (
    Project,
    CreationNode,
    ScriptWork,
    ShareLink,
    DownloadToken,
)

logger = logging.getLogger(__name__)


# ============================================================
# 7 节点流水线元信息（与 skill.engine 保持一致）
# ============================================================
PIPELINE_NODES = [
    {"index": 1, "name": "需求解析", "description": "解析输入参数，校验并规范化创意描述"},
    {"index": 2, "name": "剧本结构设计", "description": "设计整体故事线、章节节奏与冲突结构"},
    {"index": 3, "name": "人物设定", "description": "构建主要角色档案、人物关系与动机"},
    {"index": 4, "name": "分集大纲", "description": "为每一集生成关键情节与转折点"},
    {"index": 5, "name": "剧本正文", "description": "逐集生成剧本正文（场景/对白/动作）"},
    {"index": 6, "name": "审核与修订", "description": "一致性检查、敏感词过滤与文笔润色"},
    {"index": 7, "name": "导出成品", "description": "按所选格式导出，嵌入数字水印"},
]


# ============================================================
# HTML 渲染工具（预渲染，前端直接插入 DOM）
# ============================================================
def _render_progress_html(project: Project) -> str:
    """渲染项目进度卡片 HTML 片段

    安全：只使用 Project 模型自身的元信息 + 节点摘要，
    绝不暴露原始剧本数据结构。
    """
    nodes_html_parts = []
    nodes = list(project.nodes.all().order_by("node_index"))

    # 如果节点还未初始化（罕见情况），使用默认占位
    if not nodes:
        for meta in PIPELINE_NODES:
            nodes_html_parts.append(
                f'<div class="creation-node pending">'
                f'<span class="node-index">{meta["index"]}</span>'
                f'<span class="node-name">{escape(meta["name"])}</span>'
                f'<span class="node-status">待处理</span>'
                f"</div>"
            )
    else:
        for node in nodes:
            status_class = {
                CreationNode.STATUS_PENDING: "pending",
                CreationNode.STATUS_RUNNING: "running",
                CreationNode.STATUS_COMPLETED: "completed",
                CreationNode.STATUS_FAILED: "failed",
            }.get(node.status, "pending")
            status_text = node.get_status_display()
            summary = escape(node.summary_text or "")
            nodes_html_parts.append(
                f'<div class="creation-node {status_class}">'
                f'<span class="node-index">{node.node_index}</span>'
                f'<span class="node-name">{escape(node.node_name)}</span>'
                f'<span class="node-status">{status_text}</span>'
                f'<div class="node-summary">{summary}</div>'
                f"</div>"
            )

    status_text = project.get_status_display()
    return (
        f'<div class="creation-progress-card" data-project-id="{project.id}">'
        f'<div class="progress-header">'
        f'<span class="progress-status">{escape(status_text)}</span>'
        f'<span class="progress-percent">{project.progress_percent}%</span>'
        f'</div>'
        f'<div class="progress-bar"><div class="progress-fill" style="width:{project.progress_percent}%"></div></div>'
        f'<div class="progress-nodes">{"".join(nodes_html_parts)}</div>'
        f"</div>"
    )


def _render_result_html(project: Project) -> str:
    """渲染剧本结果 HTML 片段

    真实环境中由 skill 模块在第 7 节点完成后生成，
    此处为安全的 fallback：使用 Project.title + 节点摘要构造一个
    仅用于前端展示的基础 HTML，不含任何原始剧本结构。
    """
    # 优先使用 skill 层生成并写入的预渲染 HTML
    if project.rendered_result_html:
        return project.rendered_result_html

    title = project.title or f"未命名剧本 · {project.theme}"
    nodes_html = "".join(
        f'<li class="result-node-item">'
        f'<span class="idx">{n.node_index}.</span> '
        f'<span class="name">{escape(n.node_name)}</span>'
        f'<span class="status">{escape(n.get_status_display())}</span>'
        f"</li>"
        for n in project.nodes.all().order_by("node_index")
    )
    return (
        f'<div class="creation-result-card" data-project-id="{project.id}">'
        f'<h3 class="result-title">{escape(title)}</h3>'
        f'<p class="result-meta">题材：{escape(project.theme)} · 集数：{project.episode_count} 集</p>'
        f'<ul class="result-nodes">{nodes_html}</ul>'
        f'<div class="result-watermark" style="opacity:.5;font-size:12px;">'
        f'仅供 {project.user_id} 查看 · 含数字水印，禁止二次传播'
        f"</div>"
        f"</div>"
    )


def _render_share_html(share: ShareLink) -> str:
    """渲染分享页 HTML 片段

    与 _render_result_html 类似，但分享视图下不暴露用户信息，
    并在水印中包含 share token 以便溯源。
    """
    project = share.project
    title = share.custom_title or project.title or f"未命名剧本 · {project.theme}"
    return (
        f'<div class="share-result-card" data-share-token="{share.token}">'
        f'<h3 class="share-title">{escape(title)}</h3>'
        f'<p class="share-meta">题材：{escape(project.theme)} · 集数：{project.episode_count} 集</p>'
        f'<div class="share-body">'
        f'<p>此内容为分享视图，含分享者不可见的数字水印以防止恶意传播。</p>'
        f"</div>"
        f'<div class="share-watermark" style="opacity:.45;font-size:12px;">'
        f'分享 token: {share.token[:8]}… · 仅供查看'
        f"</div>"
        f"</div>"
    )


# ============================================================
# CreationService - 主服务类
# ============================================================
class CreationService:
    """创作服务

    所有与创作相关的业务逻辑均在此实现。
    """

    # 根据集数估算完成分钟数（粗略估算，实际由 skill 引擎决定）
    @staticmethod
    def _estimate_minutes(episode_count: int) -> int:
        base = 3  # 基础耗时
        per_episode = 0.3  # 每集额外分钟（粗略）
        return max(1, int(base + episode_count * per_episode))

    # ---------- 1. 提交创作任务 ----------
    @staticmethod
    @transaction.atomic
    def submit(user, data: dict) -> Tuple[Project, int]:
        """提交创作任务

        :param user: 当前登录用户
        :param data: 经 CreationSubmitSerializer 校验过的 dict
                     含 theme / core_idea / episode_count / format_variant
                     audience / reference_work
        :return: (Project 对象, 预计完成分钟数)
        :raises PermissionDenied: 非会员或次数不足
        """
        # 1) 校验会员状态
        is_member_valid, _msg = MembershipService.check_membership_status(user)
        if not is_member_valid:
            raise PermissionDenied("需有效会员身份才可提交创作任务")

        # 2) 扣除一次创作次数（若为无限套餐则不扣）
        consumed, remaining = MembershipService.consume_creation(user)
        if not consumed:
            raise PermissionDenied("创作次数不足，请升级会员或等待次日重置")

        # 3) 创建 Project
        current_membership = MembershipService.get_current_membership(user)

        project = Project.objects.create(
            user=user,
            theme=data["theme"],
            core_idea=data["core_idea"],
            episode_count=data["episode_count"],
            format_variant=data["format_variant"],
            audience=data.get("audience", ""),
            reference_work=data.get("reference_work", ""),
            user_membership=current_membership,
            status=Project.STATUS_PENDING,
            current_node_index=0,
            total_nodes=len(PIPELINE_NODES),
            progress_percent=0,
            title=f"{data['theme']} · {timezone.now().strftime('%Y%m%d%H%M')}",
            total_duration_minutes=0,
        )

        # 4) 预创建 7 个节点记录（状态 pending）
        CreationNode.objects.bulk_create(
            [
                CreationNode(
                    project=project,
                    node_index=meta["index"],
                    node_name=meta["name"],
                    node_description=meta["description"],
                    status=CreationNode.STATUS_PENDING,
                )
                for meta in PIPELINE_NODES
            ]
        )

        # 5) 生成初始进度 HTML（便于前端立即展示）
        project.rendered_progress_html = _render_progress_html(project)
        project.save(update_fields=["rendered_progress_html"])

        # 6) 异步触发 7 节点流水线（真实环境使用 Celery delay）
        #    此处使用懒导入以避免循环依赖
        try:
            from .tasks import run_creation_pipeline

            run_creation_pipeline.delay(str(project.id))
            logger.info("[Creation] 已提交异步任务 project=%s user=%s", project.id, user.id)
        except Exception as exc:  # noqa: BLE001
            # Celery 不可用也不影响数据记录，仅记录日志
            logger.warning("[Creation] Celery delay 失败: %s", exc)

        estimated_minutes = CreationService._estimate_minutes(project.episode_count)
        return project, estimated_minutes

    # ---------- 2. 查询进度 ----------
    @staticmethod
    def get_progress(project_id: str, user) -> dict:
        """查询创作进度

        :return: dict - 仅包含状态 + 预渲染 HTML 片段，不暴露原始数据结构
        """
        project = CreationService._get_user_project(project_id, user)

        # 每次查询更新一次 progress_html（节点状态可能已改变）
        project.rendered_progress_html = _render_progress_html(project)
        project.save(update_fields=["rendered_progress_html"])

        # 若已完成，生成一次性下载 token（15 分钟有效）
        download_token_str = ""
        if project.status == Project.STATUS_COMPLETED:
            try:
                dl = DownloadToken.objects.create(
                    project=project,
                    user=user,
                    token=DownloadToken.generate_token(),
                    file_format=ScriptWork.FORMAT_MARKDOWN,
                    expires_at=timezone.now() + timedelta(minutes=15),
                )
                download_token_str = dl.token
            except Exception as exc:  # noqa: BLE001
                logger.warning("[Creation] 生成下载 token 失败: %s", exc)

        result = {
            "status": project.status,
            "status_text": project.get_status_display(),
            "current_node": project.current_node_index,
            "total_nodes": project.total_nodes,
            "progress_percent": project.progress_percent,
            "rendered_progress_html": project.rendered_progress_html,
            "rendered_result_html": (
                _render_result_html(project)
                if project.status == Project.STATUS_COMPLETED
                else ""
            ),
            "download_token": download_token_str,
            "error_message": project.error_message if project.status == Project.STATUS_FAILED else "",
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        return result

    # ---------- 3. 项目详情 ----------
    @staticmethod
    def get_project_detail(project_id: str, user) -> dict:
        """获取作品详情（与 progress 类似，仅用于作品详情页）

        安全：只返回预渲染 HTML，不暴露原始剧本结构。
        """
        project = CreationService._get_user_project(project_id, user)
        return {
            "project_id": str(project.id),
            "title": project.title,
            "theme": project.theme,
            "episode_count": project.episode_count,
            "format_variant": project.format_variant,
            "status": project.status,
            "status_text": project.get_status_display(),
            "progress_percent": project.progress_percent,
            "audience": project.audience,
            "reference_work": project.reference_work,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "completed_at": project.completed_at,
            # 仅以预渲染 HTML 形式返回内容
            "rendered_result_html": _render_result_html(project),
            "rendered_progress_html": _render_progress_html(project),
        }

    # ---------- 4. 用户作品列表 ----------
    @staticmethod
    def list_user_projects(user, status_filter: Optional[str] = None):
        """获取用户的创作作品列表

        :param status_filter: 可选，按 status 过滤（pending / running / completed / failed）
        :return: QuerySet[Project]
        """
        qs = Project.objects.filter(user=user).order_by("-created_at")
        if status_filter and status_filter in {
            Project.STATUS_PENDING,
            Project.STATUS_RUNNING,
            Project.STATUS_COMPLETED,
            Project.STATUS_FAILED,
        }:
            qs = qs.filter(status=status_filter)
        return qs

    # ---------- 5. 生成分享链接 ----------
    @staticmethod
    @transaction.atomic
    def generate_share_link(
        project_id: str,
        user,
        view_limit: int = 100,
        valid_days: int = 7,
        allow_download: bool = False,
        custom_title: str = "",
    ) -> dict:
        """为作品生成分享链接

        :return: dict - 含 share_id / share_token / share_url / expires_at / ...
        """
        project = CreationService._get_user_project(project_id, user)
        if project.status != Project.STATUS_COMPLETED:
            raise PermissionDenied("仅已完成的作品可分享")

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

        # 构造分享 URL（真实环境从 settings 读取前端域名）
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

    # ---------- 6. 通过 share token 获取分享视图 ----------
    @staticmethod
    def get_share_view(share_token: str) -> dict:
        """匿名访问分享页

        仅返回预渲染 HTML + 元信息，绝不暴露原始剧本结构。
        """
        try:
            share = ShareLink.objects.select_related("project", "user").get(
                token=share_token
            )
        except ObjectDoesNotExist:
            raise PermissionDenied("分享链接无效或已过期")

        if not share.is_available:
            raise PermissionDenied("分享链接已失效或查看次数已用完")

        # 记录一次查看
        share.record_view()

        project = share.project
        if project.status != Project.STATUS_COMPLETED:
            raise PermissionDenied("该作品尚未完成")

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

    # ---------- 7. 下载剧本 ----------
    @staticmethod
    def download_script(
        project_id: str,
        user,
        file_format: str = "md",
    ) -> Tuple[bytes, str, str]:
        """下载剧本（返回二进制内容）

        :param project_id: 项目ID
        :param user: 当前用户（必须为作品创建者）
        :param file_format: md / html / zip / pdf
        :return: (file_bytes, file_name, content_type)
        :raises PermissionDenied: 未完成 / 非作者
        """
        project = CreationService._get_user_project(project_id, user)
        if project.status != Project.STATUS_COMPLETED:
            raise PermissionDenied("未完成的作品不可下载")

        # 查找已有 ScriptWork；若不存在则在内存中构造基础文本
        #   真实环境：ScriptWork.storage_path 指向 MinIO/OSS 路径，由 skill 层上传
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
            # 真实环境：从对象存储读取 bytes 并返回
            #   此处保留占位逻辑（具体实现依赖 storage backend）
            file_bytes = _read_storage_bytes(work.storage_path)
            if file_bytes:
                return file_bytes, file_name, content_type

        # fallback：生成一份仅含元信息与数字水印的占位文本
        #   在真实部署中永远不应走到这里——ScriptWork 始终存在
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

        return content, file_name, content_type

    # ---------- 8. 通过下载 token 获取（一次性短时效下载） ----------
    @staticmethod
    def download_by_token(
        token: str,
        file_format: str = "md",
    ) -> Tuple[bytes, str, str]:
        """使用一次性下载 token 下载剧本

        安全：
        - token 必须在有效期内且未被使用
        - 使用后立即标记为已使用
        - 不要求用户登录（便于分享下载场景）
        """
        try:
            dl = DownloadToken.objects.select_related("project", "user").get(
                token=token
            )
        except ObjectDoesNotExist:
            raise PermissionDenied("下载链接无效或已过期")

        if not dl.is_valid:
            raise PermissionDenied("下载链接已使用或已过期")

        # 标记已使用（一次性）
        dl.mark_used()

        return CreationService.download_script(
            str(dl.project.id), dl.user, file_format or dl.file_format
        )

    # ---------- 辅助：校验用户归属 ----------
    @staticmethod
    def _get_user_project(project_id: str, user) -> Project:
        """获取并校验 project 归属（必须为当前用户创建）"""
        try:
            project = Project.objects.get(id=project_id)
        except ObjectDoesNotExist:
            raise PermissionDenied("作品不存在或无访问权限")
        if project.user_id != user.id:
            raise PermissionDenied("无权限访问该作品")
        return project


# ============================================================
# 本地文件/对象存储读取（简单封装，真实部署替换为 MinIO/OSS SDK）
# ============================================================
def _read_storage_bytes(storage_path: str) -> Optional[bytes]:
    """读取存储路径的字节内容

    若路径不存在或不是文件，返回 None。
    真实部署应替换为 django-storages / MinIO SDK / OSS SDK。
    """
    if not storage_path:
        return None
    try:
        # 仅当 storage_path 指向本地可读文件时尝试读取（安全兜底）
        if os.path.isabs(storage_path) and os.path.isfile(storage_path):
            with open(storage_path, "rb") as f:
                return f.read()
    except OSError as exc:
        logger.warning("[Creation] 读取存储文件失败: %s", exc)
    return None

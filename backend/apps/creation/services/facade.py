"""CreationService 门面 — 静态方法委托至各子模块。"""

from typing import Optional, Tuple

from django.db import transaction

from ..models import Project
from . import progress, share_download, submission, workspace, works
from ._helpers import _get_user_project as _get_user_project_impl


class CreationService:
    """创作服务 — 所有与创作相关的业务逻辑入口。"""

    @staticmethod
    def _estimate_minutes(episode_count: int) -> int:
        return submission._estimate_minutes(episode_count)

    @staticmethod
    @transaction.atomic
    def submit(user, data: dict) -> Tuple[Project, int]:
        return submission.submit(user, data)

    @staticmethod
    def get_workspace(project_id: str, user) -> dict:
        return workspace.get_workspace(project_id, user)

    @staticmethod
    @transaction.atomic
    def save_workspace_skill(project_id: str, user, node_index: int, data: dict) -> dict:
        return workspace.save_workspace_skill(project_id, user, node_index, data)

    @staticmethod
    @transaction.atomic
    def acknowledge_quality_alert(project_id: str, user, node_index: int, alert_code: str) -> dict:
        return workspace.acknowledge_quality_alert(project_id, user, node_index, alert_code)

    @staticmethod
    @transaction.atomic
    def trigger_skill_generation(
        project_id: str,
        user,
        node_index: int,
        *,
        script_from: Optional[int] = None,
        script_to: Optional[int] = None,
        batch_size: Optional[int] = None,
        regenerate: bool = False,
        outline_mode: Optional[str] = None,
        outline_stage_key: Optional[str] = None,
    ) -> dict:
        return workspace.trigger_skill_generation(
            project_id,
            user,
            node_index,
            script_from=script_from,
            script_to=script_to,
            batch_size=batch_size,
            regenerate=regenerate,
            outline_mode=outline_mode,
            outline_stage_key=outline_stage_key,
        )

    @staticmethod
    def get_progress(project_id: str, user) -> dict:
        return progress.get_progress(project_id, user)

    @staticmethod
    @transaction.atomic
    def confirm_node(project_id: str, user) -> Project:
        return progress.confirm_node(project_id, user)

    @staticmethod
    @transaction.atomic
    def regenerate_node(project_id: str, user, node_index: Optional[int] = None) -> Project:
        return progress.regenerate_node(project_id, user, node_index)

    @staticmethod
    def get_project_detail(project_id: str, user) -> dict:
        return works.get_project_detail(project_id, user)

    @staticmethod
    def list_user_projects(
        user,
        status_filter: Optional[str] = None,
        *,
        keyword: str = "",
        ordering: str = "-created_at",
    ):
        return works.list_user_projects(
            user,
            status_filter,
            keyword=keyword,
            ordering=ordering,
        )

    @staticmethod
    def _reconcile_project_running_state(
        project: Project,
        *,
        aggressive: bool = False,
    ) -> Project:
        return works._reconcile_project_running_state(project, aggressive=aggressive)

    @staticmethod
    @transaction.atomic
    def delete_user_project(project_id: str, user) -> dict:
        return works.delete_user_project(project_id, user)

    @staticmethod
    @transaction.atomic
    def admin_delete_project(project_id: str) -> dict:
        return works.admin_delete_project(project_id)

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
        return share_download.generate_share_link(
            project_id,
            user,
            view_limit=view_limit,
            valid_days=valid_days,
            allow_download=allow_download,
            custom_title=custom_title,
        )

    @staticmethod
    def get_share_view(share_token: str) -> dict:
        return share_download.get_share_view(share_token)

    @staticmethod
    def download_script(
        project_id: str,
        user,
        file_format: str = "md",
    ) -> Tuple[bytes, str, str]:
        return share_download.download_script(project_id, user, file_format)

    @staticmethod
    def download_by_token(
        token: str,
        file_format: str = "md",
    ) -> Tuple[bytes, str, str]:
        return share_download.download_by_token(token, file_format)

    @staticmethod
    def _get_user_project(project_id: str, user) -> Project:
        return _get_user_project_impl(project_id, user)

    @staticmethod
    def run_work_agent(project_id: str, user, agent_id: str) -> dict:
        return works.run_work_agent(project_id, user, agent_id)

    @staticmethod
    def apply_work_polish(
        project_id: str,
        user,
        *,
        indices: Optional[list] = None,
        apply_all: bool = False,
        patch_script_fields: bool = False,
    ) -> dict:
        return works.apply_work_polish(
            project_id,
            user,
            indices=indices,
            apply_all=apply_all,
            patch_script_fields=patch_script_fields,
        )

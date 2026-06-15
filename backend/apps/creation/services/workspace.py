"""技能工作台相关服务。"""

from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.common.user_messages import safe_api_message

from ._helpers import _get_user_project


def get_workspace(project_id: str, user) -> dict:
    """技能工作台数据。"""
    project = _get_user_project(project_id, user)
    from ..workspace.workspace_service import build_workspace_payload

    return build_workspace_payload(project)


@transaction.atomic
def save_workspace_skill(project_id: str, user, node_index: int, data: dict) -> dict:
    project = _get_user_project(project_id, user)
    from ..workspace.workspace_service import save_skill_content

    try:
        return save_skill_content(project, int(node_index), data)
    except PermissionDenied:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PermissionDenied(safe_api_message(exc, "保存失败")) from exc


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
    """触发单个技能生成。"""
    project = _get_user_project(project_id, user)
    from ..workspace.workspace_service import generate_skill

    try:
        return generate_skill(
            project,
            int(node_index),
            script_from=script_from,
            script_to=script_to,
            batch_size=batch_size,
            regenerate=regenerate,
            outline_mode=outline_mode,
            outline_stage_key=outline_stage_key,
        )
    except PermissionDenied:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PermissionDenied(safe_api_message(exc, "无法启动技能生成")) from exc

# -*- coding: utf-8 -*-
"""Drama Skills 后台任务。"""
from __future__ import annotations

import logging

from django.tasks import task

logger = logging.getLogger(__name__)


@task(queue_name="creation")
def run_drama_role(drama_execution_id: str, agent_run_id: str = "") -> dict:
    """执行 Drama 角色并同步 DramaRoleExecution 状态。"""
    from apps.drama.services import DramaRoleRunService

    return DramaRoleRunService.execute_role(drama_execution_id, agent_run_id=agent_run_id)

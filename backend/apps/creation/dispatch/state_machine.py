# -*- coding: utf-8 -*-
"""统一任务状态机

定义 CreationTask 合法状态流转规则，禁止跨态跳转。
"""
from __future__ import annotations

from typing import Set

from apps.creation.models import CreationTask

# 合法的状态流转边 (from_state, to_state)
_VALID_TRANSITIONS: Set[tuple] = {
    (CreationTask.STATE_PENDING,   CreationTask.STATE_RUNNING),
    (CreationTask.STATE_PENDING,   CreationTask.STATE_CANCELLED),
    (CreationTask.STATE_RUNNING,   CreationTask.STATE_PAUSED),
    (CreationTask.STATE_RUNNING,   CreationTask.STATE_COMPLETED),
    (CreationTask.STATE_RUNNING,   CreationTask.STATE_FAILED),
    (CreationTask.STATE_RUNNING,   CreationTask.STATE_CANCELLED),
    (CreationTask.STATE_PAUSED,    CreationTask.STATE_RUNNING),
    (CreationTask.STATE_PAUSED,    CreationTask.STATE_CANCELLED),
    (CreationTask.STATE_FAILED,    CreationTask.STATE_RETRYING),
    (CreationTask.STATE_RETRYING,  CreationTask.STATE_RUNNING),
    (CreationTask.STATE_RETRYING,  CreationTask.STATE_FAILED),
}

# 终态：进入后不可再流转
_TERMINAL_STATES: Set[str] = {
    CreationTask.STATE_COMPLETED,
    CreationTask.STATE_CANCELLED,
}


class TaskStateMachineError(Exception):
    pass


def validate_transition(from_state: str, to_state: str) -> None:
    """校验状态流转是否合法，不合法则抛出 TaskStateMachineError"""
    if from_state in _TERMINAL_STATES:
        raise TaskStateMachineError(
            f"任务已处于终态 [{from_state}]，不可再流转到 [{to_state}]"
        )
    if (from_state, to_state) not in _VALID_TRANSITIONS:
        raise TaskStateMachineError(
            f"非法状态流转：[{from_state}] → [{to_state}]"
        )


def is_terminal(state: str) -> bool:
    return state in _TERMINAL_STATES

# -*- coding: utf-8 -*-
"""TaskDispatchService — 旧调度入口已移除。"""


class LegacyRemovedError(RuntimeError):
    """旧 CreationTask / 批量调度链路已下线。"""


class TaskDispatchService:
    """统一任务调度服务（已废弃，调用将抛出 LegacyRemovedError）。"""

    @classmethod
    def dispatch(cls, *args, **kwargs):
        raise LegacyRemovedError(
            "CreationTask 调度已移除，请使用独立 Agent 运行或工作流引擎发起创作。"
        )

    @classmethod
    def retry(cls, *args, **kwargs):
        raise LegacyRemovedError("CreationTask 重试已移除。")

    @classmethod
    def cancel(cls, *args, **kwargs):
        raise LegacyRemovedError("CreationTask 取消已移除。")

    @classmethod
    def recover_stale(cls, *args, **kwargs):
        raise LegacyRemovedError("CreationTask 僵死恢复已移除。")

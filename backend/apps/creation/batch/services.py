# -*- coding: utf-8 -*-
"""
批量创作服务层。
"""

import logging
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.creation.models import Project
from apps.creation.services.sse_progress import broadcast_progress
from apps.workflow.models import FusionPipelinePack

from .models import BatchJob, BatchProject

logger = logging.getLogger(__name__)

# CSV 最大行数限制
MAX_CSV_ROWS = 1000


class BatchJobService:
    """批量创作任务服务"""

    @classmethod
    def create_from_csv(
        cls,
        user,
        csv_data: list,
        name: str,
        theme: str,
        pipeline_pack_id: Optional[str] = None,
    ) -> BatchJob:
        """
        从 CSV 数据创建批量任务，返回 BatchJob。

        Args:
            user: 所属用户
            csv_data: CSV 行列表，每行包含 core_idea 和 row_index
            name: 任务名称
            theme: 题材
            pipeline_pack_id: 工作流包 ID

        Returns:
            BatchJob 实例
        """
        if not csv_data:
            raise ValueError("CSV 数据不能为空")
        if len(csv_data) > MAX_CSV_ROWS:
            raise ValueError(f"CSV 数据超过最大限制 {MAX_CSV_ROWS} 行")

        # 验证 pipeline_pack_id 并获取对象
        pipeline_pack = None
        if pipeline_pack_id:
            try:
                pipeline_pack = FusionPipelinePack.objects.get(id=pipeline_pack_id)
            except FusionPipelinePack.DoesNotExist:
                raise ValueError(f"工作流包不存在: {pipeline_pack_id}")

        with transaction.atomic():
            batch_job = BatchJob.objects.create(
                user=user,
                name=name,
                theme=theme,
                csv_data=csv_data,
                total_count=len(csv_data),
                pipeline_pack_id=pipeline_pack_id,
                status=BatchJob.STATUS_PENDING,
            )

            # 创建子项目
            batch_projects = []
            for row in csv_data:
                row_index = row.get("row_index", 0)
                core_idea = row.get("core_idea", "")
                extra_params = {k: v for k, v in row.items() if k not in ("row_index", "core_idea")}

                batch_projects.append(
                    BatchProject(
                        batch_job=batch_job,
                        row_index=row_index,
                        core_idea=core_idea,
                        extra_params=extra_params,
                        status=BatchProject.STATUS_PENDING,
                    )
                )

            BatchProject.objects.bulk_create(batch_projects)

        logger.info(
            "[BatchJob] 创建批量任务 name=%s user=%s total=%d",
            name,
            user.id,
            len(csv_data),
        )
        return batch_job

    @classmethod
    def dispatch(cls, batch_job_id: str) -> None:
        """
        将批量任务加入队列，由 Celery worker 执行。

        Args:
            batch_job_id: 批量任务 ID
        """
        try:
            batch_job = BatchJob.objects.get(id=batch_job_id)
        except BatchJob.DoesNotExist:
            raise ValueError(f"批量任务不存在: {batch_job_id}")

        if batch_job.status not in (BatchJob.STATUS_PENDING, BatchJob.STATUS_PAUSED):
            raise ValueError(f"批量任务状态不允许执行: {batch_job.status}")

        batch_job.status = BatchJob.STATUS_RUNNING
        batch_job.save(update_fields=["status", "updated_at"])

        # 将每个子项目加入 Celery 队列
        from apps.creation.batch.tasks import process_batch_item

        pending_projects = batch_job.batch_projects.filter(
            status=BatchProject.STATUS_PENDING
        ).values_list("id", flat=True)

        for batch_project_id in pending_projects:
            process_batch_item.delay(str(batch_project_id))

        logger.info(
            "[BatchJob] 批量任务已分发 batch_job_id=%s project_count=%d",
            batch_job_id,
            len(pending_projects),
        )

    @classmethod
    def get_progress(cls, batch_job_id: str) -> dict:
        """
        返回进度信息。

        Args:
            batch_job_id: 批量任务 ID

        Returns:
            dict: {total, completed, failed, rate}
        """
        try:
            batch_job = BatchJob.objects.get(id=batch_job_id)
        except BatchJob.DoesNotExist:
            raise ValueError(f"批量任务不存在: {batch_job_id}")

        total = batch_job.total_count
        completed = batch_job.completed_count
        failed = batch_job.failed_count
        rate = (completed + failed) / total * 100 if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "rate": round(rate, 2),
        }

    @classmethod
    def pause_job(cls, batch_job_id: str) -> None:
        """
        暂停批量任务。

        Args:
            batch_job_id: 批量任务 ID
        """
        try:
            batch_job = BatchJob.objects.get(id=batch_job_id)
        except BatchJob.DoesNotExist:
            raise ValueError(f"批量任务不存在: {batch_job_id}")

        if batch_job.status != BatchJob.STATUS_RUNNING:
            raise ValueError(f"批量任务状态不允许暂停: {batch_job.status}")

        batch_job.status = BatchJob.STATUS_PAUSED
        batch_job.save(update_fields=["status", "updated_at"])

        logger.info("[BatchJob] 批量任务已暂停 batch_job_id=%s", batch_job_id)

    @classmethod
    def resume_job(cls, batch_job_id: str) -> None:
        """
        恢复批量任务。

        Args:
            batch_job_id: 批量任务 ID
        """
        try:
            batch_job = BatchJob.objects.get(id=batch_job_id)
        except BatchJob.DoesNotExist:
            raise ValueError(f"批量任务不存在: {batch_job_id}")

        if batch_job.status != BatchJob.STATUS_PAUSED:
            raise ValueError(f"批量任务状态不允许恢复: {batch_job.status}")

        batch_job.status = BatchJob.STATUS_RUNNING
        batch_job.save(update_fields=["status", "updated_at"])

        # 重新分发待执行的子项目
        from apps.creation.batch.tasks import process_batch_item

        pending_projects = batch_job.batch_projects.filter(
            status=BatchProject.STATUS_PENDING
        ).values_list("id", flat=True)

        for batch_project_id in pending_projects:
            process_batch_item.delay(str(batch_project_id))

        logger.info(
            "[BatchJob] 批量任务已恢复 batch_job_id=%s pending_count=%d",
            batch_job_id,
            len(pending_projects),
        )


class BatchExecutionConsumer:
    """Celery Task consumer，逐条消费批量任务中的项目"""

    @classmethod
    def process_batch_item(cls, batch_project_id: str) -> dict:
        """
        执行单个子项目，返回结果。

        Args:
            batch_project_id: BatchProject ID

        Returns:
            dict: 执行结果
        """
        try:
            batch_project = BatchProject.objects.select_related(
                "batch_job", "batch_job__user"
            ).get(id=batch_project_id)
        except BatchProject.DoesNotExist:
            logger.error("[Batch] BatchProject 不存在: %s", batch_project_id)
            return {"status": "error", "message": "BatchProject not found"}

        batch_job = batch_project.batch_job

        # 检查批量任务是否被暂停
        if batch_job.status == BatchJob.STATUS_PAUSED:
            logger.info(
                "[Batch] 批量任务已暂停，跳过 batch_project_id=%s",
                batch_project_id,
            )
            return {"status": "skipped", "reason": "batch_paused"}

        # 更新子项目状态为运行中
        batch_project.status = BatchProject.STATUS_RUNNING
        batch_project.save(update_fields=["status"])

        try:
            # 1. 创建 creation.Project
            user = batch_job.user

            # 获取 pipeline_pack 对象
            pipeline_pack_obj = None
            if batch_job.pipeline_pack_id:
                try:
                    pipeline_pack_obj = FusionPipelinePack.objects.get(id=batch_job.pipeline_pack_id)
                except FusionPipelinePack.DoesNotExist:
                    pass

            project = Project.objects.create(
                user=user,
                theme=batch_job.theme,
                core_idea=batch_project.core_idea,
                episode_count=batch_project.extra_params.get("episode_count", 30),
                format_variant=batch_project.extra_params.get("format_variant", "B"),
                audience=batch_project.extra_params.get("audience", ""),
                reference_work=batch_project.extra_params.get("reference_work", ""),
                target_platform=batch_project.extra_params.get("target_platform", "douyin"),
                creation_entry=batch_project.extra_params.get("creation_entry", "from-scratch"),
                pipeline_mode=Project.MODE_WORKSPACE,
                pipeline_pack=pipeline_pack_obj,
            )

            # 关联 BatchProject 和 Project
            batch_project.project = project
            batch_project.save(update_fields=["project"])

            # 2. 调用 creation/orchestration/run_creation_pipeline()
            from apps.creation.dispatch.service import TaskDispatchService
            from apps.creation.models import CreationTask

            TaskDispatchService.dispatch(
                project=project,
                trigger_mode=CreationTask.TRIGGER_WORKSPACE,
            )

            # 3. 更新 BatchProject 状态为完成
            batch_project.status = BatchProject.STATUS_COMPLETED
            batch_project.save(update_fields=["status"])

            # 4. 更新 BatchJob 统计计数
            cls._update_batch_job_counts(batch_job)

            # 5. 广播 SSE 进度
            cls._broadcast_progress(batch_job)

            # 6. 检查是否全部完成
            cls._check_batch_job_completion(batch_job)

            logger.info(
                "[Batch] 子项目执行成功 batch_project_id=%s project_id=%s",
                batch_project_id,
                project.id,
            )
            return {"status": "success", "project_id": str(project.id)}

        except Exception as exc:
            error_msg = str(exc)
            logger.exception(
                "[Batch] 子项目执行失败 batch_project_id=%s: %s",
                batch_project_id,
                error_msg,
            )

            # 更新子项目状态为失败
            batch_project.status = BatchProject.STATUS_FAILED
            batch_project.error_message = error_msg[:500]
            batch_project.save(update_fields=["status", "error_message"])

            # 更新 BatchJob 统计计数
            cls._update_batch_job_counts(batch_job)

            # 广播 SSE 进度
            cls._broadcast_progress(batch_job)

            # 检查是否全部完成
            cls._check_batch_job_completion(batch_job)

            return {"status": "failed", "error": error_msg}

    @classmethod
    def _update_batch_job_counts(cls, batch_job: BatchJob) -> None:
        """更新批量任务的完成/失败计数"""
        completed = batch_job.batch_projects.filter(
            status=BatchProject.STATUS_COMPLETED
        ).count()
        failed = batch_job.batch_projects.filter(
            status=BatchProject.STATUS_FAILED
        ).count()

        batch_job.completed_count = completed
        batch_job.failed_count = failed
        batch_job.save(update_fields=["completed_count", "failed_count", "updated_at"])

    @classmethod
    def _broadcast_progress(cls, batch_job: BatchJob) -> None:
        """广播 SSE 进度"""
        progress = BatchJobService.get_progress(str(batch_job.id))
        broadcast_progress(
            str(batch_job.id),
            {
                "event": "batch_progress",
                "batch_job_id": str(batch_job.id),
                "total": progress["total"],
                "completed": progress["completed"],
                "failed": progress["failed"],
                "rate": progress["rate"],
            },
        )

    @classmethod
    def _check_batch_job_completion(cls, batch_job: BatchJob) -> None:
        """检查批量任务是否全部完成"""
        total = batch_job.total_count
        completed = batch_job.completed_count
        failed = batch_job.failed_count

        if completed + failed >= total:
            if failed > 0 and completed == 0:
                batch_job.status = BatchJob.STATUS_FAILED
            else:
                batch_job.status = BatchJob.STATUS_COMPLETED
            batch_job.save(update_fields=["status", "updated_at"])
            logger.info(
                "[Batch] 批量任务全部完成 batch_job_id=%s completed=%d failed=%d",
                batch_job.id,
                completed,
                failed,
            )

# -*- coding: utf-8 -*-
"""
批量创作 API（Admin 视角）
"""

from uuid import UUID

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok

from .models import BatchJob, BatchProject
from .services import BatchJobService


class BatchJobListView(APIView):
    """GET /api/admin/batch/ — 批量任务列表"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """批量任务列表"""
        status_filter = request.query_params.get("status", "").strip()
        keyword = request.query_params.get("keyword", "").strip()

        try:
            page = max(1, int(request.query_params.get("page", "1")))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(50, max(1, int(request.query_params.get("page_size", "20"))))
        except (TypeError, ValueError):
            page_size = 20

        qs = BatchJob.objects.filter(user=request.user).order_by("-created_at")
        if status_filter in dict(BatchJob.STATUS_CHOICES):
            qs = qs.filter(status=status_filter)
        if keyword:
            qs = qs.filter(name__icontains=keyword)

        total = qs.count()
        start = (page - 1) * page_size
        page_qs = list(qs[start : start + page_size])

        items = [
            {
                "id": str(job.id),
                "name": job.name,
                "status": job.status,
                "status_text": job.get_status_display(),
                "total_count": job.total_count,
                "completed_count": job.completed_count,
                "failed_count": job.failed_count,
                "theme": job.theme,
                "pipeline_pack_id": str(job.pipeline_pack_id) if job.pipeline_pack_id else None,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            for job in page_qs
        ]

        total_pages = (total + page_size - 1) // page_size if page_size else 0
        pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

        response = api_ok(items)
        response.data["pagination"] = pagination
        return response


class BatchJobCreateView(APIView):
    """POST /api/admin/batch/ — 上传 CSV 创建批量任务"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """
        上传 CSV 创建批量任务。

        入参：{name, theme, pipeline_pack_id, csv: [{"core_idea": "...", "row_index": 1}, ...]}
        """
        name = request.data.get("name", "").strip()
        theme = request.data.get("theme", "").strip()
        pipeline_pack_id = request.data.get("pipeline_pack_id")
        csv_data = request.data.get("csv", [])

        if not name:
            return api_fail("任务名称不能为空", code=400)
        if not theme:
            return api_fail("题材不能为空", code=400)
        if not csv_data:
            return api_fail("CSV 数据不能为空", code=400)

        if not isinstance(csv_data, list):
            return api_fail("CSV 数据格式错误，需要为列表", code=400)

        # 验证 pipeline_pack_id 格式
        if pipeline_pack_id:
            try:
                UUID(str(pipeline_pack_id))
            except ValueError:
                return api_fail("工作流包 ID 格式错误", code=400)

        try:
            batch_job = BatchJobService.create_from_csv(
                user=request.user,
                csv_data=csv_data,
                name=name,
                theme=theme,
                pipeline_pack_id=str(pipeline_pack_id) if pipeline_pack_id else None,
            )
        except ValueError as e:
            return api_fail(str(e), code=400)
        except Exception as e:
            return api_fail(f"创建批量任务失败: {str(e)}", code=500)

        return api_ok(
            {
                "id": str(batch_job.id),
                "name": batch_job.name,
                "status": batch_job.status,
                "total_count": batch_job.total_count,
                "theme": batch_job.theme,
                "created_at": batch_job.created_at.isoformat() if batch_job.created_at else None,
            }
        )


class BatchJobDetailView(APIView):
    """GET /api/admin/batch/<id>/ — 批量任务详情（含子项目列表）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, batch_id: str):
        """批量任务详情"""
        try:
            batch_job = BatchJob.objects.get(id=batch_id)
        except BatchJob.DoesNotExist:
            return api_fail("批量任务不存在", code=404)
        except ValueError:
            return api_fail("批量任务 ID 格式错误", code=400)

        # 子项目列表
        batch_projects = batch_job.batch_projects.all().order_by("row_index")
        projects = [
            {
                "id": str(bp.id),
                "row_index": bp.row_index,
                "core_idea": bp.core_idea,
                "extra_params": bp.extra_params,
                "status": bp.status,
                "status_text": bp.get_status_display(),
                "error_message": bp.error_message,
                "project_id": str(bp.project_id) if bp.project_id else None,
                "created_at": bp.created_at.isoformat() if bp.created_at else None,
            }
            for bp in batch_projects
        ]

        progress = BatchJobService.get_progress(str(batch_job.id))

        data = {
            "id": str(batch_job.id),
            "name": batch_job.name,
            "status": batch_job.status,
            "status_text": batch_job.get_status_display(),
            "theme": batch_job.theme,
            "pipeline_pack_id": str(batch_job.pipeline_pack_id) if batch_job.pipeline_pack_id else None,
            "total_count": batch_job.total_count,
            "completed_count": batch_job.completed_count,
            "failed_count": batch_job.failed_count,
            "created_at": batch_job.created_at.isoformat() if batch_job.created_at else None,
            "updated_at": batch_job.updated_at.isoformat() if batch_job.updated_at else None,
            "projects": projects,
            "progress": progress,
        }

        return api_ok(data)


class BatchJobDispatchView(APIView):
    """POST /api/admin/batch/<id>/dispatch/ — 启动批量执行"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str):
        """启动批量执行"""
        try:
            batch_job = BatchJob.objects.get(id=batch_id)
        except BatchJob.DoesNotExist:
            return api_fail("批量任务不存在", code=404)
        except ValueError:
            return api_fail("批量任务 ID 格式错误", code=400)

        try:
            BatchJobService.dispatch(str(batch_job.id))
        except ValueError as e:
            return api_fail(str(e), code=400)
        except Exception as e:
            return api_fail(f"启动批量执行失败: {str(e)}", code=500)

        return api_ok({"status": batch_job.status})


class BatchJobPauseView(APIView):
    """POST /api/admin/batch/<id>/pause/ — 暂停批量任务"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str):
        """暂停批量任务"""
        try:
            batch_job = BatchJob.objects.get(id=batch_id)
        except BatchJob.DoesNotExist:
            return api_fail("批量任务不存在", code=404)
        except ValueError:
            return api_fail("批量任务 ID 格式错误", code=400)

        try:
            BatchJobService.pause_job(str(batch_job.id))
        except ValueError as e:
            return api_fail(str(e), code=400)
        except Exception as e:
            return api_fail(f"暂停批量任务失败: {str(e)}", code=500)

        return api_ok({"status": BatchJob.STATUS_PAUSED})


class BatchJobResumeView(APIView):
    """POST /api/admin/batch/<id>/resume/ — 恢复批量任务"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str):
        """恢复批量任务"""
        try:
            batch_job = BatchJob.objects.get(id=batch_id)
        except BatchJob.DoesNotExist:
            return api_fail("批量任务不存在", code=404)
        except ValueError:
            return api_fail("批量任务 ID 格式错误", code=400)

        try:
            BatchJobService.resume_job(str(batch_job.id))
        except ValueError as e:
            return api_fail(str(e), code=400)
        except Exception as e:
            return api_fail(f"恢复批量任务失败: {str(e)}", code=500)

        return api_ok({"status": BatchJob.STATUS_RUNNING})


class BatchProjectRetryView(APIView):
    """POST /api/admin/batch/<batch_id>/projects/<project_id>/retry/ — 重试单个子项目"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, batch_id: str, project_id: str):
        """重试单个子项目"""
        try:
            batch_job = BatchJob.objects.get(id=batch_id)
        except BatchJob.DoesNotExist:
            return api_fail("批量任务不存在", code=404)
        except ValueError:
            return api_fail("批量任务 ID 格式错误", code=400)

        try:
            batch_project = BatchProject.objects.get(id=project_id, batch_job=batch_job)
        except BatchProject.DoesNotExist:
            return api_fail("子项目不存在", code=404)
        except ValueError:
            return api_fail("子项目 ID 格式错误", code=400)

        # 重置信
        batch_project.status = BatchProject.STATUS_PENDING
        batch_project.error_message = ""
        batch_project.save(update_fields=["status", "error_message"])

        # 如果批量任务处于暂停状态，需要先恢复
        if batch_job.status == BatchJob.STATUS_PAUSED:
            batch_job.status = BatchJob.STATUS_RUNNING
            batch_job.save(update_fields=["status", "updated_at"])

        # 重新分发
        from apps.creation.batch.tasks import process_batch_item

        process_batch_item.delay(str(batch_project.id))

        return api_ok({"status": "pending"})

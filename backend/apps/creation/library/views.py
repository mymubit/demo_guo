# -*- coding: utf-8 -*-
"""
素材库 API。

提供素材的上传、查询、解析、删除等管理接口。
所有接口均需 Admin 权限。
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from django.conf import settings
from django.views.static import serve
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok

from .models import ReferenceMaterial
from .services import MaterialInjectionService, MaterialParserService


class MaterialListView(APIView):
    """素材列表 — GET /api/admin/library/materials/"""

    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        获取素材列表。
        支持分页和筛选。
        """
        user_id = request.query_params.get("user_id")
        material_type = request.query_params.get("material_type")
        parse_status = request.query_params.get("parse_status")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        qs = ReferenceMaterial.objects.all()

        if user_id:
            qs = qs.filter(user_id=user_id)
        if material_type:
            qs = qs.filter(material_type=material_type)
        if parse_status:
            qs = qs.filter(parse_status=parse_status)

        total = qs.count()
        offset = (page - 1) * page_size
        materials = qs[offset : offset + page_size]

        items = []
        for m in materials:
            items.append({
                "id": str(m.id),
                "name": m.name,
                "material_type": m.material_type,
                "material_type_label": m.get_material_type_display(),
                "file_size": m.file_size,
                "parse_status": m.parse_status,
                "parse_status_label": m.get_parse_status_display(),
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            })

        return api_ok({
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        })


class MaterialUploadView(APIView):
    """素材上传 — POST /api/admin/library/materials/upload/"""

    permission_classes = [IsAdminUser]

    def post(self, request):
        """
        上传素材文件。

        支持 multipart/form-data。
        入参：name, material_type, file
        """
        name = request.POST.get("name", "").strip()
        material_type = request.POST.get("material_type", ReferenceMaterial.TYPE_OTHER)
        uploaded_file = request.FILES.get("file")

        if not name:
            return api_fail("素材名称不能为空", code=400)
        if not uploaded_file:
            return api_fail("请上传文件", code=400)

        # 获取用户 ID（从请求参数或当前用户）
        user_id = request.POST.get("user_id")
        if user_id:
            from apps.users.models import User

            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return api_fail("用户不存在", code=404)
        else:
            user = request.user

        # 保存文件
        file_size = uploaded_file.size
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        upload_dir = os.path.join(settings.MEDIA_ROOT, "reference_materials", str(user.id))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_name)

        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # 创建素材记录
        material = ReferenceMaterial.objects.create(
            user=user,
            name=name,
            material_type=material_type,
            file_path=file_path,
            file_size=file_size,
            parse_status=ReferenceMaterial.STATUS_PARSING,
        )

        return api_ok({
            "id": str(material.id),
            "name": material.name,
            "material_type": material.material_type,
            "file_size": material.file_size,
            "parse_status": material.parse_status,
        }, message="上传成功")


class MaterialDetailView(APIView):
    """素材详情与删除 — GET/DELETE /api/admin/creation/library/materials/<id>/"""

    permission_classes = [IsAdminUser]

    def _get_material(self, material_id: str):
        try:
            return ReferenceMaterial.objects.get(pk=material_id)
        except ReferenceMaterial.DoesNotExist:
            return None

    def get(self, request, material_id: str):
        """获取素材详情。"""
        material = self._get_material(material_id)
        if material is None:
            return api_fail("素材不存在", code=404)

        return api_ok({
            "id": str(material.id),
            "user_id": str(material.user_id),
            "name": material.name,
            "material_type": material.material_type,
            "material_type_label": material.get_material_type_display(),
            "file_path": material.file_path,
            "file_size": material.file_size,
            "parsed_content": material.parsed_content,
            "parse_status": material.parse_status,
            "parse_status_label": material.get_parse_status_display(),
            "parse_error": material.parse_error,
            "created_at": material.created_at.isoformat() if material.created_at else None,
            "updated_at": material.updated_at.isoformat() if material.updated_at else None,
        })

    def delete(self, request, material_id: str):
        """删除素材及其本地文件（不可恢复）。"""
        material = self._get_material(material_id)
        if material is None:
            return api_fail("素材不存在", code=404)

        if material.file_path and os.path.exists(material.file_path):
            try:
                os.remove(material.file_path)
            except OSError:
                pass

        material.delete()
        return api_ok(message="删除成功")


class MaterialParseView(APIView):
    """素材解析 — POST /api/admin/library/materials/<id>/parse/"""

    permission_classes = [IsAdminUser]

    def post(self, request, material_id: str):
        """
        触发素材解析。

        解析完成后更新素材的 parse_status 和 parsed_content。
        """
        try:
            material = ReferenceMaterial.objects.get(pk=material_id)
        except ReferenceMaterial.DoesNotExist:
            return api_fail("素材不存在", code=404)

        if material.parse_status == ReferenceMaterial.STATUS_PARSING:
            return api_fail("素材正在解析中，请勿重复提交")

        service = MaterialParserService()
        result = service.parse(material.id)

        if "error" in result:
            return api_fail(result["error"], code=500)

        return api_ok({
            "id": str(material.id),
            "parse_status": material.parse_status,
            "parsed_content": material.parsed_content,
        }, message="解析完成")


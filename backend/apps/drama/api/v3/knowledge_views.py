# -*- coding: utf-8 -*-
"""V3 知识库只读 REST。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_error, api_response
from apps.drama.orchestrator.knowledge_catalog import list_docs, read_doc


class V3KnowledgeListView(APIView):
    """GET /api/v3/knowledge/?q=&section= — 文件索引。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        q = (request.query_params.get("q") or "").strip() or None
        section = (request.query_params.get("section") or "").strip() or None
        return api_response({"items": list_docs(q=q, section=section)})


class V3KnowledgeDocView(APIView):
    """GET /api/v3/knowledge/doc/?path= — markdown 正文。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        path = (request.query_params.get("path") or "").strip()
        if not path:
            return api_error(400, "缺少 path 查询参数")
        return api_response(read_doc(path))

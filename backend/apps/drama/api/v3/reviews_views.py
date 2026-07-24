# -*- coding: utf-8 -*-
"""V3 独立剧本评审 REST API。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import BusinessException, VALIDATION_ERROR
from apps.core.responses import api_response
from apps.drama.api.v3.serializers import (
    ScriptReviewCompareQuerySerializer,
    ScriptReviewCreateSerializer,
    ScriptReviewUploadSerializer,
)
from apps.drama.models import ScriptReview, ScriptReviewRun
from apps.drama.services import script_review_service as svc


class V3ScriptReviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        project_id = (request.query_params.get("project_id") or "").strip() or None
        items = [
            svc.serialize_review(item, include_script=False, include_runs=False)
            for item in svc.list_reviews(owner=request.user, project_id=project_id)
        ]
        return api_response({"items": items})

    def post(self, request: Request) -> Response:
        content_type = (request.content_type or "").lower()
        if "multipart/form-data" in content_type or request.FILES:
            serializer = ScriptReviewUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            upload = data["file"]
            raw = upload.read()
            text = svc.decode_upload_bytes(raw, filename=upload.name or "")
            review = svc.create_review(
                owner=request.user,
                script_text=text,
                title=data.get("title") or "",
                project_id=data.get("project_id"),
                source_type=ScriptReview.SourceType.UPLOAD,
                source_filename=upload.name or "",
            )
        else:
            serializer = ScriptReviewCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            review = svc.create_review(
                owner=request.user,
                script_text=data["script_text"],
                title=data.get("title") or "",
                project_id=data.get("project_id"),
                source_type=ScriptReview.SourceType.PASTE,
            )
        return api_response(
            svc.serialize_review(review, include_script=True, include_runs=True),
            status=201,
        )


class V3ScriptReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, review_id) -> Response:
        review = svc.get_owned_review(owner=request.user, review_id=review_id)
        return api_response(
            svc.serialize_review(review, include_script=True, include_runs=True)
        )


class V3ScriptReviewScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, review_id) -> Response:
        review = svc.get_owned_review(owner=request.user, review_id=review_id)
        review_run = svc.enqueue_review_run(
            review=review, kind=ScriptReviewRun.Kind.QUALITY
        )
        svc.dispatch_review_run(review_run)
        review_run.refresh_from_db()
        return api_response({"run": svc.serialize_run(review_run)}, status=202)


class V3ScriptReviewComplianceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, review_id) -> Response:
        review = svc.get_owned_review(owner=request.user, review_id=review_id)
        review_run = svc.enqueue_review_run(
            review=review, kind=ScriptReviewRun.Kind.COMPLIANCE
        )
        svc.dispatch_review_run(review_run)
        review_run.refresh_from_db()
        return api_response({"run": svc.serialize_run(review_run)}, status=202)


class V3ScriptReviewRunListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, review_id) -> Response:
        review = svc.get_owned_review(owner=request.user, review_id=review_id)
        kind = (request.query_params.get("kind") or "").strip()
        qs = ScriptReviewRun.objects.filter(review=review).order_by("-created_at")
        if kind:
            if kind not in ScriptReviewRun.Kind.values:
                raise BusinessException(
                    VALIDATION_ERROR,
                    "kind 须为 quality|compliance",
                    http_status=400,
                )
            qs = qs.filter(kind=kind)
        return api_response({"items": [svc.serialize_run(item) for item in qs]})


class V3ScriptReviewRunDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, review_id, run_id) -> Response:
        review = svc.get_owned_review(owner=request.user, review_id=review_id)
        try:
            run = ScriptReviewRun.objects.get(id=run_id, review=review)
        except ScriptReviewRun.DoesNotExist as exc:
            from apps.core.exceptions import NOT_FOUND

            raise BusinessException(NOT_FOUND, "评审记录不存在", http_status=404) from exc
        return api_response(svc.serialize_run(run))


class V3ScriptReviewCompareView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, review_id) -> Response:
        review = svc.get_owned_review(owner=request.user, review_id=review_id)
        serializer = ScriptReviewCompareQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return api_response(
            svc.compare_runs(
                review=review,
                run_a_id=data["a"],
                run_b_id=data["b"],
            )
        )

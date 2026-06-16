# -*- coding: utf-8 -*-
"""后台 API 视图基类。"""
from rest_framework.views import APIView


class AdminAPIView(APIView):
    """关闭 DRF 默认节流；后台路由已在 SECURITY_RATE_LIMIT_SKIP_PATHS 白名单。"""

    throttle_classes = []

"""
前台 API 路由入口

挂载于 /api/，面向 C 端用户与创作者。
业务模型与服务在 apps.users / membership / orders / creation / skill 等领域 app 中维护。
"""
from django.urls import include, path

from apps.portal.skills.urls import config_urlpatterns
from apps.system_config.urls import public_urlpatterns as system_config_public_urlpatterns
# 【运营 M4】C 端用户主动反馈 + 行为埋点上报
from apps.operations.urls import portal_urlpatterns as operations_portal_urlpatterns

app_name = "portal"

urlpatterns = [
    path("auth/", include("apps.portal.auth.urls")),
    path("users/", include("apps.portal.users.urls")),
    path("members/", include("apps.portal.membership.urls")),
    path("orders/", include("apps.portal.orders.urls")),
    path("billing/", include("apps.portal.billing.urls")),
    path("creation/", include("apps.portal.creation.urls")),
    path("workflow/", include("apps.portal.workflow.urls")),
    path("agent/", include("apps.portal.agent.urls")),
    path("works/", include("apps.portal.creation.urls_works")),
    path("skill/", include("apps.portal.config.urls")),
    # Cursor Agent 专用（只读公开）
    path("skills/", include("apps.portal.skills.urls")),
    path("configs/", include((config_urlpatterns, "portal-configs"))),
    path("system-configs/", include((system_config_public_urlpatterns, "system-configs"))),
    # 【运营 M4】C 端用户主动反馈
    path("operations/", include((operations_portal_urlpatterns, "operations"))),
]

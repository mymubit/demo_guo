"""旧接口统一 410 响应。"""
from rest_framework.response import Response

_DEFAULT_MESSAGE = (
    "该接口已废弃，请使用独立 Agent 运行接口 "
    "POST /api/creation/projects/<project_id>/agents/<agent_id>/run/"
)


def legacy_gone_response(message=None):
    return Response(
        {
            "code": 410,
            "message": message or _DEFAULT_MESSAGE,
            "data": None,
        },
        status=200,
    )


def legacy_workspace_gone_response():
    return legacy_gone_response()

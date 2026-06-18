"""旧 node_index 工作台接口统一响应。"""
from rest_framework.response import Response


def legacy_workspace_gone_response():
    return Response(
        {
            "code": 410,
            "message": (
                "该接口已废弃，请使用独立 Agent 运行接口 "
                "POST /api/creation/projects/<project_id>/agents/<agent_id>/run/"
            ),
            "data": None,
        },
        status=200,
    )

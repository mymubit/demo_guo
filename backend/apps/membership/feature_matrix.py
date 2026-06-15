# -*- coding: utf-8 -*-
"""会员权益矩阵（C 端对比展示）。"""

FREE_TIER_MATRIX = [
    {"key": "create_project", "label": "发起创作项目", "free": True, "member": True},
    {"key": "export_md", "label": "Markdown 导出", "free": True, "member": True},
    {"key": "cloud_storage", "label": "作品云端保存", "free": True, "member": True},
    {"key": "step_pipeline", "label": "分步掌控创作", "free": True, "member": True},
    {"key": "membership_open_grant", "label": "开通赠送创作币", "free": False, "member": True},
    {"key": "recharge_bonus_coins", "label": "充值额外赠送创作币", "free": False, "member": True},
    {"key": "share_link", "label": "作品分享链接", "free": False, "member": True},
    {"key": "priority_queue", "label": "优先创作队列", "free": False, "member": True},
    {"key": "pull_sheet", "label": "拉片分析", "free": False, "member": True, "coming_soon": True, "member_only": True},
    {"key": "inspiration_plan", "label": "灵感策划", "free": False, "member": True, "member_only": True},
    {"key": "benchmark", "label": "爆款对标", "free": False, "member": True, "coming_soon": True, "member_only": True},
]


def plan_feature_matrix(plan) -> list:
    features = plan.features if isinstance(plan.features, dict) else {}
    matrix = features.get("matrix")
    if isinstance(matrix, list) and matrix:
        return matrix
    items = features.get("items") or []
    if isinstance(items, list):
        return [{"key": f"item_{i}", "label": str(label), "free": False, "member": True} for i, label in enumerate(items)]
    return []


def build_feature_matrix_payload(user) -> dict:
    from apps.membership.feature_matrix_service import FeatureMatrixService
    from apps.membership.models import MembershipPlan
    from apps.membership.services import MembershipService

    membership = MembershipService.get_current_membership(user)
    plans = MembershipPlan.objects.filter(is_active=True).order_by("sort_order")
    recommended = plans.filter(is_recommended=True).first() or plans.first()
    free_matrix = FeatureMatrixService.resolve_matrix()

    return {
        "free_tier": {"name": "普通用户", "matrix": free_matrix},
        "member_tier": {"name": "会员用户", "matrix": free_matrix},
        "is_member": membership is not None and membership.is_active and not membership.is_expired,
        "current_plan": {
            "id": str(membership.plan_id) if membership else None,
            "name": membership.plan.name if membership else None,
            "end_at": membership.end_at if membership else None,
        },
        "recommended_plan": {
            "id": str(recommended.id) if recommended else None,
            "name": recommended.name if recommended else None,
            "grant_coins": recommended.grant_coins if recommended else 0,
            "matrix": plan_feature_matrix(recommended) if recommended else [],
            "items": (recommended.features or {}).get("items", []) if recommended else [],
        },
        "plans": [
            {
                "id": str(p.id),
                "name": p.name,
                "price": str(p.price),
                "grant_coins": p.grant_coins,
                "is_recommended": p.is_recommended,
                "matrix": plan_feature_matrix(p),
                "items": (p.features or {}).get("items", []),
            }
            for p in plans
        ],
    }

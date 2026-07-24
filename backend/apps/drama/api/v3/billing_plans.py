# -*- coding: utf-8 -*-
"""V3 套餐只读静态壳（对齐 W6 设计文案，无支付/无配额）。"""
from __future__ import annotations

BILLING_PLANS = [
    {
        "id": "basic",
        "name": "基础版",
        "price_label": "¥99/月",
        "features": [
            "每月 3 项目",
            "每项目最多 30 集",
            "基础评分/合规",
            "标准导出",
            "不含分镜/宣发/API",
        ],
    },
    {
        "id": "pro",
        "name": "专业版",
        "price_label": "¥299/月",
        "features": [
            "每月 10 项目",
            "最多 100 集",
            "十维评分",
            "合规+修复",
            "分批+质检闭环",
            "分镜+宣发",
            "不含团队协作",
        ],
    },
    {
        "id": "team",
        "name": "团队版",
        "price_label": "¥999/月",
        "features": [
            "不限项目/集数",
            "自定义权重",
            "企业合规库",
            "5 席位协作",
            "完整交付包",
            "API",
            "客成支持",
        ],
    },
]

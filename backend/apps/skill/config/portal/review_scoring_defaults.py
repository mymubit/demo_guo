# -*- coding: utf-8 -*-
"""质量审查评分 SSOT 默认值。"""

DEFAULT_REVIEW_WEIGHTS = {
    "format": 20,
    "rhythm": 40,
    "content": 20,
    "production": 20,
}

DEFAULT_GRADE_THRESHOLDS = {
    "S": 90,
    "A": 80,
    "B": 70,
    "C": 60,
    "D": 0,
}

DEFAULT_PASS_THRESHOLD = 70
DEFAULT_MIN_SUB_ITEM_SCORE = 75
DEFAULT_RELEASE_PASS_SCORE = 85

# 运营预设 — 与 C 端「剧本评估」同一套评分逻辑，仅调整严格度
REVIEW_SCORING_PRESETS = {
    "standard": {
        "label": "标准（推荐）",
        "description": "默认策略：通过线 70 分，节奏权重 40%，与当前剧本评估一致。",
        "pass_threshold": DEFAULT_PASS_THRESHOLD,
        "weights": dict(DEFAULT_REVIEW_WEIGHTS),
        "grade_thresholds": dict(DEFAULT_GRADE_THRESHOLDS),
    },
    "strict": {
        "label": "严格",
        "description": "平台精品筛选：通过线 75 分，提高 S/A 门槛，内容权重略升。",
        "pass_threshold": 75,
        "weights": {"format": 20, "rhythm": 35, "content": 25, "production": 20},
        "grade_thresholds": {"S": 92, "A": 85, "B": 75, "C": 65, "D": 0},
    },
    "relaxed": {
        "label": "宽松",
        "description": "内测 / 鼓励完稿：通过线 60 分，等级线整体下调。",
        "pass_threshold": 60,
        "weights": {"format": 15, "rhythm": 35, "content": 25, "production": 25},
        "grade_thresholds": {"S": 88, "A": 78, "B": 65, "C": 55, "D": 0},
    },
    "rhythm_first": {
        "label": "节奏优先",
        "description": "短剧流量导向：节奏权重 50%，适合强钩子、快节奏题材。",
        "pass_threshold": 70,
        "weights": {"format": 15, "rhythm": 50, "content": 15, "production": 20},
        "grade_thresholds": dict(DEFAULT_GRADE_THRESHOLDS),
    },
}


def list_review_scoring_presets():
    return [
        {
            "id": preset_id,
            "label": preset["label"],
            "description": preset["description"],
            "pass_threshold": preset["pass_threshold"],
            "weights": preset["weights"],
            "grade_thresholds": preset["grade_thresholds"],
        }
        for preset_id, preset in REVIEW_SCORING_PRESETS.items()
    ]


def expand_review_scoring_preset(preset_id: str) -> dict:
    preset = REVIEW_SCORING_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"未知预设: {preset_id}")
    return {
        "pass_threshold": preset["pass_threshold"],
        "weights": dict(preset["weights"]),
        "grade_thresholds": dict(preset["grade_thresholds"]),
    }


def detect_review_scoring_preset(cfg: dict) -> str:
    for preset_id, preset in REVIEW_SCORING_PRESETS.items():
        if (
            int(cfg.get("pass_threshold", -1)) == preset["pass_threshold"]
            and dict(cfg.get("weights") or {}) == preset["weights"]
            and dict(cfg.get("grade_thresholds") or {}) == preset["grade_thresholds"]
        ):
            return preset_id
    return "custom"

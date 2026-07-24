# -*- coding: utf-8 -*-
"""从技能仓 synthesize_matrix_params 合成 rule_params（SSOT 复用）。"""
from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings


@lru_cache(maxsize=1)
def _load_synthesize_module() -> Any:
    root = Path(settings.DRAMA_SKILLS_ROOT)
    path = root / "tools" / "optimizers" / "synthesize_matrix_params.py"
    if not path.is_file():
        raise FileNotFoundError(f"找不到矩阵合成脚本: {path}")
    spec = importlib.util.spec_from_file_location("drama_synthesize_matrix_params", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载矩阵合成脚本: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthesize_rule_params(genre_matrix: dict[str, Any]) -> dict[str, Any]:
    """返回含 matrix_key / reversal_density / emotion_curve / act_ratio / hook_types。"""
    module = _load_synthesize_module()
    return module.synthesize_rule_params(genre_matrix)

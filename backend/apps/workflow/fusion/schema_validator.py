# -*- coding: utf-8 -*-
"""JSON Schema 校验 — 运行时只读 FusionJsonSchema（DB SSOT）。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Tuple

from .config_loader import FusionSkillConfig, get_fusion_config

logger = logging.getLogger(__name__)

try:
    import jsonschema
    from jsonschema import Draft7Validator

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    Draft7Validator = None  # type: ignore


def validate_against_schema(
    payload: dict,
    schema_file: str,
    *,
    config: FusionSkillConfig | None = None,
) -> Tuple[bool, List[str]]:
    if not HAS_JSONSCHEMA:
        logger.warning("未安装 jsonschema，跳过 Schema 校验")
        return True, []

    from apps.workflow.pipeline_store import FusionPipelineDbService

    rel = schema_file.replace("schemas/", "")
    schema_dict = None
    if FusionPipelineDbService.should_use_db():
        schema_dict = FusionPipelineDbService.get_schema_dict(rel)

    if schema_dict is None:
        return False, [f"Schema 不存在（DB）：{rel}"]

    validator = Draft7Validator(schema_dict)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    messages = [f"{'.'.join(str(p) for p in err.path) or '$'}: {err.message}" for err in errors]
    return len(messages) == 0, messages[:20]

# -*- coding: utf-8 -*-
"""参考库 JSON — DB-only SSOT."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from apps.skill.models import ReferenceLibraryConfig

logger = logging.getLogger(__name__)

CONFIG_KEY = "default"

REFERENCE_FILES: tuple[str, ...] = (
    "industry-benchmarks.json",
    "character-archetypes.json",
    "hook-types-library.json",
    "reversal-patterns-library.json",
    "douyin-formula-library.json",
    "theme-templates.json",
)


class ReferenceLibraryService:
    @staticmethod
    def _get_row() -> ReferenceLibraryConfig:
        try:
            row, _ = ReferenceLibraryConfig.objects.get_or_create(
                config_key=CONFIG_KEY,
                defaults={"content": {}},
            )
            return row
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == "DatabaseOperationForbidden":
                raise
            raise

    @classmethod
    def clear_cache(cls) -> None:
        cls.get_json.cache_clear()

    @classmethod
    @lru_cache(maxsize=32)
    def get_json(cls, filename: str) -> dict:
        name = (filename or "").strip()
        if not name:
            return {}
        try:
            row = cls._get_row()
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == "DatabaseOperationForbidden":
                return {}
            raise
        try:
            content = row.content if isinstance(row.content, dict) else {}
            data = content.get(name)
            return data if isinstance(data, dict) else {}
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ != "DatabaseOperationForbidden":
                logger.debug("reference library DB 读取失败 %s: %s", name, exc)
            return {}

    @classmethod
    def list_filenames(cls) -> List[str]:
        try:
            row = cls._get_row()
            content = row.content if isinstance(row.content, dict) else {}
            return sorted(content.keys())
        except Exception:  # noqa: BLE001
            return []

    @classmethod
    def ensure_defaults(cls) -> bool:
        """Runtime never imports external files; reads DB only."""
        return False

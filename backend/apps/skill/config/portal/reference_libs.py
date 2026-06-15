# -*- coding: utf-8 -*-
"""参考库 JSON — DB SSOT；磁盘 references/ 仅 import/sync。"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    def _disk_refs_dir(cls) -> Optional[Path]:
        try:
            from apps.workflow.fusion.config_loader import get_fusion_config

            return get_fusion_config().root / "references"
        except Exception:  # noqa: BLE001
            return None

    @classmethod
    def _read_disk_file(cls, filename: str) -> Optional[dict]:
        refs_dir = cls._disk_refs_dir()
        if refs_dir is None:
            return None
        path = refs_dir / filename
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取磁盘参考库失败 %s: %s", filename, exc)
            return None

    @classmethod
    def import_from_disk(cls, *, overwrite: bool = False) -> int:
        """从磁盘 references/ 导入全部参考 JSON 到 DB。"""
        row = cls._get_row()
        content = dict(row.content) if isinstance(row.content, dict) else {}
        imported = 0
        for filename in REFERENCE_FILES:
            if not overwrite and filename in content:
                continue
            data = cls._read_disk_file(filename)
            if data is None:
                continue
            content[filename] = data
            imported += 1
        if imported:
            row.content = content
            row.save(update_fields=["content", "updated_at"])
            cls.clear_cache()
        logger.info("[ReferenceLibrary] import_from_disk imported=%s total=%s", imported, len(content))
        return imported

    @classmethod
    def ensure_defaults(cls) -> bool:
        """DB 无内容时从磁盘 seed。"""
        try:
            row = cls._get_row()
            if isinstance(row.content, dict) and row.content:
                return False
        except Exception:  # noqa: BLE001
            return False
        return cls.import_from_disk(overwrite=False) > 0

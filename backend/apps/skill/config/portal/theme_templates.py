# -*- coding: utf-8 -*-
"""题材模板富字段 — DB SSOT（ThemeTemplate.params）；磁盘仅 import。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_THEME_CODE_ALIASES: Dict[str, str] = {
    "domineering-ceo": "overbearing-ceo",
    "overbearing-ceo": "domineering-ceo",
    "mystery-reversal": "suspense",
    "suspense": "mystery-reversal",
}

# DB/磁盘不可用时，保证 C 端可读字段与题材推荐仍可工作
_THEME_RICH_FIELDS: Dict[str, Dict[str, Any]] = {
    "sweet-pet": {
        "coreConflictFormula": "傲娇男主与元气女主甜蜜推拉，虐点与甜点交替",
        "audienceFit": "18-35 岁女性向短视频受众",
        "keyReversalTypes": ["误会解开", "吃醋反转", "告白时刻"],
        "emotionalPeakMoments": ["甜蜜暴击", "告白瞬间"],
        "sampleCoreHooks": ["冷酷总裁爱上倔强灰姑娘"],
    },
    "family-revenge": {
        "coreConflictFormula": "婆媳矛盾与家庭压迫下的隐忍复仇",
        "audienceFit": "家庭伦理向，强情绪共鸣",
        "keyReversalTypes": ["隐忍爆发", "身份反转", "真相揭露"],
        "emotionalPeakMoments": ["当众打脸", "真相揭晓"],
        "sampleCoreHooks": ["婆婆刁难儿媳，女主觉醒复仇打脸"],
    },
}


class ThemeTemplateCatalogService:
    @classmethod
    def clear_cache(cls) -> None:
        cls.get_templates_map.cache_clear()

    @classmethod
    def _builtin_templates_map(cls) -> Dict[str, Dict[str, Any]]:
        from apps.skill.config.portal.skill_settings import ThemeTemplateService

        out: Dict[str, Dict[str, Any]] = {}
        for row in ThemeTemplateService.BUILTIN_THEMES:
            code = (row.get("theme_code") or "").strip()
            if not code:
                continue
            params = dict(row.get("params") or {})
            rich = dict(_THEME_RICH_FIELDS.get(code) or {})
            out[code] = {
                "displayName": row.get("theme_name") or code,
                **params,
                **rich,
            }
        return out

    @classmethod
    def _load_disk_templates(cls) -> Dict[str, Dict[str, Any]]:
        from apps.skill.config.portal.reference_libs import ReferenceLibraryService

        raw = ReferenceLibraryService.get_json("theme-templates.json")
        if not raw:
            raw = ReferenceLibraryService._read_disk_file("theme-templates.json") or {}
        templates = raw.get("themeTemplates") if isinstance(raw, dict) else None
        if not isinstance(templates, dict):
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for code, entry in templates.items():
            if not isinstance(entry, dict):
                continue
            rich = dict(_THEME_RICH_FIELDS.get(code) or {})
            merged = {**rich, **entry}
            out[code] = {
                "displayName": merged.get("displayName") or code,
                **merged,
            }
        return out

    @classmethod
    @lru_cache(maxsize=1)
    def get_templates_map(cls) -> Dict[str, Dict[str, Any]]:
        from apps.skill.config.portal.skill_settings import ThemeTemplateService

        out: Dict[str, Dict[str, Any]] = {}
        try:
            rows = ThemeTemplateService.list_themes(only_active=False)
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ != "DatabaseOperationForbidden":
                logger.debug("ThemeTemplate DB 读取失败: %s", exc)
            rows = []
        for row in rows:
            code = (row.get("theme_code") or "").strip()
            if not code:
                continue
            params = row.get("params") if isinstance(row.get("params"), dict) else {}
            rich = dict(_THEME_RICH_FIELDS.get(code) or {})
            out[code] = {
                "displayName": row.get("theme_name") or code,
                **rich,
                **params,
            }
        if not out:
            out = cls._load_disk_templates()
        if not out:
            out = cls._builtin_templates_map()
        return out

    @classmethod
    def get_theme_entry(cls, theme: str) -> Optional[Dict[str, Any]]:
        key = (theme or "").strip()
        if not key:
            return None
        templates = cls.get_templates_map()
        entry = templates.get(key)
        if entry:
            return entry
        alias = _THEME_CODE_ALIASES.get(key)
        if alias:
            return templates.get(alias)
        return None

    @classmethod
    def import_from_disk(cls, *, merge: bool = True) -> int:
        """将 theme-templates.json 合并进 ThemeTemplate.params。"""
        from apps.skill.config.portal.reference_libs import ReferenceLibraryService
        from apps.skill.config.portal.skill_settings import ThemeTemplateService

        raw = ReferenceLibraryService.get_json("theme-templates.json")
        if not raw:
            data = ReferenceLibraryService._read_disk_file("theme-templates.json")
            raw = data or {}
        templates = raw.get("themeTemplates") if isinstance(raw, dict) else None
        if not isinstance(templates, dict):
            return 0

        imported = 0
        for code, entry in templates.items():
            if not isinstance(entry, dict):
                continue
            existing = ThemeTemplateService.get_theme(code)
            params = dict(existing.get("params") or {}) if existing else {}
            display_name = str(entry.get("displayName") or code).strip()
            new_params = {k: v for k, v in entry.items() if k != "displayName"}
            if merge and params:
                params.update(new_params)
            else:
                params = new_params
            ThemeTemplateService.create_or_update(
                {
                    "theme_code": code,
                    "theme_name": display_name,
                    "params": params,
                    "is_active": existing.get("is_active", True) if existing else True,
                    "sort_order": existing.get("sort_order", 0) if existing else 0,
                }
            )
            imported += 1
        cls.clear_cache()
        logger.info("[ThemeTemplateCatalog] import_from_disk themes=%s", imported)
        return imported

    @classmethod
    def ensure_defaults(cls) -> bool:
        """params 缺少 coreConflictFormula 时从磁盘 import。"""
        templates = cls.get_templates_map()
        needs_import = not templates or not any(
            isinstance(v, dict) and v.get("coreConflictFormula") for v in templates.values()
        )
        if not needs_import:
            return False
        return cls.import_from_disk(merge=True) > 0

# -*- coding: utf-8 -*-
"""Admin config center APIs."""
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.pagination import StandardPagination
from apps.console.responses import (
    CACHE_KEY_DASHBOARD,
    CACHE_KEY_DASHBOARD_LEGACY,
    CACHE_KEY_STATS,
    CACHE_KEY_SKILL_CONFIG_PREFIX,
    CACHE_TTL,
    DEFAULT_CONFIG_KEYS,
    api_fail,
    _is_sensitive_key,
    api_ok,
    _random_password)

from apps.skill.models import HookLibrary, SkillConfig, ThemeTemplate
from apps.console.serializers import (
    HookSerializer,
    SkillConfigSerializer,
    SkillConfigUpdateSerializer,
    ThemeTemplateSerializer,
)


# ============================================================
# 鎶€鑳介厤缃鐞嗭紙瀵规帴 apps.skill.models.SkillConfig锛?
# ============================================================

class SkillConfigView(APIView):
    """Skill config management."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_default_configs(self):
        """Return default skill config keys."""
        return set(DEFAULT_CONFIG_KEYS)

    def get(self, request, key=None):
        # 鍗曟潯鏌ヨ
        if key:
            obj = SkillConfig.objects.filter(config_key=key).first()
            if obj is None:
                return api_fail(f"config key {key} not found")
            plain = obj.get_decrypted_value() or ""
            # 鍗曟潯鏌ヨ涓嶅仛鑴辨晱锛屼繚璇佺鐞嗗憳鑳界湅鍒板畬鏁存槑鏂囷紙鍓嶇鍙寜闇€鑷閬洊锛?
            data = {
                "key": obj.config_key,
                "value": plain,
                "description": obj.description or "",
                "updated_at": obj.updated_at,
            }
            serializer = SkillConfigSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return api_ok(serializer.validated_data)

        # 鍒楄〃鏌ヨ锛欴B 璁板綍 + 榛樿鍒楄〃涓皻鏈惤搴撶殑 key锛屽悎骞跺悗缁熶竴杩斿洖
        db_map = {}
        for sc in SkillConfig.objects.all():
            plain = sc.get_decrypted_value() or ""
            db_map[sc.config_key] = {
                "key": sc.config_key,
                "value": plain,
                "description": sc.description or "",
                "updated_at": sc.updated_at,
            }

        all_keys = set(db_map.keys()) | self._get_default_configs()
        items = []
        for k in sorted(all_keys):
            base = db_map.get(k, {
                "key": k,
                "value": "",
                "description": "",
                "updated_at": None,
            })
            # 鏁忔劅椤癸細鍒楄〃鏄剧ず鏃堕伄鐩栦负 ******
            display_value = "******" if _is_sensitive_key(k) else base.get("value", "")
            items.append({
                "key": base["key"],
                "value": display_value,
                "description": base.get("description", ""),
                "updated_at": base.get("updated_at"),
            })

        serializer = SkillConfigSerializer(items, many=True)
        return api_ok(serializer.data)

    def put(self, request, key=None):
        if not key:
            return api_fail("璇峰湪 URL 涓彁渚涢厤缃?key")
        input_ser = SkillConfigUpdateSerializer(data=request.data or {})
        input_ser.is_valid(raise_exception=True)
        new_value = input_ser.validated_data.get("value", "")
        new_description = input_ser.validated_data.get("description", "")

        # 閫氳繃 SkillConfig.set_encrypted_value 鍔犲瘑瀛樺偍锛堜笌 skill 妯″潡鍔犲瘑瀹炵幇涓€鑷达級
        obj, created = SkillConfig.objects.update_or_create(
            config_key=key,
            defaults={
                "description": new_description or key,
            },
        )
        obj.set_encrypted_value(str(new_value))
        obj.save()

        # 娓呴櫎 skill 妯″潡鐩稿叧鐨勭紦瀛樺墠缂€锛岃涓嬫父璇诲彇鐢熸晥
        try:
            cache.delete_pattern("skill:config:*")
        except Exception:
            pass
        cache.delete(CACHE_KEY_DASHBOARD)
        cache.delete(CACHE_KEY_STATS)

        data = {
            "key": obj.config_key,
            "value": new_value,
            "description": obj.description,
            "updated_at": obj.updated_at,
        }
        return api_ok(data, message="config updated")


class CreationFormCatalogView(APIView):
    """Portal creation form catalog."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        base = FusionSsotCatalog().public_catalog()
        overrides = get_creation_form_overrides()
        return api_ok(
            {
                "skillVersion": base.get("skillVersion"),
                "catalog": {
                    "budgetLevels": base.get("budgetLevels") or [],
                    "platforms": base.get("platforms") or [],
                    "creationEntries": base.get("creationEntries") or [],
                    "formatVariants": base.get("formatVariants") or [],
                    "episodeSettings": base.get("episodeSettings") or {},
                    "sections": base.get("sections") or {},
                    "themes": base.get("themes") or [],
                    "creationEntryProfiles": base.get("creationEntryProfiles") or {},
                },
                "overrides": overrides,
            }
        )

    def put(self, request):
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        payload = request.data or {}
        overrides = payload.get("overrides")
        if overrides is None:
            overrides = payload

        if not isinstance(overrides, dict):
            return api_fail("overrides 蹇呴』鏄?JSON 瀵硅薄")

        allowed_keys = {
            "budgetLevels",
            "platforms",
            "creationEntries",
            "formatVariants",
            "episodeSettings",
            "sections",
            "themes",
            "creationEntryProfiles",
        }
        cleaned = {k: v for k, v in overrides.items() if k in allowed_keys}
        if not cleaned and overrides:
            return api_fail(f"浠呭厑璁歌鐩栧瓧娈碉細{', '.join(sorted(allowed_keys))}")

        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        CreationFormOverrideService.save_overrides(cleaned)
        try:
            cache.delete_pattern("skill:config:*")
        except Exception:
            pass

        merged = get_creation_form_overrides()
        return api_ok({"overrides": merged}, message="creation form config saved")


class CreationFormImportView(APIView):
    """Disk import endpoint removed."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        base = FusionSsotCatalog().public_catalog()
        return api_ok(
            {
                "skillVersion": base.get("skillVersion"),
                "catalog": {
                    "creationEntryProfiles": base.get("creationEntryProfiles") or {},
                },
                "overrides": get_creation_form_overrides(),
                "externalDiskImport": "removed",
                "migrationCommand": "python manage.py import_agent_assets --inventory external_asset_inventory.json --commit",
            },
            message="Disk catalog sync has been removed.",
        )


# ============================================================
# 棰樻潗妯℃澘绠＄悊锛堝鎺?apps.skill.models.ThemeTemplate锛?
# ============================================================

class ThemeTemplateView(APIView):
    """Theme template list/create."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = ThemeTemplate.objects.all().order_by("sort_order", "-created_at")
        items = []
        for t in qs:
            # 瀛楁鏄犲皠锛氬皢 ThemeTemplate 琛ㄥ瓧娈垫槧灏勪负鍓嶇鏈熸湜鐨勫瓧娈?
            prompt = ""
            try:
                params = t.params or {}
                hook_types = params.get("hook_types") if isinstance(params, dict) else []
                if hook_types and isinstance(hook_types, list):
                    prompt = ",".join(str(x) for x in hook_types)
            except Exception:
                prompt = ""

            items.append({
                "id": str(t.id),
                "name": t.theme_name or "",
                "category": t.theme_code or "",
                "prompt_template": prompt,
                "is_active": bool(t.is_active),
                "sort_order": int(t.sort_order or 0),
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })
        serializer = ThemeTemplateSerializer(items, many=True)
        return api_ok(serializer.data)

    def post(self, request):
        serializer = ThemeTemplateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        theme_code = v.get("category") or f"custom-{secrets.token_hex(6)}"
        theme_name = v.get("name")
        if not theme_name:
            return api_fail("棰樻潗鍚嶇О涓嶈兘涓虹┖")

        obj = ThemeTemplate.objects.create(
            theme_code=theme_code,
            theme_name=theme_name,
            is_active=bool(v.get("is_active", True)),
            sort_order=int(v.get("sort_order", 0) or 0),
            description="",
        )
        cache.delete(CACHE_KEY_DASHBOARD)

        data = {
            "id": str(obj.id),
            "name": obj.theme_name,
            "category": obj.theme_code,
            "prompt_template": "",
            "is_active": bool(obj.is_active),
            "sort_order": obj.sort_order,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return api_ok(data, message="theme created", http_status=status.HTTP_201_CREATED)


class ThemeTemplateDetailView(APIView):
    """Theme template update."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, theme_id=None):
        try:
            obj = ThemeTemplate.objects.get(pk=theme_id)
        except ThemeTemplate.DoesNotExist:
            return api_fail("theme not found")

        serializer = ThemeTemplateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        obj.theme_name = v.get("name", obj.theme_name)
        obj.theme_code = v.get("category", obj.theme_code)
        obj.is_active = bool(v.get("is_active", obj.is_active))
        obj.sort_order = int(v.get("sort_order", obj.sort_order) or 0)
        obj.save()

        data = {
            "id": str(obj.id),
            "name": obj.theme_name,
            "category": obj.theme_code,
            "prompt_template": "",
            "is_active": bool(obj.is_active),
            "sort_order": obj.sort_order,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return api_ok(data, message="theme updated")


# ============================================================
# 閽╁瓙搴撶鐞嗭紙瀵规帴 apps.skill.models.HookLibrary锛?
# ============================================================

class HookView(APIView):
    """Hook library list/create."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = HookLibrary.objects.all().order_by("-use_count", "-created_at")
        items = []
        for h in qs:
            snippet = (h.content or "")[:20]
            items.append({
                "id": str(h.id),
                "name": snippet + ("..." if len(h.content or "") > 20 else ""),
                "hook_type": h.hook_type or "opening",
                "content": h.content or "",
                "is_active": bool(h.is_active),
                "use_count": h.use_count,
                "created_at": h.created_at,
            })
        serializer = HookSerializer(items, many=True)
        return api_ok(serializer.data)

    def post(self, request):
        serializer = HookSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        content = v.get("content")
        if not content:
            return api_fail("hook content cannot be empty")

        obj = HookLibrary.objects.create(
            hook_type=v.get("hook_type", "opening"),
            content=content,
            tags="",
            is_active=bool(v.get("is_active", True)),
        )

        snippet = (obj.content or "")[:20]
        data = {
            "id": str(obj.id),
            "name": snippet + ("..." if len(obj.content or "") > 20 else ""),
            "hook_type": obj.hook_type,
            "content": obj.content,
            "is_active": bool(obj.is_active),
            "created_at": obj.created_at,
        }
        return api_ok(data, message="hook created", http_status=status.HTTP_201_CREATED)


class HookDetailView(APIView):
    """Hook library update/delete."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, hook_id=None):
        try:
            obj = HookLibrary.objects.get(pk=hook_id)
        except HookLibrary.DoesNotExist:
            return api_fail("hook not found")

        serializer = HookSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        if v.get("content"):
            obj.content = v["content"]
        if v.get("hook_type"):
            obj.hook_type = v["hook_type"]
        if "is_active" in v:
            obj.is_active = bool(v["is_active"])
        obj.save()

        snippet = (obj.content or "")[:20]
        data = {
            "id": str(obj.id),
            "name": snippet + ("..." if len(obj.content or "") > 20 else ""),
            "hook_type": obj.hook_type,
            "content": obj.content,
            "is_active": bool(obj.is_active),
            "use_count": obj.use_count,
            "created_at": obj.created_at,
        }
        return api_ok(data, message="hook updated")

    def delete(self, request, hook_id=None):
        try:
            obj = HookLibrary.objects.get(pk=hook_id)
        except HookLibrary.DoesNotExist:
            return api_fail("hook not found")
        obj.delete()
        return api_ok(None, message="hook deleted")

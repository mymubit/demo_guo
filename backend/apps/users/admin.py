"""
Django 后台管理配置

注意：
- 为了保护用户隐私，后台列表只展示 phone_hash / email_hash，
  不展示明文手机号/邮箱。
- 只有超级用户能访问 User 管理。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile


# ============================================================
# UserProfile 内联
# ============================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "用户资料"
    verbose_name_plural = verbose_name
    fields = ("nickname", "avatar_url", "gender", "bio")


# ============================================================
# User 管理
# ============================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户后台管理"""
    fieldsets = (
        ("基本信息", {"fields": ("id", "phone", "email", "password")}),
        ("哈希索引（只读）", {"fields": ("phone_hash", "email_hash")}),
        ("展示信息", {"fields": ("nickname", "avatar_url")}),
        ("权限与状态", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("时间信息", {"fields": ("created_at", "last_login")}),
    )
    add_fieldsets = (
        ("新增用户", {
            "classes": ("wide",),
            "fields": ("phone", "password1", "password2", "nickname"),
        }),
    )
    list_display = (
        "id_hex",
        "nickname",
        "phone_hash",
        "email_hash",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
        "last_login",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "created_at")
    search_fields = ("nickname", "phone_hash", "email_hash")
    readonly_fields = ("id", "phone_hash", "email_hash", "created_at", "last_login")
    ordering = ("-created_at",)
    inlines = (UserProfileInline,)

    def id_hex(self, obj):
        return obj.id.hex[:12] if obj.id else "-"
    id_hex.short_description = "用户ID"


# ============================================================
# UserProfile 管理（独立）
# ============================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料独立管理"""
    list_display = ("user_id_hex", "nickname", "gender", "updated_at")
    list_filter = ("gender", "updated_at")
    search_fields = ("nickname", "user__nickname")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("id", "user", "nickname", "avatar_url")}),
        ("资料", {"fields": ("gender", "bio")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )
    raw_id_fields = ("user",)

    def user_id_hex(self, obj):
        return obj.user.id.hex[:12] if obj.user_id else "-"
    user_id_hex.short_description = "所属用户ID"

"""
会员模块 Django Admin
"""
from django.contrib import admin

from .models import MembershipPlan, UserMembership, PromoCode


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "validity_days",
        "creation_quota",
        "is_recommended",
        "is_active",
        "sort_order",
        "created_at",
    )
    list_filter = ("is_active", "is_recommended")
    search_fields = ("name",)
    ordering = ("sort_order", "-created_at")
    readonly_fields = ("created_at",)


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "start_at",
        "end_at",
        "remaining_creations",
        "is_active",
    )
    list_filter = ("is_active", "plan")
    search_fields = ("user__username", "user__phone")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    raw_id_fields = ("plan",)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "plan",
        "max_uses",
        "used_count",
        "expires_at",
        "is_active",
        "is_expired",
    )
    list_filter = ("is_active", "plan")
    search_fields = ("code",)
    readonly_fields = ("created_at",)
    raw_id_fields = ("plan",)

    def is_expired(self, obj) -> bool:
        return obj.is_expired

    is_expired.boolean = True

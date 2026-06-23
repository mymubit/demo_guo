# -*- coding: utf-8 -*-
"""
订单模块 Django Admin
"""
from django.contrib import admin

from .models import Order, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    fields = ("transaction_id", "amount", "status", "paid_at")
    readonly_fields = ("transaction_id", "created_at")
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_no",
        "user",
        "membership_plan",
        "amount",
        "status",
        "payment_method",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("order_no", "user__username", "user__phone")
    readonly_fields = ("order_no", "created_at")
    autocomplete_fields = ("user",)
    raw_id_fields = ("membership_plan",)
    inlines = [PaymentInline]

    def has_add_permission(self, request):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "order",
        "amount",
        "status",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("transaction_id", "order__order_no")
    readonly_fields = ("transaction_id", "created_at")
    raw_id_fields = ("order",)

    def has_add_permission(self, request):
        return False

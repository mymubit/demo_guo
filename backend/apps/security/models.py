"""
安全模块数据模型

包含审计日志模型，用于记录系统关键操作，支持安全审计和合规追溯。
"""
import uuid

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.utils.translation import gettext_lazy as _


class AuditLogQuerySet(models.QuerySet):
    """
    审计日志查询集

    禁用 update 和 delete 操作，确保日志记录不可修改/删除。
    """

    def update(self, **kwargs):
        raise RuntimeError("审计日志记录不允许修改")

    def delete(self):
        raise RuntimeError("审计日志记录不允许删除")

    def _delete(self):
        raise RuntimeError("审计日志记录不允许删除")


class AuditLogManager(models.Manager.from_queryset(AuditLogQuerySet)):
    """
    审计日志管理器

    覆盖 QuerySet 的 update/delete，确保日志只读。
    """

    def get_queryset(self):
        return super().get_queryset()


class AuditLog(models.Model):
    """
    系统审计日志模型

    记录用户和系统的关键操作行为，支持安全审计与追溯分析。
    模型实例一旦创建，不允许修改或删除，只能插入新记录。
    """

    class ActionType(models.TextChoices):
        """
        操作类型枚举
        """
        LOGIN = "login", _("用户登录")
        LOGOUT = "logout", _("用户登出")
        REGISTER = "register", _("用户注册")
        CREATE = "create", _("创建资源")
        READ = "read", _("读取资源")
        UPDATE = "update", _("更新资源")
        DELETE = "delete", _("删除资源")
        DOWNLOAD = "download", _("下载资源")
        EXPORT = "export", _("导出资源")
        PAYMENT = "payment", _("支付操作")
        ADMIN = "admin", _("后台管理")
        API_CALL = "api_call", _("API 调用")
        SIGNATURE_FAIL = "signature_fail", _("签名验证失败")
        RATE_LIMIT = "rate_limit", _("触发限流")
        PERMISSION_DENY = "permission_deny", _("权限拒绝")
        DATA_LEAK = "data_leak", _("疑似数据泄露")
        OTHER = "other", _("其他操作")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("日志ID"),
        help_text=_("全局唯一的日志记录ID"),
    )

    user_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("用户ID"),
        help_text=_("关联用户ID，未登录用户为空"),
    )

    action = models.CharField(
        max_length=32,
        choices=ActionType.choices,
        default=ActionType.API_CALL,
        db_index=True,
        verbose_name=_("操作类型"),
        help_text=_("本次请求/操作的类型枚举"),
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("客户端IP"),
        help_text=_("请求来源IP地址"),
    )

    device_fingerprint = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("设备指纹"),
        help_text=_("客户端设备指纹，用于设备识别与反作弊"),
    )

    request_path = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("请求路径"),
        help_text=_("HTTP 请求路径 (PATH_INFO)"),
    )

    request_method = models.CharField(
        max_length=10,
        db_index=True,
        verbose_name=_("请求方法"),
        help_text=_("HTTP 请求方法，如 GET / POST / PUT / DELETE"),
    )

    request_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_("请求体Hash"),
        help_text=_("请求体 SHA-256 哈希值，便于追溯请求内容"),
    )

    response_status = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("响应状态码"),
        help_text=_("HTTP 响应状态码"),
    )

    extra_info = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        verbose_name=_("扩展信息"),
        help_text=_("额外的上下文信息，存储为 JSON"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_("创建时间"),
        help_text=_("日志记录时间"),
    )

    objects = AuditLogManager()

    class Meta:
        app_label = "security"
        db_table = "sf_audit_log"
        verbose_name = _("审计日志")
        verbose_name_plural = _("审计日志")
        ordering = ["-created_at"]
        # 不允许修改/删除，仅 INSERT
        default_permissions = ("view",)
        indexes = [
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["ip_address", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["response_status", "-created_at"]),
            models.Index(fields=["device_fingerprint", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.action} - {self.ip_address}"

    # ---- 禁用修改/删除 ----
    def save(self, *args, **kwargs):
        # 如果是已存在对象（有 pk 且非新创建），禁止保存
        if self.pk is not None and not self._state.adding:
            raise RuntimeError("审计日志记录不允许修改")
        # 仅允许 INSERT（新增）
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("审计日志记录不允许删除")

    def full_clean(self, *args, **kwargs):
        """
        仅允许新记录做字段校验。
        """
        if self.pk is not None and not self._state.adding:
            raise RuntimeError("审计日志记录不允许修改")
        return super().full_clean(*args, **kwargs)

    @classmethod
    def log(
        cls,
        action: str,
        request=None,
        user=None,
        response=None,
        request_hash: str | None = None,
        extra_info: dict | None = None,
    ) -> "AuditLog":
        """
        便捷方法：基于 Django HttpRequest 对象创建审计日志。

        :param action: 操作类型（ActionType 枚举值）
        :param request: Django HttpRequest 对象
        :param user: 用户对象或 None
        :param response: HttpResponse 对象或 None
        :param request_hash: 请求体哈希值
        :param extra_info: 额外的上下文信息
        :return: 已保存的 AuditLog 实例
        """
        ip = None
        device_fp = None
        path = ""
        method = ""

        if request is not None:
            ip = cls._get_client_ip(request)
            device_fp = request.META.get("HTTP_X_DEVICE_FINGERPRINT", "") or None
            path = request.path or ""
            method = request.method or ""

        user_id = None
        if user is not None and hasattr(user, "id"):
            user_id = user.id
        elif request is not None and hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.id

        response_status = None
        if response is not None and hasattr(response, "status_code"):
            response_status = response.status_code

        return cls.objects.create(
            action=action,
            user_id=user_id,
            ip_address=ip,
            device_fingerprint=device_fp,
            request_path=path[:512],
            request_method=method[:10],
            request_hash=request_hash,
            response_status=response_status,
            extra_info=extra_info or {},
        )

    @staticmethod
    def _get_client_ip(request) -> str | None:
        """
        从请求中提取客户端真实 IP。

        优先使用 X-Forwarded-For 头（代理场景），其次使用 REMOTE_ADDR。
        """
        if request is None:
            return None
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if x_forwarded_for:
            # X-Forwarded-For 可能是多个 IP 逗号分隔，取第一个
            ip = x_forwarded_for.split(",")[0].strip()
            if ip:
                return ip
        return request.META.get("REMOTE_ADDR") or None


# ---- 使用 pre_save 信号进一步防止意外修改 ----
def _audit_log_pre_save(sender, instance, **kwargs):
    """
    确保所有保存操作都是 INSERT。
    """
    if instance.pk is not None and not instance._state.adding:
        raise RuntimeError("审计日志记录不允许修改")


signals.pre_save.connect(_audit_log_pre_save, sender=AuditLog)


def _audit_log_pre_delete(sender, instance, **kwargs):
    """
    阻止任何删除审计日志的行为。
    """
    raise RuntimeError("审计日志记录不允许删除")


signals.pre_delete.connect(_audit_log_pre_delete, sender=AuditLog)

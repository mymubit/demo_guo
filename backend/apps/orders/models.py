"""
订单与支付数据模型
"""
import uuid
import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.membership.models import MembershipPlan


def generate_order_no() -> str:
    """生成订单号：SF + 时间戳 + 6 位随机字符"""
    import time

    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    random_part = secrets.token_hex(3).upper()
    return f"SF{timestamp}{random_part}"


def generate_transaction_id() -> str:
    """生成模拟交易号：TX + 时间戳 + 8 位随机字符"""
    import time

    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    random_part = secrets.token_hex(4).upper()
    return f"TX{timestamp}{random_part}"


class Order(models.Model):
    """订单"""

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "待支付"),
        (STATUS_PAID, "已支付"),
        (STATUS_CANCELLED, "已取消"),
        (STATUS_REFUNDED, "已退款"),
    ]

    PAYMENT_METHOD_WECHAT = "wechat"
    PAYMENT_METHOD_ALIPAY = "alipay"
    PAYMENT_METHOD_MOCK = "mock"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_WECHAT, "微信支付"),
        (PAYMENT_METHOD_ALIPAY, "支付宝"),
        (PAYMENT_METHOD_MOCK, "模拟支付"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_no = models.CharField("订单号", max_length=64, unique=True, default=generate_order_no)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="用户",
    )
    membership_plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="会员套餐",
    )
    TYPE_MEMBERSHIP = "membership"
    TYPE_RECHARGE = "recharge"
    TYPE_CHOICES = [
        (TYPE_MEMBERSHIP, "会员购买"),
        (TYPE_RECHARGE, "充值创作币"),
    ]
    order_type = models.CharField(
        "订单类型",
        max_length=16,
        choices=TYPE_CHOICES,
        default=TYPE_MEMBERSHIP,
    )
    recharge_package = models.ForeignKey(
        "billing.RechargePackage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="充值档位",
    )
    coins_granted = models.PositiveIntegerField(
        "到账币数",
        default=0,
        help_text="充值订单支付成功后发放的创作币",
    )
    amount = models.DecimalField("订单金额", max_digits=10, decimal_places=2, default=Decimal("0"))
    status = models.CharField(
        "订单状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    payment_method = models.CharField(
        "支付方式",
        max_length=16,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_MOCK,
    )
    paid_at = models.DateTimeField("支付时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["order_no"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.order_no} - ¥{self.amount} ({self.get_status_display()})"

    @property
    def is_paid(self) -> bool:
        return self.status == self.STATUS_PAID


class Payment(models.Model):
    """支付记录"""

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "处理中"),
        (STATUS_SUCCESS, "支付成功"),
        (STATUS_FAILED, "支付失败"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(
        "交易号",
        max_length=128,
        unique=True,
        default=generate_transaction_id,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="所属订单",
    )
    amount = models.DecimalField("支付金额", max_digits=10, decimal_places=2)
    status = models.CharField(
        "支付状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    paid_at = models.DateTimeField("支付时间", null=True, blank=True)
    raw_response = models.JSONField("原始响应", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "支付记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.transaction_id} - ¥{self.amount}"


class MembershipGrant(models.Model):
    """会员订单权益发放记录，用于退款时精确回滚。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="membership_grant",
        verbose_name="订单",
    )
    user_membership = models.ForeignKey(
        "membership.UserMembership",
        on_delete=models.PROTECT,
        related_name="order_grants",
        verbose_name="会员记录",
    )
    grant_days = models.PositiveIntegerField("发放天数", default=0)
    grant_coins = models.PositiveIntegerField("赠送币数", default=0)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "会员权益发放记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_membership"]),
        ]

    def __str__(self):
        return f"{self.order.order_no} -> {self.user_membership_id}"

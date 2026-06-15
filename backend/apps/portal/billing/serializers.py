from rest_framework import serializers


class RechargeOrderCreateSerializer(serializers.Serializer):
    """充值订单创建输入。"""

    package_id = serializers.UUIDField()
    payment_method = serializers.CharField(required=False, allow_blank=True, max_length=16)

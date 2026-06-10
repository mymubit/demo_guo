"""
简化版 serializers
"""
from rest_framework import serializers


class UserRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(min_length=6, max_length=128)
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=64)


class UserLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=128)

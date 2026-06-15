"""
开发环境配置

继承 base.py，覆盖开发专用设置：
- DEBUG = True
- 允许所有来源跨域（方便本地前端联调）
- 关闭签名验证和限流（避免 HMR/轮询触发 429）
"""
import os

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# 开发环境允许所有跨域来源
CORS_ALLOW_ALL_ORIGINS = True

# 开发环境关闭请求签名验证，避免前端调试被 401 拦截
SECURITY_SIGNATURE_ENABLED = False

# 开发环境默认关闭限流，可通过环境变量临时开启
SECURITY_RATE_LIMIT_ENABLED = os.getenv("SECURITY_RATE_LIMIT_ENABLED", "false").lower() in (
    "1",
    "true",
    "yes",
)

# 仅本地开发允许模拟支付，便于联调会员/充值链路。
ALLOW_MOCK_PAYMENT = os.getenv("ALLOW_MOCK_PAYMENT", "true").lower() in (
    "1",
    "true",
    "yes",
)

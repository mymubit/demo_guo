# apps/common/utils.py
# 通用工具函数集合

import hashlib
import random
import secrets
import string
import time
import uuid

from django.utils import timezone


def generate_uuid() -> str:
    """生成标准 UUID4 字符串（无连字符，大写）。

    :return: 32 位十六进制字符串
    """
    return uuid.uuid4().hex.upper()


def generate_random_string(length: int = 16) -> str:
    """生成指定长度的随机字符串（包含大小写字母和数字）。

    使用 secrets 模块以获得加密安全的随机字符。

    :param length: 字符串长度，默认 16
    :return: 随机字符串
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_order_no(prefix: str = 'ORD') -> str:
    """生成订单号 / 流水号。

    规则：{prefix} + {YYYYMMDDHHmmss} + {6 位随机数字}
    例：ORD20260610120000123456

    :param prefix: 订单号前缀，默认为 ORD
    :return: 订单号字符串
    """
    now = timezone.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    # 生成 6 位随机数字（使用 random 以兼顾速度，订单号对随机性要求不严格）
    random_digits = ''.join(random.choices(string.digits, k=6))
    return f'{prefix}{timestamp}{random_digits}'


def format_datetime(dt) -> str:
    """格式化 datetime 为 'YYYY-MM-DD HH:mm:ss' 字符串。

    :param dt: datetime 对象（可为时区感知或无时区）
    :return: 格式化后的时间字符串；若输入为 None 则返回空字符串
    """
    if dt is None:
        return ''
    # 若为 timezone-aware 时间，转为本地时间后再格式化
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_client_ip(request) -> str:
    """从 Django/DRF 的 request 对象中获取客户端真实 IP。

    优先从 X-Forwarded-For 头读取（经过反向代理时的场景），
    其次检查 X-Real-IP，最后回退到 request.META['REMOTE_ADDR']。

    :param request: HttpRequest 对象
    :return: 客户端 IP 字符串
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For 可能包含多个 IP，以逗号分隔，第一个为客户端真实 IP
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('HTTP_X_REAL_IP', '')
        if not ip:
            ip = request.META.get('REMOTE_ADDR', '')
    return ip


def hash_string(s: str, algorithm: str = 'sha256') -> str:
    """对字符串进行哈希加密。

    :param s: 待加密字符串
    :param algorithm: 哈希算法，支持 md5 / sha1 / sha256（默认）/ sha512 等
    :return: 十六进制哈希字符串
    :raises ValueError: 当指定的算法不受支持时抛出
    """
    if not isinstance(s, str):
        raise TypeError('输入必须为字符串类型')
    # 使用 hashlib.new 以支持多种算法
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f'不支持的哈希算法: {algorithm}') from e
    hasher.update(s.encode('utf-8'))
    return hasher.hexdigest()

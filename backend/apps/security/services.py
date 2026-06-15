"""
核心安全服务集合

提供以下安全能力：
- 加解密服务（AES-256-ECB / AES-256-CBC）
- 请求签名服务（HMAC-SHA256）
- 数字水印服务（为剧本内容生成并植入不可见水印）
- 限流服务（基于用户ID + IP 的接口限流）
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import struct
import time
from dataclasses import dataclass, field
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from django.conf import settings
from django.core.cache import caches

logger = logging.getLogger(__name__)


# ======================================================================
# 加解密服务
# ======================================================================
class EncryptionService:
    """
    对称加解密服务

    支持 AES-256-ECB 和 AES-256-CBC 两种模式，适用于敏感数据（手机号、邮箱等）的
    本地存储加密。所有输入/输出均为 str，密文使用 Base64 编码。

    使用示例::

        cipher = EncryptionService(key="your-32-byte-secret-key")
        encrypted = cipher.encrypt_cbc("明文内容")
        plaintext = cipher.decrypt_cbc(encrypted)
    """

    # AES-256 需要 32 字节密钥
    KEY_SIZE = 32
    BLOCK_SIZE = 16  # AES 固定块大小

    def __init__(self, key: str | None = None, encoding: str = "utf-8"):
        """
        :param key: 32 字节密钥，若为 None 则使用 settings.SKILL_ENCRYPT_KEY
        :param encoding: 字符串编解码方式
        """
        raw_key = (key or getattr(settings, "SKILL_ENCRYPT_KEY", "")).encode(encoding)
        # 将密钥标准化到 32 字节，使用 SHA-256 摘要以确保长度一致
        self._key = hashlib.sha256(raw_key).digest()
        self._encoding = encoding

    # ---------------- AES-256-ECB ----------------
    def encrypt_ecb(self, plaintext: str) -> str:
        """
        使用 AES-256-ECB 加密。

        ECB 模式无需 IV，便于按字段查询/索引，但安全性略低于 CBC。
        """
        data = plaintext.encode(self._encoding)
        padded = pad(data, self.BLOCK_SIZE)
        cipher = AES.new(self._key, AES.MODE_ECB)
        ciphertext = cipher.encrypt(padded)
        return base64.b64encode(ciphertext).decode(self._encoding)

    def decrypt_ecb(self, ciphertext_b64: str) -> str:
        """
        使用 AES-256-ECB 解密。
        """
        try:
            raw = base64.b64decode(ciphertext_b64)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("无效的 Base64 密文") from exc
        cipher = AES.new(self._key, AES.MODE_ECB)
        try:
            padded = cipher.decrypt(raw)
            plain = unpad(padded, self.BLOCK_SIZE)
        except (ValueError, KeyError) as exc:
            raise ValueError("密文解密失败，可能密钥或填充错误") from exc
        return plain.decode(self._encoding)

    # ---------------- AES-256-CBC ----------------
    def encrypt_cbc(self, plaintext: str, iv: bytes | None = None) -> str:
        """
        使用 AES-256-CBC 加密。

        :param plaintext: 明文
        :param iv: 可选的 16 字节 IV，不传则随机生成
        :return: IV + 密文（前 16 字节为 IV）的 Base64 编码字符串
        """
        data = plaintext.encode(self._encoding)
        padded = pad(data, self.BLOCK_SIZE)
        iv_bytes = iv or os.urandom(self.BLOCK_SIZE)
        cipher = AES.new(self._key, AES.MODE_CBC, iv_bytes)
        ciphertext = iv_bytes + cipher.encrypt(padded)
        return base64.b64encode(ciphertext).decode(self._encoding)

    def decrypt_cbc(self, ciphertext_b64: str) -> str:
        """
        使用 AES-256-CBC 解密。

        :param ciphertext_b64: Base64 编码的 IV+密文
        """
        try:
            raw = base64.b64decode(ciphertext_b64)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("无效的 Base64 密文") from exc
        if len(raw) < self.BLOCK_SIZE * 2:
            raise ValueError("密文长度不足")
        iv_bytes = raw[: self.BLOCK_SIZE]
        ciphertext = raw[self.BLOCK_SIZE:]
        cipher = AES.new(self._key, AES.MODE_CBC, iv_bytes)
        try:
            padded = cipher.decrypt(ciphertext)
            plain = unpad(padded, self.BLOCK_SIZE)
        except (ValueError, KeyError) as exc:
            raise ValueError("密文解密失败，可能密钥或填充错误") from exc
        return plain.decode(self._encoding)


# ======================================================================
# 请求签名服务
# ======================================================================
@dataclass
class SignatureResult:
    """
    签名验证结果封装
    """

    ok: bool
    reason: str = ""
    signature: str = ""
    ts: int | None = None
    nonce: str = ""

    def __bool__(self):
        return self.ok


class SignatureService:
    """
    请求签名服务

    算法：
        signature = hex( HMAC-SHA256(secret, method + path + timestamp + nonce + body_hash) )

    防重放：
        - 时间窗口：timestamp 必须在当前时间 ± SIGNATURE_TIME_WINDOW 秒内
        - Nonce：同 nonce 在时间窗口内不重复（Redis 存储）
    """

    NONCE_CACHE_PREFIX = "sf:sign:nonce:"
    BODY_HASH_CACHE_PREFIX = "sf:sign:body:"

    def __init__(
        self,
        secret: str | None = None,
        time_window: int | None = None,
        cache_alias: str = "default",
    ):
        self._secret = secret or getattr(settings, "API_SIGN_SECRET", "")
        self._time_window = int(
            time_window or getattr(settings, "SIGNATURE_TIME_WINDOW", 300)
        )
        try:
            self._cache = caches[cache_alias]
        except Exception:
            from django.core.cache import cache

            self._cache = cache

    # ---------------- 签名生成 ----------------
    @staticmethod
    def compute_body_hash(body: bytes | str | None) -> str:
        """
        计算请求体的 SHA-256 哈希值。

        - body 为 bytes: 直接参与哈希
        - body 为 str: 按 UTF-8 编码
        - body 为 None / 空字符串: 哈希空字符串
        """
        if body is None:
            body = b""
        elif isinstance(body, str):
            body = body.encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def build_sign_string(
        self,
        method: str,
        path: str,
        timestamp: int,
        nonce: str,
        body_hash: str,
    ) -> bytes:
        """
        构造签名字符串（bytes 形式，便于 HMAC 计算）。
        """
        method = (method or "").upper().strip()
        path = (path or "").strip()
        message = f"{method}{path}{timestamp}{nonce}{body_hash}"
        return message.encode("utf-8")

    def sign(
        self,
        method: str,
        path: str,
        timestamp: int,
        nonce: str,
        body_hash: str,
    ) -> str:
        """
        计算 HMAC-SHA256 签名，返回小写 hex 字符串。
        """
        msg_bytes = self.build_sign_string(method, path, timestamp, nonce, body_hash)
        digest = hmac.new(self._secret.encode("utf-8"), msg_bytes, hashlib.sha256).digest()
        return digest.hex()

    # ---------------- 签名验证 ----------------
    def verify(
        self,
        method: str,
        path: str,
        timestamp: int | str,
        nonce: str,
        body_hash: str,
        signature: str,
    ) -> SignatureResult:
        """
        验证请求签名。

        :return: SignatureResult，通过时 ok=True
        """
        # 1. 参数完整性
        if not signature:
            return SignatureResult(False, "缺少 X-Signature")
        if not timestamp:
            return SignatureResult(False, "缺少 X-Timestamp")
        if not nonce:
            return SignatureResult(False, "缺少 X-Nonce")

        # 2. 时间戳合法性
        try:
            ts_int = int(timestamp)
        except (TypeError, ValueError):
            return SignatureResult(False, "X-Timestamp 格式错误")

        now = int(time.time())
        if abs(now - ts_int) > self._time_window:
            return SignatureResult(
                False,
                f"请求已过期，时间窗口为 {self._time_window} 秒",
                signature,
                ts_int,
                nonce,
            )

        # 3. Nonce 防重放（在 Redis 中标记）
        nonce_key = f"{self.NONCE_CACHE_PREFIX}{nonce}"
        try:
            with self._cache.lock(f"{nonce_key}:lock", timeout=5):
                if self._cache.get(nonce_key):
                    return SignatureResult(
                        False, "Nonce 已被使用", signature, ts_int, nonce
                    )
                # 标记 nonce 已使用，过期时间稍大于时间窗口
                self._cache.set(nonce_key, "1", timeout=self._time_window + 60)
        except Exception:
            # 缓存不可用时降级为纯时间窗口校验
            logger.warning("签名服务：缓存连接失败，降级为纯时间窗口校验")

        # 4. 签名校验（使用 compare_digest 防时序攻击）
        expected = self.sign(method, path, ts_int, nonce, body_hash)
        if not hmac.compare_digest(expected.lower(), signature.lower()):
            return SignatureResult(False, "签名不匹配", signature, ts_int, nonce)

        return SignatureResult(True, "", signature, ts_int, nonce)

    # ---------------- 便捷方法：一次性生成签名头 ----------------
    def generate_headers(
        self,
        method: str,
        path: str,
        body: bytes | str | None = None,
    ) -> dict[str, str]:
        """
        生成签名请求头（用于测试/调试时模拟客户端）。

        返回 dict：{"X-Timestamp": ..., "X-Nonce": ..., "X-Signature": ...,
                      "X-Body-Hash": ...}
        """
        ts = int(time.time())
        nonce = secrets.token_hex(16)
        body_hash = self.compute_body_hash(body)
        sign = self.sign(method, path, ts, nonce, body_hash)
        return {
            "X-Timestamp": str(ts),
            "X-Nonce": nonce,
            "X-Signature": sign,
            "X-Body-Hash": body_hash,
        }


# ======================================================================
# 数字水印服务
# ======================================================================
@dataclass
class WatermarkInfo:
    """
    数字水印内容封装
    """

    user_id: int | None = None
    device_fingerprint: str = ""
    document_id: str = ""
    timestamp: int = field(default_factory=lambda: int(time.time()))
    version: int = 1

    def to_json(self) -> str:
        data = {
            "u": self.user_id,
            "d": self.device_fingerprint,
            "doc": self.document_id,
            "ts": self.timestamp,
            "v": self.version,
        }
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str) -> "WatermarkInfo":
        data = json.loads(payload)
        return cls(
            user_id=data.get("u"),
            device_fingerprint=data.get("d", ""),
            document_id=data.get("doc", ""),
            timestamp=int(data.get("ts", 0)),
            version=int(data.get("v", 1)),
        )


class WatermarkService:
    """
    剧本内容数字水印服务

    水印策略：在剧本文本中的汉字之间植入不可见的零宽字符序列，用于溯源内容传播。
    编码方式：将 payload（JSON 字符串）先 Base64，再将每个 Base64 字符映射成
    4 个零宽字符组合，拼接后插入到文本特定位置（标题后、段落开始处）。

    零宽字符集合：\u200B \u200C \u200D \uFEFF
    """

    # 4 个零宽字符用于 Base64 的 6bit 编码映射
    _ZWC = ["\u200B", "\u200C", "\u200D", "\uFEFF"]  # 0, 1, 2, 3
    _ZWC_SET = frozenset(_ZWC)

    # Base64 字符表
    _BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    # 用于文本清洗
    _ZWC_RE = re.compile(f"[{''.join(_ZWC)}]")

    def __init__(self, encrypt_key: str | None = None):
        self._encryption = EncryptionService(encrypt_key)

    # ---------------- 核心编解码 ----------------
    def _encode_to_zwc(self, data: bytes) -> str:
        """
        将字节数据编码成零宽字符序列。

        策略：每个字节拆分为 4 组 2 bit (0~3)，每组映射为一个零宽字符。
        8 bit → 4 个 ZWC。
        """
        out = []
        for byte in data:
            for shift in (6, 4, 2, 0):
                idx = (byte >> shift) & 0b11
                out.append(self._ZWC[idx])
        return "".join(out)

    def _decode_from_zwc(self, zwc_text: str) -> bytes:
        """
        从零宽字符序列还原原始字节数据。
        """
        char_to_idx = {ch: i for i, ch in enumerate(self._ZWC)}
        # 仅保留零宽字符
        bits_chars = [c for c in zwc_text if c in self._ZWC_SET]
        if len(bits_chars) % 4 != 0:
            raise ValueError("水印序列长度不正确，可能已损坏")
        out = bytearray()
        for i in range(0, len(bits_chars), 4):
            byte = 0
            for j in range(4):
                idx = char_to_idx.get(bits_chars[i + j])
                if idx is None:
                    raise ValueError("水印字符集不匹配")
                byte = (byte << 2) | idx
            out.append(byte)
        return bytes(out)

    def _pack_payload(self, info: WatermarkInfo) -> str:
        """
        封装水印信息 -> JSON -> 加密 -> Base64 -> 零宽字符
        """
        payload = info.to_json()
        encrypted = self._encryption.encrypt_cbc(payload)
        raw = base64.b64decode(encrypted)
        return self._encode_to_zwc(raw)

    def _unpack_payload(self, zwc_text: str) -> WatermarkInfo:
        """
        从零宽字符反解水印信息。
        """
        raw = self._decode_from_zwc(zwc_text)
        b64 = base64.b64encode(raw).decode("ascii")
        plain = self._encryption.decrypt_cbc(b64)
        return WatermarkInfo.from_json(plain)

    # ---------------- 公开 API ----------------
    def embed_watermark(
        self,
        content: str,
        user_id: int | None = None,
        device_fingerprint: str = "",
        document_id: str = "",
    ) -> str:
        """
        为剧本内容植入不可见水印。

        水印插入策略：
        - 文本开头：插入一个水印片段
        - 每隔若干段落（以 \\n\\n 作为段落分隔）再插入一次
        所有水印片段内容相同，便于片段泄露时也可溯源。

        :param content: 原始剧本文本
        :param user_id: 用户ID（可选）
        :param device_fingerprint: 设备指纹（可选）
        :param document_id: 文档ID（可选）
        :return: 带有水印的文本
        """
        if not content:
            return content

        info = WatermarkInfo(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            document_id=document_id,
            timestamp=int(time.time()),
        )
        zwc = self._pack_payload(info)

        # 在文本开头插入水印（放在第一个字符之后，避免污染开头格式）
        segments: list[str] = []
        if content:
            segments.append(content[0])
            segments.append(zwc)
            segments.append(content[1:])
        watermarked = "".join(segments)

        # 每隔 3 段落在段落间插入一次
        paragraphs = watermarked.split("\n\n")
        if len(paragraphs) > 3:
            new_paragraphs = []
            for i, p in enumerate(paragraphs):
                new_paragraphs.append(p)
                if i > 0 and i % 3 == 0 and i < len(paragraphs) - 1:
                    new_paragraphs.append(zwc)
            watermarked = "\n\n".join(new_paragraphs)

        return watermarked

    def extract_watermark(self, content: str) -> WatermarkInfo | None:
        """
        从文本中提取水印信息。

        :param content: 带水印的文本
        :return: WatermarkInfo 对象，若无法提取则返回 None
        """
        if not content:
            return None

        # 收集所有零宽字符
        zwc_chars = [c for c in content if c in self._ZWC_SET]
        if len(zwc_chars) < 4:
            return None

        # 尝试以 4 的倍数截取并解码
        zwc_text = "".join(zwc_chars)
        length = len(zwc_text) - (len(zwc_text) % 4)
        if length == 0:
            return None
        try:
            return self._unpack_payload(zwc_text[:length])
        except Exception:
            return None

    @classmethod
    def clean_watermark(cls, content: str) -> str:
        """
        去除文本中的所有零宽水印字符（用于展示/导出干净版本）。
        """
        if not content:
            return content
        return cls._ZWC_RE.sub("", content)

    def detect_leak(
        self,
        content: str,
        expected_user_id: int | None = None,
        expected_document_id: str = "",
    ) -> tuple[bool, WatermarkInfo | None]:
        """
        检测内容是否为平台流出的剧本，并返回水印信息。

        :return: (是否命中, 水印信息)
        """
        info = self.extract_watermark(content)
        if info is None:
            return False, None
        hit = True
        if expected_user_id is not None and info.user_id != expected_user_id:
            hit = False
        if expected_document_id and info.document_id != expected_document_id:
            hit = False
        return hit, info


# ======================================================================
# 限流服务
# ======================================================================
@dataclass
class RateLimitPolicy:
    """
    限流策略配置
    """

    key_prefix: str = "sf:rl"
    # 默认每分钟 60 次请求（按用户+IP）
    default_limit: int = 60
    default_window: int = 60  # 秒
    # 匿名用户更严格
    anon_limit: int = 30
    anon_window: int = 60
    # 自定义路径规则：path -> (limit, window)
    path_rules: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class RateLimitResult:
    """
    限流结果
    """

    allowed: bool
    remaining: int
    limit: int
    window: int
    reset_after: int  # 剩余窗口（秒）
    key: str

    def __bool__(self):
        return self.allowed


class RateLimitService:
    """
    接口限流服务

    基于 Redis 实现滑动窗口/令牌桶简易算法：
    key = "prefix:{user_id}:{ip}:{path_or_global}:{bucket}"
    每个窗口内计数，超出限制拒绝请求。
    """

    def __init__(
        self,
        policy: RateLimitPolicy | None = None,
        cache_alias: str = "default",
    ):
        self._policy = policy or RateLimitPolicy()
        try:
            self._cache = caches[cache_alias]
        except Exception:
            from django.core.cache import cache

            self._cache = cache

    # ---------------- Key 构造 ----------------
    def _build_key(
        self,
        user_id: int | str | None,
        ip: str,
        path: str = "*",
    ) -> str:
        user_part = f"u{user_id}" if user_id else "anon"
        ip_part = hashlib.md5((ip or "unknown").encode()).hexdigest()[:8]
        path_part = hashlib.md5(path.encode()).hexdigest()[:6]
        return f"{self._policy.key_prefix}:{user_part}:{ip_part}:{path_part}"

    def _get_bucket(self, window: int) -> int:
        """
        按窗口大小返回当前时间桶（固定窗口算法）。
        """
        return int(time.time() // window)

    # ---------------- 核心限流 ----------------
    def check(
        self,
        user_id: int | str | None,
        ip: str,
        path: str = "*",
    ) -> RateLimitResult:
        """
        检查是否允许本次请求。

        - 若路径匹配 path_rules，使用对应策略
        - 否则根据是否登录使用默认/匿名策略
        """
        # 路径匹配（最长前缀匹配）
        matched_limit, matched_window = None, None
        for rule_path, (limit, window) in self._policy.path_rules.items():
            if path.startswith(rule_path):
                matched_limit, matched_window = limit, window
                break

        if matched_limit is not None:
            limit, window = matched_limit, matched_window
        elif user_id:
            limit, window = self._policy.default_limit, self._policy.default_window
        else:
            limit, window = self._policy.anon_limit, self._policy.anon_window

        bucket = self._get_bucket(window)
        key = f"{self._build_key(user_id, ip, path)}:{bucket}"

        # 原子自增
        try:
            current = self._cache.incr(key)
            if current is None or current == 0:
                # 键不存在时 incr 在某些缓存后端会失败，回退为 add
                self._cache.add(key, 1, timeout=window + 10)
                current = 1
        except Exception:
            try:
                self._cache.add(key, 1, timeout=window + 10)
                current = 1
            except Exception:
                # 缓存不可用时直接放行
                logger.warning("限流服务：缓存不可用，请求直接放行")
                return RateLimitResult(True, limit, limit, window, 0, key)

        now = int(time.time())
        reset_after = (bucket + 1) * window - now
        remaining = max(0, limit - current)

        allowed = current <= limit
        return RateLimitResult(allowed, remaining, limit, window, reset_after, key)

    # ---------------- 便捷方法 ----------------
    def get_current_usage(
        self,
        user_id: int | str | None,
        ip: str,
        path: str = "*",
    ) -> tuple[int, int]:
        """
        查询当前窗口内已使用的请求数及限制。
        返回 (current_count, limit)
        """
        if user_id:
            limit, window = self._policy.default_limit, self._policy.default_window
        else:
            limit, window = self._policy.anon_limit, self._policy.anon_window

        bucket = self._get_bucket(window)
        key = f"{self._build_key(user_id, ip, path)}:{bucket}"

        try:
            value = self._cache.get(key)
            current = int(value or 0)
        except Exception:
            current = 0
        return current, limit


# ======================================================================
# 便捷单例导出
# ======================================================================
_default_encryption: EncryptionService | None = None
_default_signature: SignatureService | None = None
_default_watermark: WatermarkService | None = None
_default_rate_limit: RateLimitService | None = None


def get_encryption() -> EncryptionService:
    """获取默认加解密服务实例。"""
    global _default_encryption
    if _default_encryption is None:
        _default_encryption = EncryptionService()
    return _default_encryption


def get_signature() -> SignatureService:
    """获取默认签名服务实例。"""
    global _default_signature
    if _default_signature is None:
        _default_signature = SignatureService()
    return _default_signature


def get_watermark() -> WatermarkService:
    """获取默认水印服务实例。"""
    global _default_watermark
    if _default_watermark is None:
        _default_watermark = WatermarkService()
    return _default_watermark


def get_rate_limit() -> RateLimitService:
    """获取默认限流服务实例。"""
    global _default_rate_limit
    if _default_rate_limit is None:
        from django.conf import settings

        policy = RateLimitPolicy(
            default_limit=int(getattr(settings, "SECURITY_RATE_LIMIT_DEFAULT", 60) or 60),
        )
        _default_rate_limit = RateLimitService(policy=policy)
    return _default_rate_limit

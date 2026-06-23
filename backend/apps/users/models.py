# -*- coding: utf-8 -*-
"""
用户模块数据模型

包含：
1. EncryptedCharField - 自定义加密字段，用于手机号、邮箱等敏感数据
2. User - 自定义用户模型（AUTH_USER_MODEL）
3. UserProfile - 用户扩展资料模型
"""
import base64
import hashlib
import hmac
import uuid

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ============================================================
# 加密工具函数
# ============================================================

def _get_key(key_name: str) -> bytes:
    """获取配置中的加密密钥，统一处理为 32 字节（AES-256）

    :param key_name: settings 中的密钥名称，如 'ENCRYPT_PHONE_KEY'
    :return: 32 字节密钥
    """
    raw_key = getattr(settings, key_name, "") or ""
    if not raw_key:
        raise ValueError(f"settings.{key_name} 未配置")
    # 对任意长度的 key 做 SHA256 得到稳定 32 字节密钥
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def _encrypt(plain: str, key_name: str) -> str:
    """使用 AES-256-CBC 加密字符串

    :param plain: 明文
    :param key_name: settings 中密钥字段名
    :return: base64 编码的密文（iv + ciphertext）
    """
    if plain is None or plain == "":
        return plain
    key = _get_key(key_name)
    iv = hashlib.sha256(uuid.uuid4().bytes).digest()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(plain.encode("utf-8"), AES.block_size))
    return base64.b64encode(iv + ct_bytes).decode("ascii")


def _decrypt(cipher_b64: str, key_name: str) -> str:
    """解密 AES-256-CBC 加密的字符串

    :param cipher_b64: base64 编码的密文
    :param key_name: settings 中密钥字段名
    :return: 明文
    """
    if cipher_b64 is None or cipher_b64 == "":
        return cipher_b64
    try:
        key = _get_key(key_name)
        raw = base64.b64decode(cipher_b64.encode("ascii"))
        iv = raw[:16]
        ct = raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size).decode("utf-8")
    except Exception:
        # 解密失败时返回原值（兼容历史未加密数据）
        return cipher_b64


def _stable_hash(plain: str, key_name: str = "ENCRYPT_PHONE_KEY") -> str:
    """对明文做稳定 HMAC-SHA256 哈希，用于加密字段的查询与唯一约束

    由于 AES-CBC 使用随机 IV，相同明文的密文不固定，
    因此需要额外的哈希字段来实现 unique 约束和快速查询。

    :param plain: 明文
    :param key_name: settings 中的密钥字段名
    :return: 长度为 64 的十六进制字符串
    """
    if plain is None or plain == "":
        return ""
    key = _get_key(key_name)
    return hmac.new(key, plain.encode("utf-8"), hashlib.sha256).hexdigest()


# ============================================================
# 自定义加密字段
# ============================================================

class EncryptedCharField(models.CharField):
    """自定义加密 CharField

    在写入数据库前加密，从数据库读取后解密。
    通过 setting_name 指定使用哪个密钥。
    不支持基于密文的 unique 约束和精确查询（请使用 *_hash 辅助字段）。
    """

    def __init__(self, *args, setting_name: str = "ENCRYPT_PHONE_KEY", **kwargs):
        self.setting_name = setting_name
        kwargs.setdefault("max_length", 255)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """写入数据库前加密"""
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return _encrypt(str(value), self.setting_name)

    def from_db_value(self, value, expression, connection):
        """从数据库读取后解密"""
        if value in (None, ""):
            return value
        return _decrypt(str(value), self.setting_name)

    def to_python(self, value):
        if value in (None, ""):
            return value
        return str(value)


# ============================================================
# 用户管理器
# ============================================================

class UserManager(BaseUserManager):
    """自定义用户管理器

    以手机号为唯一标识创建用户；内部使用 phone_hash 进行查询
    """

    use_in_migrations = True

    def get_by_natural_key(self, phone):
        """Django 认证后端调用的方法

        使用稳定哈希值（phone_hash）进行查询，兼容输入可能是密文或明文的情况。
        """
        if not phone:
            raise self.model.DoesNotExist()
        # 优先计算哈希并查询；若哈希查询不到，尝试密文字段（兜底）
        h = _stable_hash(str(phone), "ENCRYPT_PHONE_KEY")
        try:
            return self.get(phone_hash=h)
        except self.model.DoesNotExist:
            raise

    def _sync_hashes(self, user):
        """在保存前同步 *_hash 辅助字段"""
        if getattr(user, "phone", None):
            user.phone_hash = _stable_hash(str(user.phone), "ENCRYPT_PHONE_KEY")
        if getattr(user, "email", None):
            user.email_hash = _stable_hash(str(user.email), "ENCRYPT_EMAIL_KEY")
        else:
            user.email_hash = ""

    def _create_user(self, phone: str, password: str = None, **extra_fields):
        """内部创建用户方法"""
        if not phone:
            raise ValueError("必须提供手机号")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        self._sync_hashes(user)
        user.save(using=self._db)
        # 同时创建对应的 UserProfile
        UserProfile.objects.using(self._db).get_or_create(
            user=user,
            defaults={
                "nickname": extra_fields.get("nickname", f"用户{user.id.hex[:8]}"),
                "avatar_url": extra_fields.get("avatar_url", ""),
            },
        )
        return user

    def create_user(self, phone: str, password: str = None, **extra_fields):
        """创建普通用户"""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone: str, password: str = None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级用户必须设置 is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级用户必须设置 is_superuser=True")
        return self._create_user(phone, password, **extra_fields)


# ============================================================
# User 模型
# ============================================================

class User(AbstractBaseUser, PermissionsMixin):
    """自定义用户模型

    - phone / email 使用 AES-256-CBC 加密存储
    - phone_hash / email_hash 为稳定哈希，用于唯一约束和快速查询
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="用户ID",
    )
    # 加密存储字段
    phone = EncryptedCharField(
        setting_name="ENCRYPT_PHONE_KEY",
        max_length=255,
        unique=True,
        verbose_name="手机号（加密）",
        help_text="使用 AES-256-CBC 加密存储；唯一性由 phone_hash 在业务层保证",
    )
    email = EncryptedCharField(
        setting_name="ENCRYPT_EMAIL_KEY",
        max_length=255,
        blank=True,
        default="",
        verbose_name="邮箱（加密）",
    )
    # 稳定哈希字段，用于唯一约束与查询
    phone_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="手机号哈希",
        help_text="HMAC-SHA256，用于唯一索引与查询",
    )
    email_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="邮箱哈希",
    )

    nickname = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="昵称",
    )
    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="头像URL",
    )

    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    is_staff = models.BooleanField(default=False, verbose_name="是否员工")
    is_superuser = models.BooleanField(default=False, verbose_name="是否超管")

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="注册时间",
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["phone_hash"]),
            models.Index(fields=["email_hash"]),
        ]

    def __str__(self) -> str:
        return f"{self.nickname or '未命名用户'} ({self.id.hex[:8]})"

    def get_full_name(self) -> str:
        return self.nickname or self.phone

    def get_short_name(self) -> str:
        return self.nickname or self.phone

    def save(self, *args, **kwargs):
        """保存前同步 phone_hash / email_hash"""
        if self.phone:
            self.phone_hash = _stable_hash(str(self.phone), "ENCRYPT_PHONE_KEY")
        if self.email:
            self.email_hash = _stable_hash(str(self.email), "ENCRYPT_EMAIL_KEY")
        else:
            self.email_hash = ""
        super().save(*args, **kwargs)


# ============================================================
# UserProfile 模型
# ============================================================

class UserProfile(models.Model):
    """用户扩展资料模型

    与 User 一对一关系，保存用户的个性化信息
    """

    class Gender(models.TextChoices):
        MALE = "M", "男"
        FEMALE = "F", "女"
        OTHER = "O", "其他"
        UNKNOWN = "U", "未知"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="资料ID",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="所属用户",
    )
    nickname = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="昵称",
    )
    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="头像URL",
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
        verbose_name="性别",
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="个人简介",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = verbose_name
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user} 的资料"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 保存资料时同步更新 User 的昵称和头像，保证两者一致
        changed = []
        if self.nickname and self.user.nickname != self.nickname:
            self.user.nickname = self.nickname
            changed.append("nickname")
        if self.avatar_url and self.user.avatar_url != self.avatar_url:
            self.user.avatar_url = self.avatar_url
            changed.append("avatar_url")
        if changed:
            self.user.save(update_fields=changed)

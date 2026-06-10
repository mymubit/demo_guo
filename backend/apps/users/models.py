"""
用户模型
"""
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, nickname=None, **extra_fields):
        if not phone:
            raise ValueError('手机号不能为空')
        user = self.model(
            phone=phone,
            nickname=nickname or f'用户{phone[-4:]}',
            **extra_fields
        )
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, nickname=None):
        user = self.create_user(
            phone=phone,
            password=password,
            nickname=nickname or '超级管理员',
            is_staff=True,
            is_superuser=True,
        )
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """自定义用户模型

    以手机号作为唯一登录标识
    """
    id = models.UUIDField(primary_key=True, default=__import__('uuid').uuid4, editable=False)
    phone = models.CharField('手机号', max_length=32, unique=True, db_index=True)
    nickname = models.CharField('昵称', max_length=64, blank=True, default='新用户')
    email = models.CharField('邮箱', max_length=128, blank=True, default='')
    avatar = models.CharField('头像URL', max_length=512, blank=True, default='')
    is_active = models.BooleanField('是否活跃', default=True)
    is_staff = models.BooleanField('是否为员工', default=False)
    is_superuser = models.BooleanField('是否为超级管理员', default=False)
    date_joined = models.DateTimeField('注册时间', default=timezone.now)
    last_login = models.DateTimeField('最后登录', null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'sf_users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f'{self.nickname}({self.phone})'

    def save(self, *args, **kwargs):
        # 更新登录时间
        if self.pk is None:
            self.date_joined = timezone.now()
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """用户补充信息"""
    id = models.UUIDField(primary_key=True, default=__import__('uuid').uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField('性别', max_length=10, blank=True, default='')
    bio = models.TextField('个人简介', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'sf_user_profiles'
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f'{self.user.nickname}的资料'

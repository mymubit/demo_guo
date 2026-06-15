# -*- coding: utf-8 -*-
"""创建后台管理员账号（is_staff=True）"""
from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = "创建或更新后台管理员（手机号登录，is_staff=True）"

    def add_arguments(self, parser):
        parser.add_argument("--phone", required=True, help="11 位手机号")
        parser.add_argument("--password", required=True, help="登录密码（至少 8 位）")
        parser.add_argument("--nickname", default="管理员", help="昵称")

    def handle(self, *args, **options):
        phone = options["phone"].strip()
        password = options["password"]
        nickname = options["nickname"]

        if len(password) < 8:
            self.stderr.write(self.style.ERROR("密码至少 8 位"))
            return

        try:
            user = User.objects.get_by_natural_key(phone)
        except User.DoesNotExist:
            user = None

        if user:
            user.is_staff = True
            user.is_superuser = True
            user.nickname = nickname or user.nickname
            user.is_active = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Admin user updated: phone={phone}"))
        else:
            User.objects.create_superuser(
                phone=phone,
                password=password,
                nickname=nickname,
            )
            self.stdout.write(self.style.SUCCESS(f"Admin user created: phone={phone}"))

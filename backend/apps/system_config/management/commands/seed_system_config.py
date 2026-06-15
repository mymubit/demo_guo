# -*- coding: utf-8 -*-
"""初始化动态配置中心默认配置。"""
from django.core.management.base import BaseCommand

from apps.system_config.services import SystemConfigService


class Command(BaseCommand):
    help = "初始化动态配置中心默认配置"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="覆盖已有配置值，仅建议开发/测试环境使用",
        )

    def handle(self, *args, **options):
        result = SystemConfigService.seed_defaults(
            overwrite=bool(options.get("overwrite")),
            stdout=self.stdout,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "动态配置初始化完成：分类新增 {created_categories}，配置新增 {created_items}，配置更新 {updated_items}".format(
                    **result
                )
            )
        )

# -*- coding: utf-8 -*-
"""
初始化技能数据命令

运行方式：
    python manage.py init_skill_data

功能：
    1. 初始化默认技能配置
    2. 初始化8大题材模板
    3. 初始化20条钩子库
    4. 初始化默认对话模板
"""
from django.core.management.base import BaseCommand

from apps.skill.config.portal.skill_settings import init_skill_data


class Command(BaseCommand):
    help = '初始化技能数据（配置、题材模板、钩子库等）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始初始化技能数据...'))

        try:
            init_skill_data()
            self.stdout.write(self.style.SUCCESS('技能数据初始化完成！'))
            self.stdout.write(self.style.SUCCESS('  - 技能配置：已初始化'))
            self.stdout.write(self.style.SUCCESS('  - 大模型：已迁移/初始化'))
            self.stdout.write(self.style.SUCCESS('  - 题材模板：8大题材已就绪'))
            self.stdout.write(self.style.SUCCESS('  - 钩子库：20+条钩子已入库'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'初始化失败: {e}'))
            raise

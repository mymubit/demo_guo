# -*- coding: utf-8 -*-
"""清除 Redis 中的接口限流计数（sf:rl:*）。"""
from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "清除限流中间件在 Redis 中的计数键（sf:rl:*）"

    def handle(self, *args, **options):
        cleared = 0
        try:
            client = cache.client.get_client(write=True)
            keys = list(client.scan_iter(match="sf:rl:*", count=500))
            if keys:
                cleared = client.delete(*keys)
        except AttributeError:
            self.stderr.write("当前缓存后端不支持 scan_iter，请手动清理 Redis 中 sf:rl:* 键。")
            return
        except Exception as exc:
            self.stderr.write(f"清理失败: {exc}")
            return

        self.stdout.write(self.style.SUCCESS(f"已清除 {cleared or 0} 个限流计数键"))

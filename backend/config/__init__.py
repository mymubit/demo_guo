"""Django 配置包，加载 Celery。"""
from config.celery import app as celery_app

__all__ = ("celery_app",)

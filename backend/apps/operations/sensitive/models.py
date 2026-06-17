"""敏感词模块（精简版）。

只一个表：SensitiveWord
不做：分级、规则表达式、版本快照、违规日志（个人站用不上）
"""
from __future__ import annotations

from django.db import models


class SensitiveWord(models.Model):
    """敏感词。"""

    word = models.CharField(max_length=128, unique=True)
    note = models.CharField(max_length=255, blank=True, default="", help_text="给自己看的备注")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_sensitive_word"
        ordering = ["-updated_at"]

    def __str__(self) -> str:  # pragma: no cover
        return self.word
